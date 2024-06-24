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
    };

    // Event listener for the Manual button
    document.getElementById('getManualTopics').onclick = function () {
        fetchTopics('/get-manual-topics');
    };

    // Event listener for the Random button
    document.getElementById('searchRandomContext').onclick = function () {
        topicDropdown.style.display = 'none'; // Hide the dropdown
        inputField.style.display = 'block'; // Show input field for typing
        inputField.value = ''; // Clear previous input
        inputField.focus(); // Focus on the input field

        // Fetch a random document immediately upon clicking Random
        fetch('/get-random-document')
            .then(response => response.json())
            .then(doc => {
                const results = document.getElementById('results');
                results.innerHTML = `<strong>Title:</strong> ${doc.title}<br><strong>Content:</strong> ${doc.content}`;
            });
    };

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
            });
    };

    function displayResults(documents, elementId) {
        const container = document.getElementById(elementId);
        container.innerHTML = '';

        // Iterate over each document data
        documents.forEach((doc, index) => {
            setTimeout(() => {
                const div = document.createElement('div');
                div.innerHTML = `<strong>Title:</strong> ${doc.title}<br><strong>Content:</strong> ${doc.content}<br><strong>Score:</strong> ${doc.score}`;
                container.appendChild(div);
            }, index * 400); // Delay of 0 for the first, 200ms for the second, and so on
        });
    }
});
