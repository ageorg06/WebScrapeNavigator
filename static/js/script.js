document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('url');
    const submitBtn = document.getElementById('submitBtn');
    const status = document.getElementById('status');
    const scrapedContent = document.getElementById('scrapedContent');
    const requiresAuthCheckbox = document.getElementById('requiresAuth');
    const authFields = document.getElementById('authFields');

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

        const requestBody = {
            url,
            max_workers: 5
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
                pollTaskStatus(data.task_id);
            } else {
                throw new Error('Failed to start scraping task');
            }
        } catch (error) {
            status.textContent = `Error: ${error.message}`;
            status.style.backgroundColor = '#FF0000';
            submitBtn.disabled = false;
        }
    });

    function pollTaskStatus(taskId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/task_status/${taskId}`);
                const data = await response.json();

                if (data.state === 'PENDING' || data.state === 'PROGRESS') {
                    status.textContent = `Scraping in progress... ${data.status}`;
                } else if (data.state === 'SUCCESS') {
                    clearInterval(pollInterval);
                    status.textContent = 'Scraping completed!';
                    status.style.backgroundColor = '#4CAF50';
                    displayScrapedContent(data.result.content, data.result.errors);
                    submitBtn.disabled = false;
                } else {
                    clearInterval(pollInterval);
                    throw new Error(data.status);
                }
            } catch (error) {
                clearInterval(pollInterval);
                status.textContent = `Error: ${error.message}`;
                status.style.backgroundColor = '#FF0000';
                submitBtn.disabled = false;
            }
        }, 2000); // Poll every 2 seconds
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
