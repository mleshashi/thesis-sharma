document.addEventListener('DOMContentLoaded', function () {
    const topicDropdown = document.getElementById('topicDropdown');
    const inputField = document.getElementById('inputField');
    const answerInfoContainer = document.querySelector('.llm-answer-info-container');
    const finalAnswer1 = document.querySelector('.llm-answer1');
    const finalAnswer2 = document.querySelector('.llm-answer2');
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
        clearAdditionalInfo();
    };

    document.getElementById('getManualTopics').onclick = function () {
        fetchTopics('/get-manual-topics');
        clearResults();
        clearLLMAnswers();
        clearExistingModal();
        clearAdditionalInfo();
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

                    // Create the title element
                    const title = document.createElement('div');
                    title.classList.add('image-title');
                    title.innerText = doc.title || 'No Title'; // Provide default text if title is missing

                    const modal = document.createElement('div');
                    modal.classList.add('modal');

                    modal.appendChild(title); // Append the title to the modal first
                    modal.appendChild(img); // Append the image to the modal
                    document.body.appendChild(modal);

                    // Center the modal with a top offset
                    modal.style.top = `180px`;

                    // Close modal on background click
                    modal.onclick = function (event) {
                        if (event.target === modal) {
                            clearExistingModal();
                        }
                    };
                } else {
                    alert("No image found");
                }
            });
        clearResults();
        clearLLMAnswers();
        clearAdditionalInfo();
    };

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

            // Show the answer info container with titles
            answerInfoContainer.style.display = 'flex';
            finalAnswer1.style.display = 'block';
            finalAnswer2.style.display = 'block';

            // Open a new HTML page in a new tab
            const annotationURL = '/annotation'; // The URL of the new page
            window.open(annotationURL, '_blank');
        })
        .catch(error => {
            console.error('Error:', error);
        });

        // Show the modal overlay
        loadingModal.classList.remove('hidden');

        // Automatically hide the modal after 1 minute
        setTimeout(() => {
            loadingModal.classList.add('hidden');
        }, 60000);
    
        clearExistingModal();
        clearLLMAnswerContent();
    };    

    document.getElementById('generateAnswers').onclick = function () {
        // Get the number of top documents to use
        const topN = prompt("Enter the number of top documents to use:", "1");

        // Fetch the prepared LLM input and generate the answer
        fetch(`/prepare-llm-input?top_n=${topN}`)
            .then(response => response.json())
            .then(data => {
                if (data.message !== "LLM input prepared and stored successfully") {
                    throw new Error("Failed to prepare LLM input.");
                }
                // Generate the LLM answer
                return fetch('/generate-llm-answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
            })
            .then(response => response.json())
            .then(() => {
                // Retrieve scores including the generated LLM answer
                return fetch('/retrieve-scores');
            })
            .then(response => response.json())
            .then(scores => {
                console.log("Retrieve Scores Response:", scores);
                const finalAnswerContent = document.querySelector('.llm-answer-content1');
                const llmAnswer = scores.llm_answer;
                if (llmAnswer && llmAnswer.choices && llmAnswer.choices.length > 0 && llmAnswer.choices[0].message) {
                    // Convert Markdown to HTML
                    const markdownContent = llmAnswer.choices[0].message.content;
                    const htmlContent = marked.parse(markdownContent); // Use marked.parse to convert Markdown to HTML
                    finalAnswerContent.innerHTML = htmlContent; // Display the HTML content
                } else {
                    finalAnswerContent.innerHTML = "No valid response received.";
                }
                finalAnswerContent.classList.remove('hidden'); // Show the final answer content
            })
            .catch(error => {
                console.error('Error:', error);
                const finalAnswerContent = document.querySelector('.llm-answer-content1');
                finalAnswerContent.innerHTML = `An error occurred while generating the answer: ${error.message}`;
                finalAnswerContent.classList.remove('hidden'); // Show the error message
            });
    };


    // Event listener for the save button
    document.getElementById('save').onclick = function () {
        fetch('/save-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            console.log('Query saved successfully:', data);
        })
        .catch(error => console.error('Error:', error));
    };

    function clearResults() {
        document.getElementById('model1-results').innerHTML = '';
        document.getElementById('model2-results').innerHTML = '';
        document.getElementById('model3-results').innerHTML = '';
        document.getElementById('model4-results').innerHTML = '';
    }

    function clearLLMAnswers() {
        document.querySelectorAll('.llm-answer-content1').forEach(el => el.innerHTML = '');
        document.querySelectorAll('.llm-answer1').forEach(el => el.style.display = 'none');
    }

    function clearLLMAnswerContent() {
        const finalAnswerContent = document.querySelector('.llm-answer-content1');
        finalAnswerContent.innerHTML = '';
    }

    function clearExistingModal() {
        const existingModal = document.querySelector('.modal');
        if (existingModal) {
            document.body.removeChild(existingModal);
        }
    }

    function clearAdditionalInfo() {
        const additionalInfoContainer = document.querySelector('.llm-answer-content2');
        additionalInfoContainer.innerHTML = '';
        additionalInfoContainer.closest('.llm-answer2').style.display = 'none';
    }

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
                        </div>
                        <div class="relevant-score-right">
                            <img src="data:image/jpeg;base64,${doc.image_data}" class="compact-image" onclick="enlargeImage(this)">
                        </div>
                    </div>
                    <hr><br>`; // Add horizontal line here
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
        clearLLMAnswerContent(); // Call the function to clear only the LLM answer content
    
        // Fetch the search results from /retrieve-results
        fetch('/retrieve-results')
            .then(response => response.json())
            .then(results => {
                // Store the results using /store-scores
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
                    .catch(error => console.error('Error fetching NDCG scores:', error));
                })
                .catch(error => console.error('Error storing scores:', error));
            })
            .catch(error => console.error('Error retrieving results:', error));
    };
    
    function displayNDCGScores(ndcg_scores) {
        // Clear existing NDCG scores
        document.querySelectorAll('.ndcg-score').forEach(el => el.remove());
    
        document.getElementById('model1-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG@3: <span class="ndcg-value">${ndcg_scores.model_1_documents.toFixed(2)}</span></div>`);
        document.getElementById('model2-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG@3: <span class="ndcg-value">${ndcg_scores.model_2_documents.toFixed(2)}</span></div>`);
        document.getElementById('model3-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG@3: <span class="ndcg-value">${ndcg_scores.model_3_documents.toFixed(2)}</span></div>`);
        document.getElementById('model4-results').insertAdjacentHTML('beforeend', `<div class="ndcg-score">NDCG@3: <span class="ndcg-value">${ndcg_scores.model_4_documents.toFixed(2)}</span></div>`);
    }

});
