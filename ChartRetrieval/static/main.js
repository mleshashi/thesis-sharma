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
        clearTopDocuments();
    };

    document.getElementById('getManualTopics').onclick = function () {
        fetchTopics('/get-manual-topics');
        clearResults();
        clearLLMAnswers();
        clearExistingModal();
        clearTopDocuments();
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
        clearTopDocuments();
    };

    function performSearch() {
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
            answerInfoContainer.style.display = 'flex';
            finalAnswer1.style.display = 'block';
            finalAnswer2.style.display = 'block';

            const annotationURL = '/annotation';
            window.open(annotationURL, '_blank');
        })
        .catch(error => {
            console.error('Error:', error);
        });

        loadingModal.classList.remove('hidden');

        setTimeout(() => {
            loadingModal.classList.add('hidden');
        }, 1000);

        clearExistingModal();
        clearLLMAnswers();
        clearTopDocuments();
    }

    document.getElementById('search').onclick = performSearch;

    inputField.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            performSearch();
        }
    });

    document.getElementById('generateAnswers').onclick = function () {

        // Clear the existing LLM answers and top documents
        clearTopDocuments();
        clearLLMAnswers();

        // Ask for which NDCG value to use (1, 2, or 3)
        const ndcgValue = prompt("Enter which NDCG value to use (1, 2, or 3):", "1");
    
        // Validate the input
        if (![1, 2, 3].includes(parseInt(ndcgValue))) {
            alert("Invalid input. Please enter 1, 2, or 3.");
            return;
        }
    
        // Fetch the prepared LLM input and generate the answer
        fetch(`/prepare-llm-input?ndcg=${ndcgValue}`)
            .then(response => response.json())
            .then(data => {
                if (data.message !== "LLM input prepared and stored successfully") {
                    throw new Error("Failed to prepare LLM input.");
                }
    
                // Retrieve the top documents
                return fetch('/retrieve-top-documents');
            })
            .then(response => response.json())
            .then(data => {
                displayTopDocuments(data.top_documents);
    
                // Generate the LLM answers
                return fetch('/generate-llm-answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
            })
            .then(response => response.json())
            .then(() => {
                // Retrieve scores including the generated LLM answers
                return fetch('/retrieve-llm-answers');
            })
            .then(response => response.json())
            .then(scores => {
                console.log("Retrieve Scores Response:", scores);
                const finalAnswerContent1 = document.querySelector('.llm-answer-content1');
                const finalAnswerContent2 = document.querySelector('.llm-answer-content2');
    
                const gptAnswer = scores.gpt_llm_answer;
                const lamaAnswer = scores.lama_llm_answer;
    
                // Randomly decide the order of answers
                const placeGPTFirst = Math.random() < 0.5;
    
                // Function to render the content in HTML
                const renderAnswer = (answer, container, answerId) => {
                    if (answer && answer.choices && answer.choices.length > 0 && answer.choices[0].message) {
                        const markdownContent = answer.choices[0].message.content;
                        const htmlContent = marked.parse(markdownContent); // Use marked.parse to convert Markdown to HTML
                        container.innerHTML = htmlContent; // Display the HTML content
                        container.setAttribute('data-answer-id', answerId); // Set data-answer-id
                    } else {
                        container.innerHTML = "No valid response received.";
                    }
                };
    
                // Place GPT and Lama answers based on the random decision
                if (placeGPTFirst) {
                    renderAnswer(gptAnswer, finalAnswerContent1, 'gpt_llm_answer');
                    renderAnswer(lamaAnswer, finalAnswerContent2, 'lama_llm_answer');
                } else {
                    renderAnswer(lamaAnswer, finalAnswerContent1, 'lama_llm_answer');
                    renderAnswer(gptAnswer, finalAnswerContent2, 'gpt_llm_answer');
                }
    
                // Show the answers container
                document.querySelector('.llm-answer-info-container').classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error:', error);
                const finalAnswerContent1 = document.querySelector('.llm-answer-content1');
                const finalAnswerContent2 = document.querySelector('.llm-answer-content2');
                finalAnswerContent1.innerHTML = `An error occurred while generating the answer: ${error.message}`;
                finalAnswerContent2.innerHTML = `An error occurred while generating the answer: ${error.message}`;
                document.querySelector('.llm-answer-info-container').classList.remove('hidden'); // Show the error message
            });
    };
    

    document.getElementById('save').onclick = function () {
        // Collect annotation values for Final Answer 1
        const relevance1 = document.querySelector('.llm-answer1 .relevance-dropdown').value;
        const faithfulness1 = document.querySelector('.llm-answer1 .faithfulness-dropdown').value;
        const answerId1 = document.querySelector('.llm-answer-content1').getAttribute('data-answer-id');
    
        // Collect annotation values for Final Answer 2
        const relevance2 = document.querySelector('.llm-answer2 .relevance-dropdown').value;
        const faithfulness2 = document.querySelector('.llm-answer2 .faithfulness-dropdown').value;
        const answerId2 = document.querySelector('.llm-answer-content2').getAttribute('data-answer-id');

        // Validate the annotations
        if (!relevance1 || !faithfulness1 || !relevance2 || !faithfulness2) {
            showMessage('Please complete all annotations before saving.');
            return;
        }
    
        // Retrieve the LLM answers
        fetch('/retrieve-llm-answers')
            .then(response => response.json())
            .then(scores => {
                // Add annotations to the LLM answers based on the stored order
                if (scores[answerId1]) {
                    scores[answerId1].annotation = {
                        relevance: relevance1,
                        faithfulness: faithfulness1
                    };
                }
                if (scores[answerId2]) {
                    scores[answerId2].annotation = {
                        relevance: relevance2,
                        faithfulness: faithfulness2
                    };
                }
    
                // Send updated LLM answers back to the server
                return fetch('/save-llm-answers', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(scores)
                });
            })
            .then(response => response.json())
            .then(data => {
                console.log('Annotations saved successfully:', data);
            // Save the query and other relevant data
            return fetch('/save-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });
        })
        .then(response => response.json())
        .then(data => {
            showMessage('Annotation saved');
            console.log('Query saved successfully:', data);
        })
        .catch(error => console.error('Error saving data:', error));
    };

    function showMessage(message) {
        const centeredMessage = document.getElementById('centered-message');
        centeredMessage.innerText = message;
        centeredMessage.style.display = 'block';
        setTimeout(() => {
            centeredMessage.style.display = 'none';
        }, 3000);
    }

    function clearResults() {
        ['model1-results', 'model2-results', 'model3-results', 'model4-results', 'model5-results', 'model6-results'].forEach(id => {
            document.getElementById(id).innerHTML = '';
        });
    }
    
    function clearLLMAnswers() {
        // Clear the content
        ['.llm-answer-content1', '.llm-answer-content2'].forEach(selector => {
            document.querySelectorAll(selector).forEach(el => el.innerHTML = '');
        });
    
        // Reset the relevance and faithfulness dropdowns
        document.querySelectorAll('.relevance-dropdown, .faithfulness-dropdown').forEach(dropdown => {
            dropdown.selectedIndex = 0;
        });
    }

    function clearTopDocuments() {
        const topDocumentsContainer = document.getElementById('top-documents-container');
        topDocumentsContainer.innerHTML = '';
    }
    
    function clearExistingModal() {
        const existingModal = document.querySelector('.modal');
        if (existingModal) {
            document.body.removeChild(existingModal);
        }
    }
    

    function displayTopDocuments(documents) {
        const topDocumentsContainer = document.getElementById('top-documents-container');
        topDocumentsContainer.innerHTML = '';
    
        documents.forEach((doc, index) => {
            const div = document.createElement('div');
            div.classList.add('top-document');
            if (documents.length === 1) {
                div.classList.add('single');
            }
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
                </div>`;
            topDocumentsContainer.appendChild(div);
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
        clearLLMAnswers(); // Call the function to clear only the LLM answer content
    
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
    
        // Function to create the NDCG score HTML for a given model
        function createNDCGScoreHTML(modelKey, modelName) {
            return `
                <div class="ndcg-score">NDCG@1: <span class="ndcg-value">${ndcg_scores[1][modelKey].toFixed(2)}</span></div>
                <div class="ndcg-score">NDCG@2: <span class="ndcg-value">${ndcg_scores[2][modelKey].toFixed(2)}</span></div>
                <div class="ndcg-score">NDCG@3: <span class="ndcg-value">${ndcg_scores[3][modelKey].toFixed(2)}</span></div>
            `;
        }
    
        // Insert the NDCG scores for each model
        document.getElementById('model1-results').insertAdjacentHTML('beforeend', createNDCGScoreHTML('BM25_documents', 'Model 1'));
        document.getElementById('model2-results').insertAdjacentHTML('beforeend', createNDCGScoreHTML('BM25-llava_documents', 'Model 2'));
        document.getElementById('model3-results').insertAdjacentHTML('beforeend', createNDCGScoreHTML('Clip_documents', 'Model 3'));
        document.getElementById('model4-results').insertAdjacentHTML('beforeend', createNDCGScoreHTML('Mistral_documents', 'Model 4'));
        document.getElementById('model5-results').insertAdjacentHTML('beforeend', createNDCGScoreHTML('Mistral-llava_documents', 'Model 5'));
        document.getElementById('model6-results').insertAdjacentHTML('beforeend', createNDCGScoreHTML('Qwen2_documents', 'Model 6'));
    }

});
