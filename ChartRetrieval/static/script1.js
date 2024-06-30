document.addEventListener('DOMContentLoaded', function () {
    const topicDropdown = document.getElementById('topicDropdown');
    const inputField = document.getElementById('inputField');

    // Function to fetch topics and populate the dropdown
    function fetchTopics(url) {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                topicDropdown.innerHTML = ''; // Clear existing options
                data.topics.forEach(topic => {
                    let option = new Option(topic, topic);
                    topicDropdown.add(option);
                });
                topicDropdown.style.display = 'block'; // Show dropdown
                inputField.style.display = 'none'; // Hide input field
            });
    }

    // Event listener for the Touche button
    document.getElementById('getTopics').onclick = function () {
        fetchTopics('/get-topics');

        // Clear all previous results and LLM answers
        clearResults();
        clearLLMAnswers();

    };

    // Event listener for the Manual button
    document.getElementById('getManualTopics').onclick = function () {
        fetchTopics('/get-manual-topics');

        // Clear all previous results and LLM answers
        clearResults();
        clearLLMAnswers();

    };

    // Event listener for the Random button
    document.getElementById('searchRandomContext').onclick = function () {
        topicDropdown.style.display = 'none'; // Hide the dropdown
        inputField.style.display = 'block'; // Show input field for typing
        inputField.value = ''; // Clear previous input
        inputField.focus(); // Focus on the input field

        // Fetch a random image immediately upon clicking Random
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

                    // Close the modal when clicking outside the image
                    modal.onclick = function() {
                        document.body.removeChild(modal);
                    };
                } else {
                    alert("No image found");
                }
            });
            
        // Clear all previous results and LLM answers
        clearResults();
        clearLLMAnswers();
    };

    // Function to clear all retrieved answers
    function clearResults() {
        document.getElementById('model1-results').innerHTML = '';
        document.getElementById('model2-results').innerHTML = '';
        document.getElementById('model3-results').innerHTML = '';
        document.getElementById('model4-results').innerHTML = '';
    }

    // Function to clear and hide all LLM answers
    function clearLLMAnswers() {
        document.querySelectorAll('.llm-answer-content').forEach(el => el.innerHTML = '');
        document.querySelectorAll('.llm-answer').forEach(el => el.style.display = 'none');
    }

    // Search functionality for both dropdown and input field
    document.getElementById('search').onclick = function () {
        const isDropdownVisible = topicDropdown.style.display !== 'none';
        const topic = isDropdownVisible ? topicDropdown.value : inputField.value;

        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic })
        })
            .then(response => response.json())
            .then(data => {
                // Display results for each model
                displayResults(data.model_1_documents, 'model1-results');
                displayResults(data.model_2_documents, 'model2-results');
                displayResults(data.model_3_documents, 'model3-results');
                displayResults(data.model_4_documents, 'model4-results');

                // Show the final answer titles
                document.querySelectorAll('.llm-answer').forEach(el => el.style.display = 'block');
            });
    };

    // Event listener for the Generate Answers button
    document.getElementById('generateAnswers').onclick = function () {
        // Simulate fetching the answers from the LLM
        setTimeout(() => {
            document.querySelector('#model1-answer .llm-answer-content').textContent = 'Final Answer for BM25';
            document.querySelector('#model2-answer .llm-answer-content').textContent = 'Final Answer for Mistral';
            document.querySelector('#model3-answer .llm-answer-content').textContent = 'Final Answer for GTE-QWEN2';
            document.querySelector('#model4-answer .llm-answer-content').textContent = 'Final Answer for CLIP';
        }, 1000); // Simulate a delay
    };

    // Function to display results
    function displayResults(documents, elementId) {
        const container = document.getElementById(elementId);
        container.innerHTML = ''; // Clear existing content

        // Iterate over each document data
        documents.forEach((doc, index) => {
            setTimeout(() => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <strong>Title:</strong> ${doc.title}<br>
                    <strong>Content:</strong> ${doc.content}<br>
                    <div class="relevant-score-container">
                        <div class="relevant-score-left">
                            <div class="relevant-score-row">
                                <strong>Score:</strong> ${doc.score}
                            </div>
                            <div class="relevant-score-row">
                                <strong>Relevance:</strong>
                                <select id="relevance-score-${index}" class="relevant-score-input">
                                    <option value="-1">-1(Unable to Judge)</option>
                                    <option value="0">0(No)</option>
                                    <option value="1">1(Partially Relevant)</option>
                                    <option value="2">2(Relevant)</option>
                                    <option value="3">3(Highly Relevant)</option>
                                </select>
                            </div>
                            <div class="relevant-score-row">
                                <strong>Completeness:</strong>
                                <select id="completeness-score-${index}" class="completeness-score-input">
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
                    </div>`;
                container.appendChild(div);
            }, index * 400); // Delay of 0 for the first, 200ms for the second, and so on
        });
    }


    // Function to enlarge image
    window.enlargeImage = function(img) {
        const modal = document.createElement('div');
        modal.classList.add('modal');
        const enlargedImg = document.createElement('img');
        enlargedImg.src = img.src;
        enlargedImg.classList.add('enlarged-image');

        // Determine the position of the small image
        const imgRect = img.getBoundingClientRect();
        const windowWidth = window.innerWidth;
        const isLeftOfCenter = imgRect.left < windowWidth / 2;

        // Set the position based on the small image's position
        if (isLeftOfCenter) {
            enlargedImg.style.marginLeft = '50%'; // Center in the right half
        } else {
            enlargedImg.style.marginRight = '50%'; // Center in the left half
        }

        modal.appendChild(enlargedImg);
        document.body.appendChild(modal);

        // Close the modal when clicking outside the image
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                document.body.removeChild(modal);
            }
        });

        // Focus on the first dropdown field (relevance score)
        const parentDiv = img.closest('.relevant-score-container');
        const relevanceDropdown = parentDiv.querySelector('.relevant-score-input');
        if (relevanceDropdown) {
            relevanceDropdown.focus();
        }

        // Handle Enter key to move to the next dropdown field
        parentDiv.querySelectorAll('select').forEach((select, index, selects) => {
            select.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    const nextSelect = selects[index + 1];
                    if (nextSelect) {
                        nextSelect.focus();
                    } else {
                        // Optionally, cycle back to the first select if there's no next select
                        selects[0].focus();
                    }
                }
            });
        });
    };

});
