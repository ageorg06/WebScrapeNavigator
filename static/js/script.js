document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('url');
    const submitBtn = document.getElementById('submitBtn');
    const status = document.getElementById('status');
    const scrapedContent = document.getElementById('scrapedContent');

    urlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
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

        try {
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                status.textContent = `Scraping completed! Pages attempted: ${data.total_pages_attempted}, Pages scraped: ${data.total_pages_scraped}`;
                status.style.backgroundColor = '#4CAF50';
                displayScrapedContent(data.content, data.errors);
                
                // Add download button
                const downloadBtn = document.createElement('button');
                downloadBtn.textContent = 'Download Full Content';
                downloadBtn.onclick = () => {
                    window.location.href = `/download/${data.job_id}`;
                };
                scrapedContent.appendChild(downloadBtn);
                
                submitBtn.disabled = false;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            status.textContent = `Error: ${error.message}`;
            status.style.backgroundColor = '#FF0000';
            submitBtn.disabled = false;
        }
    });

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
            contentDiv.innerHTML = '<h3>Scraped Content (First page):</h3>';
            content.forEach((page, index) => {
                const pageContent = document.createElement('div');
                pageContent.innerHTML = `
                    <h4>Page ${index + 1}: ${page.url}</h4>
                    <p>${page.content.substring(0, 300)}...</p>
                `;
                contentDiv.appendChild(pageContent);
            });
            scrapedContent.appendChild(contentDiv);
        } else {
            scrapedContent.innerHTML += '<p>No content was scraped.</p>';
        }
    }
});
