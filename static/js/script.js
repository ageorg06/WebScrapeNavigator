document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM content loaded");

    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('url');
    const submitBtn = document.getElementById('submitBtn');
    const status = document.getElementById('status');
    const scrapedContent = document.getElementById('scrapedContent');
    const requiresAuthCheckbox = document.getElementById('requiresAuth');
    const authFields = document.getElementById('authFields');
    const urlTree = document.getElementById('urlTree');

    console.log("Elements retrieved:", { urlForm, urlInput, submitBtn, status, scrapedContent, requiresAuthCheckbox, authFields, urlTree });

    requiresAuthCheckbox.addEventListener('change', () => {
        authFields.style.display = requiresAuthCheckbox.checked ? 'block' : 'none';
    });

    urlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log("Form submitted");

        const url = urlInput.value.trim();
        
        if (!url) {
            alert('Please enter a valid URL');
            return;
        }

        submitBtn.disabled = true;
        status.style.display = 'block';
        status.textContent = 'Scraping in progress...';
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

        console.log("Request body:", requestBody);

        try {
            console.log("Sending fetch request");
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            console.log("Fetch response received");
            const data = await response.json();
            console.log("Response data:", data);

            if (data.status === 'completed') {
                status.textContent = 'Scraping completed';
                status.style.backgroundColor = '#4CAF50';
                console.log("Updating URL tree");
                updateUrlTree(data.url_tree);
                console.log("Displaying scraped content");
                displayScrapedContent(data.content, data.errors, data.job_id);
                
                console.log("Triggering download");
                downloadContent(data.formatted_content, `scraped_content_${data.job_id}.json`);
            } else {
                throw new Error(data.message || 'Failed to scrape website');
            }
        } catch (error) {
            console.error("Error occurred:", error);
            status.textContent = `Error: ${error.message}`;
            status.style.backgroundColor = '#FF0000';
        } finally {
            submitBtn.disabled = false;
        }
    });

    function updateUrlTree(tree) {
        console.log("Updating URL tree with:", tree);
        urlTree.innerHTML = '';
        if (tree && tree.children) {
            const treeHtml = createTreeHtml(tree);
            urlTree.appendChild(treeHtml);
        }
    }

    function createTreeHtml(node) {
        console.log("Creating tree HTML for node:", node);
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
            const nestedUl = this.parentElement.querySelector('.nested');
            if (nestedUl) {
                nestedUl.classList.toggle('active');
                this.classList.toggle('caret-down');
            }
        });

        return li;
    }

    function displayScrapedContent(content, errors, jobId) {
        console.log("Displaying scraped content:", { content, errors, jobId });
        scrapedContent.innerHTML = '<h2>Scraping Results:</h2>';
        
        if (errors && errors.length > 0) {
            const errorsList = document.createElement('ul');
            errorsList.innerHTML = '<h3>Errors:</h3>';
            errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                errorsList.appendChild(li);
            });
            scrapedContent.appendChild(errorsList);
        }

        if (content && content.length > 0) {
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

            // Add download button
            const downloadBtn = document.createElement('button');
            downloadBtn.textContent = 'Download Results';
            downloadBtn.onclick = () => {
                window.location.href = `/download/${jobId}`;
            };
            scrapedContent.appendChild(downloadBtn);
        } else {
            scrapedContent.innerHTML += '<p>No content was scraped.</p>';
        }
    }

    function downloadContent(content, filename) {
        console.log("Downloading content:", { filename });
        const blob = new Blob([content], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});
