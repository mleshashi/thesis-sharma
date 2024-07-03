document.addEventListener('DOMContentLoaded', function () {
    const topicDropdown = document.getElementById('topicDropdown');
    const inputField = document.getElementById('inputField');
    let topic = '';

    function fetchTopics(url) {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                topicDropdown.innerHTML = '';
                data.topics.forEach(topic => {
                    let option = new Option(topic, topic);
                    topicDropdown.add(option);
                });
                topicDropdown.style.display = 'block';
                inputField.style.display = 'none';
            });
    }

    document.getElementById('getTopics').onclick = function () {
        fetchTopics('/get-topics');
        clearResults();
        clearLLMAnswers();
        clearExistingModal();
    };

    document.getElementById('getManualTopics').onclick = function () {
        fetchTopics('/get-manual-topics');
        clearResults();
        clearLLMAnswers();
        clearExistingModal();
    };

    document.getElementById('searchRandomContext').onclick = function () {
        topicDropdown.style.display = 'none';
        inputField.style.display = 'block';
        inputField.value = '';
        inputField.focus();

        // Remove any existing modal
        clearExistingModal();

        fetch('/get-random-image')
            .then(response => response.json())
            .then(doc => {
                if (doc.image_data) {
                    const img = document.createElement('img');
                    img.src = `data:image/jpeg;base64,${doc.image_data}`;
                    img.classList.add('enlarged-image');
                    const modal = document.createElement('div');
                    modal.classList.add('modal');
                    modal.appendChild(img);
                    document.body.appendChild(modal);
                    modal.style.top = `150px`;
                    modal.onclick = function() {
                        document.body.removeChild(modal);
                    };
                } else {
                    alert("No image found");
                }
            });
        clearResults();
        clearLLMAnswers();
    };

    function clearResults() {
        document.getElementById('model1-results').innerHTML = '';
        document.getElementById('model2-results').innerHTML = '';
        document.getElementById('model3-results').innerHTML = '';
        document.getElementById('model4-results').innerHTML = '';
    }

    function clearLLMAnswers() {
        document.querySelectorAll('.llm-answer-content').forEach(el => el.innerHTML = '');
        document.querySelectorAll('.llm-answer').forEach(el => el.style.display = 'none');
    }

    function clearExistingModal() {
        const existingModal = document.querySelector('.modal');
        if (existingModal) {
            document.body.removeChild(existingModal);
        }
    }

    document.getElementById('search').onclick = function () {
        const isDropdownVisible = topicDropdown.style.display !== 'none';
        topic = isDropdownVisible ? topicDropdown.value : inputField.value;

        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic })
        })
            .then(response => response.json())
            .then(data => {
                displayResults(data.model_1_documents, 'model1-results');
                displayResults(data.model_2_documents, 'model2-results');
                displayResults(data.model_3_documents, 'model3-results');
                displayResults(data.model_4_documents, 'model4-results');
                document.querySelectorAll('.llm-answer').forEach(el => el.style.display = 'block');
            });

        clearExistingModal();
    };

    document.getElementById('generateAnswers').onclick = function () {
        setTimeout(() => {
            document.querySelector('#model1-answer .llm-answer-content').textContent = 'Final Answer for BM25';
            document.querySelector('#model2-answer .llm-answer-content').textContent = 'Final Answer for Mistral';
            document.querySelector('#model3-answer .llm-answer-content').textContent = 'Final Answer for GTE-QWEN2';
            document.querySelector('#model4-answer .llm-answer-content').textContent = 'Final Answer for CLIP';
        }, 1000);
    };
    

    function displayResults(documents, elementId) {
        const container = document.getElementById(elementId);
        container.innerHTML = '';
        documents.forEach((doc, index) => {
            setTimeout(() => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <div class="document-info">
                        <strong>Title:</strong> <span class="doc-title">${doc.title}</span><br>
                        <strong>Content:</strong> <span class="doc-content">${doc.content}</span><br>
                    </div>
                    <div class="relevant-score-container">
                        <div class="relevant-score-left">
                            <div class="relevant-score-row">
                                <strong>Score:</strong> <span class="score">${doc.score}</span>
                            </div>
                            <div class="relevant-score-row">
                                <strong>Relevance:</strong>
                                <select class="relevance-score-input">
                                    <option value="-1">-1(Unable to Judge)</option>
                                    <option value="0">0(No)</option>
                                    <option value="1">1(Partially Relevant)</option>
                                    <option value="2">2(Relevant)</option>
                                    <option value="3">3(Highly Relevant)</option>
                                </select>
                            </div>
                            <div class="relevant-score-row">
                                <strong>Completeness:</strong>
                                <select class="completeness-score-input">
                                    <option value="-1">-1(Unable to Judge)</option>
                                    <option value="0">0(No)</option>
                                    <option value="1">1(Somewhat)</option>
                                    <option value="2">2(Yes but not completely)</option>
                                    <option value="3">3(Yes)</option>
                                </select>
                            </div>
                        </div>
                        <div class="relevant-score-right">
                            <img src="data:image/jpeg;base64,${doc.image_data}" class="compact-image" onclick="enlargeImage(this)">
                        </div>
                        <!-- Include title and content in hidden-info for evaluation purposes -->
                        <div class="hidden-info">
                            <span class="hidden-title">${doc.title}</span>
                            <span class="hidden-content">${doc.content}</span>
                        </div>
                    </div>`;
                container.appendChild(div);
            }, index * 400);
        });
    }
    

    window.enlargeImage = function(img) {
        const modal = document.createElement('div');
        modal.classList.add('modal');

        // Create the close button
        const closeButton = document.createElement('span');
        closeButton.classList.add('close-button');
        closeButton.innerHTML = '&times;'; // HTML entity for the 'X' symbol

        // Add event listener to the close button to remove the modal
        closeButton.addEventListener('click', function() {
            document.body.removeChild(modal);
        });
    
        const enlargedImg = document.createElement('img');
        enlargedImg.src = img.src;
        enlargedImg.classList.add('enlarged-image');
    
        modal.appendChild(closeButton); // Append the close button to the modal
        modal.appendChild(enlargedImg);
        document.body.appendChild(modal);
    
        // Wait for the image to load to get its natural dimensions
        enlargedImg.onload = function() {
            const naturalWidth = enlargedImg.naturalWidth;
            const naturalHeight = enlargedImg.naturalHeight;
    
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
    
            // Set the size of the modal based on the natural size of the image
            const modalWidth = Math.min(naturalWidth, windowWidth - 40);
            const modalHeight = Math.min(naturalHeight, windowHeight - 40);
    
            modal.style.width = `${modalWidth}px`;
            modal.style.height = `${modalHeight}px`;
    
            const imgRect = img.getBoundingClientRect();
            const windowCenter = windowWidth / 2;
            const isLeftOfCenter = imgRect.left < windowCenter;
    
            // Center the modal vertically within the window
            modal.style.top = `${Math.max(20, (windowHeight - modalHeight) / 2)}px`;
    
            if (isLeftOfCenter) {
                // Position the modal on the right side of the window
                modal.style.left = `${Math.min(windowWidth - modalWidth - 20, windowCenter + 20)}px`;
            } else {
                // Position the modal on the left side of the window
                modal.style.left = `${Math.max(windowCenter - modalWidth - 80)}px`;
            }
        };
    
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                document.body.removeChild(modal);
            }
        });

        // Add event listener to the compact image to remove the modal on second click
        img.addEventListener('click', function() {
            document.body.removeChild(modal);
        });
    
        const parentDiv = img.closest('.relevant-score-container');
        const relevanceDropdown = parentDiv.querySelector('.relevance-score-input');
        if (relevanceDropdown) {
            relevanceDropdown.focus();
        }
        parentDiv.querySelectorAll('select').forEach((select, index, selects) => {
            select.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    const nextSelect = selects[index + 1];
                    if (nextSelect) {
                        nextSelect.focus();
                    } else {
                        selects[0].focus();
                    }
                }
            });
        });
    };
        

    document.getElementById('evaluateButton').onclick = function() {
        const documents = document.getElementsByClassName('relevant-score-container');
        const results = {
            query: topic,
            model_1_documents: [],
            model_2_documents: [],
            model_3_documents: [],
            model_4_documents: []
        };

        Array.from(documents).forEach((doc) => {
            const score = doc.querySelector('.score').innerText;
            const relevance = doc.querySelector('.relevance-score-input').value;
            const completeness = doc.querySelector('.completeness-score-input').value;
            const image_data = doc.querySelector('.compact-image').src.split(',')[1]; // Fetch base64 part of image data

            // Fetching title and content from the hidden-info div
            const title = doc.querySelector('.hidden-title').innerText;
            const content = doc.querySelector('.hidden-content').innerText;


            const result = {
                score: parseFloat(score),
                relevance: parseFloat(relevance),
                completeness: parseFloat(completeness),
                title: title.trim(),
                content: content.trim(),
                image_data: image_data.trim()
            };

            if (doc.closest('#model1-results')) {
                results.model_1_documents.push(result);
            } else if (doc.closest('#model2-results')) {
                results.model_2_documents.push(result);
            } else if (doc.closest('#model3-results')) {
                results.model_3_documents.push(result);
            } else if (doc.closest('#model4-results')) {
                results.model_4_documents.push(result);
            }
        });

        fetch('/store-scores', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(results)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Scores stored successfully:', data);
            // Fetch the NDCG scores after storing the results
            fetch('/evaluate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(results)
            })
            .then(response => response.json())
            .then(ndcg_scores => {
                displayNDCGScores(ndcg_scores);
            })
            .catch(error => console.error('Error:', error));
        })
        .catch(error => console.error('Error:', error));
    };

    function displayNDCGScores(ndcg_scores) {

        // Clear existing NDCG scores
        document.querySelectorAll('.ndcg-score').forEach(el => el.remove());
        
        document.getElementById('model1-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG Score: <span class="ndcg-value">${ndcg_scores.model_1_documents.toFixed(2)}</span></div>`);
        document.getElementById('model2-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG Score: <span class="ndcg-value">${ndcg_scores.model_2_documents.toFixed(2)}</span></div>`);
        document.getElementById('model3-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG Score: <span class="ndcg-value">${ndcg_scores.model_3_documents.toFixed(2)}</span></div>`);
        document.getElementById('model4-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG Score: <span class="ndcg-value">${ndcg_scores.model_4_documents.toFixed(2)}</span></div>`);
    }
});


