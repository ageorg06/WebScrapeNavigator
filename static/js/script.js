document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('url');
    const submitBtn = document.getElementById('submitBtn');
    const status = document.getElementById('status');
    const scrapedContent = document.getElementById('scrapedContent');
    const requiresAuthCheckbox = document.getElementById('requiresAuth');
    const authFields = document.getElementById('authFields');
    const urlTree = document.getElementById('urlTree');

    requiresAuthCheckbox.addEventListener('change', () => {
        authFields.style.display = requiresAuthCheckbox.checked ? 'block' : 'none';
    });

    urlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        
        if (!url) {
            alert('Please enter a valid URL');
            return;
        }

        submitBtn.disabled = true;
        status.style.display = 'block';
        status.textContent = 'Starting scraping task...';
        status.style.backgroundColor = '#FFA500';
        scrapedContent.innerHTML = '';
        urlTree.innerHTML = '';

        const requestBody = {
            url,
            max_workers: 5,
            preprocessing_options: {
                clean_html: document.getElementById('cleanHtml').checked,
                remove_special_chars: document.getElementById('removeSpecialChars').checked,
                remove_extra_whitespace: document.getElementById('removeExtraWhitespace').checked,
                remove_stopwords: document.getElementById('removeStopwords').checked
            }
        };

        if (requiresAuthCheckbox.checked) {
            requestBody.auth = {
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };
        }

        try {
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();

            if (data.status === 'task_started') {
                startEventSource(data.task_id);
            } else {
                throw new Error('Failed to start scraping task');
            }
        } catch (error) {
            status.textContent = `Error: ${error.message}`;
            status.style.backgroundColor = '#FF0000';
            submitBtn.disabled = false;
        }
    });

    function startEventSource(taskId) {
        const eventSource = new EventSource(`/scrape_updates/${taskId}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateStatus(data);
            updateUrlTree(data.url_tree);

            if (data.status === 'completed') {
                eventSource.close();
                displayScrapedContent(data.result.content, data.result.errors);
                submitBtn.disabled = false;
            }
        };

        eventSource.onerror = (error) => {
            console.error('EventSource failed:', error);
            eventSource.close();
            status.textContent = 'Error: Lost connection to the server';
            status.style.backgroundColor = '#FF0000';
            submitBtn.disabled = false;
        };
    }

    function updateStatus(data) {
        status.textContent = `Scraping in progress... Pages scraped: ${data.pages_scraped}`;
        status.style.backgroundColor = '#FFA500';
    }

    function updateUrlTree(tree) {
        urlTree.innerHTML = '';
        const treeHtml = createTreeHtml(tree);
        urlTree.appendChild(treeHtml);
    }

    function createTreeHtml(node) {
        const li = document.createElement('li');
        const span = document.createElement('span');
        span.textContent = node.url;
        span.classList.add('caret');
        li.appendChild(span);

        if (node.children && node.children.length > 0) {
            const ul = document.createElement('ul');
            ul.classList.add('nested');
            node.children.forEach(child => {
                ul.appendChild(createTreeHtml(child));
            });
            li.appendChild(ul);
        }

        span.addEventListener('click', function() {
            this.parentElement.querySelector('.nested').classList.toggle('active');
            this.classList.toggle('caret-down');
        });

        return li;
    }

    function displayScrapedContent(content, errors) {
        scrapedContent.innerHTML = '<h2>Scraping Results:</h2>';
        
        if (errors.length > 0) {
            const errorsList = document.createElement('ul');
            errorsList.innerHTML = '<h3>Errors:</h3>';
            errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                errorsList.appendChild(li);
            });
            scrapedContent.appendChild(errorsList);
        }

        if (content.length > 0) {
            const contentDiv = document.createElement('div');
            contentDiv.innerHTML = '<h3>Scraped Content:</h3>';
            
            function displayPages(start, end) {
                for (let i = start; i < end && i < content.length; i++) {
                    const page = content[i];
                    const pageContent = document.createElement('div');
                    pageContent.innerHTML = `
                        <h4>Page ${i + 1}: ${page.url}</h4>
                        <p>${page.content.substring(0, 300)}...</p>
                    `;
                    contentDiv.appendChild(pageContent);
                }
            }

            displayPages(0, 5);
            scrapedContent.appendChild(contentDiv);

            if (content.length > 5) {
                const showMoreBtn = document.createElement('button');
                showMoreBtn.textContent = 'Show More';
                showMoreBtn.onclick = () => {
                    const currentPageCount = contentDiv.children.length;
                    displayPages(currentPageCount, currentPageCount + 5);
                    if (currentPageCount + 5 >= content.length) {
                        showMoreBtn.style.display = 'none';
                    }
                };
                scrapedContent.appendChild(showMoreBtn);
            }
        } else {
            scrapedContent.innerHTML += '<p>No content was scraped.</p>';
        }
    }
});
