document.addEventListener('DOMContentLoaded', function () {
    const topicDropdown = document.getElementById('topicDropdown');
    const inputField = document.getElementById('inputField');

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
    };

    document.getElementById('getManualTopics').onclick = function () {
        fetchTopics('/get-manual-topics');
    };

    document.getElementById('searchRandomContext').onclick = function () {
        topicDropdown.style.display = 'none';
        inputField.style.display = 'block';
        inputField.value = '';
        inputField.focus();

        fetch('/get-random-document')
            .then(response => response.json())
            .then(doc => {
                const resultsLeft = document.getElementById('results-left');
                resultsLeft.innerHTML = `<strong>Title:</strong> ${doc.title}<br><strong>Content:</strong> ${doc.content}`;
            });
    };

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
                const resultsLeft = document.getElementById('results-left');
                const resultsRight = document.getElementById('results-right');
                resultsLeft.innerHTML = '<h3>Model 1 Results:</h3>';
                resultsRight.innerHTML = '<h3>Model 2 Results:</h3>';

                data.model_1_documents.forEach((doc, index) => {
                    setTimeout(() => {
                        const div = document.createElement('div');
                        div.innerHTML = `<strong>Title:</strong> ${doc.title}<br><strong>Content:</strong> ${doc.content}<br><strong>Score:</strong> ${doc.score}`;
                        resultsLeft.appendChild(div);
                    }, index * 400);
                });

                data.model_2_documents.forEach((doc, index) => {
                    setTimeout(() => {
                        const div = document.createElement('div');
                        div.innerHTML = `<strong>Title:</strong> ${doc.title}<br><strong>Content:</strong> ${doc.content}<br><strong>Score:</strong> ${doc.score}`;
                        resultsRight.appendChild(div);
                    }, index * 400);
                });
            });
    };
});
