document.addEventListener('DOMContentLoaded', function () {
    const annotationQuery = document.getElementById('annotation-query');
    const annotationContainer = document.getElementById('annotation-results');

    // Fetch and display the search results and query
    fetch('/retrieve-results')
        .then(response => response.json())
        .then(searchResults => {
            const query = searchResults.query || 'No Query Found';
            annotationQuery.innerHTML = `<h2>${query}</h2>`;

            // Combine all documents into one array
            const allDocuments = [
                ...searchResults.BM25_documents,
                ...searchResults['BM25-llava_documents'],
                ...searchResults.Clip_documents,
                ...searchResults.Mistral_documents,
                ...searchResults['Mistral-llava_documents'],
                ...searchResults.Qwen2_documents
            ];

            // Remove duplicate documents
            const uniqueDocuments = [];
            const titles = new Set();
            allDocuments.forEach(doc => {
                const uniqueKey = `${doc.title}-${doc.content}-${doc.image_data}`;
                if (!titles.has(uniqueKey)) {
                    titles.add(uniqueKey);
                    uniqueDocuments.push(doc);
                }
            });

            // Shuffle the documents randomly
            uniqueDocuments.sort(() => Math.random() - 0.5);

            // Display each document in the annotation container
            uniqueDocuments.forEach((doc, index) => {
                const div = document.createElement('div');
                div.classList.add('document-info-container');
                div.innerHTML = `
                    <div class="document-info">
                        <strong>Title:</strong> <span class="doc-title">${doc.title}</span><br>
                        <strong>Content:</strong> <span class="doc-content">${doc.content}</span><br>
                        <div class="relevant-score-container">
                            <div class="relevant-score-row">
                                <strong>Relevance:</strong>
                                <select class="relevance-score-input">
                                    <option value="" disabled selected>Select Relevance</option>
                                    <option value="0">0 (No)</option>
                                    <option value="1">1 (Partially Relevant)</option>
                                    <option value="2">2 (Relevant)</option>
                                    <option value="3">3 (Highly Relevant)</option>
                                </select>
                            </div>
                            <div class="relevant-score-row">
                                <strong>Completeness:</strong>
                                <select class="completeness-score-input">
                                    <option value="" disabled selected>Select Completeness</option>
                                    <option value="0">0 (No)</option>
                                    <option value="1">1 (Somewhat)</option>
                                    <option value="2">2 (Mostly)</option>
                                    <option value="3">3 (Yes)</option>
                                </select>
                            </div>
                            <!-- Include title and content in hidden-info for evaluation purposes -->
                            <div class="hidden-info">
                                <span class="hidden-title">${doc.title}</span>
                                <span class="hidden-content">${doc.content}</span>
                            </div>
                        </div>
                    </div>
                    <div class="compact-image-container">
                        <img src="data:image/jpeg;base64,${doc.image_data}" class="compact-image" onclick="enlargeImage(this)">
                    </div>
                    <hr><br>`; // Add horizontal line here
                annotationContainer.appendChild(div);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });

    // Add the random annotation feature
    document.getElementById('annotateButton').onclick = function () {
        const documents = document.getElementsByClassName('relevant-score-container');
        Array.from(documents).forEach((doc) => {
            const relevanceInput = doc.querySelector('.relevance-score-input');
            const completenessInput = doc.querySelector('.completeness-score-input');
            relevanceInput.value = Math.floor(Math.random() * 4); // Random value between 0 and 3
            completenessInput.value = Math.floor(Math.random() * 4); // Random value between 0 and 3
        });
    };

    document.getElementById('saveAnnotations').onclick = function () {
        // Get annotator details
        const annotatorName = document.getElementById('annotatorName').value;

        // Get document annotations
        const documents = document.getElementsByClassName('document-info-container');
        const annotations = Array.from(documents).map(doc => {
            return {
                title: doc.querySelector('.hidden-title').innerText,
                content: doc.querySelector('.hidden-content').innerText,
                relevance: doc.querySelector('.relevance-score-input').value,
                completeness: doc.querySelector('.completeness-score-input').value
            };
        });
    
        // Check if all annotations are complete
        const allAnnotated = annotations.every(annotation => annotation.relevance !== '' && annotation.completeness !== '');
    
        if (allAnnotated && annotatorName) {
            // Include annotator details in the data
            const data = {
                annotatorName,
                annotations
            };
            // If all annotations are complete, save them
            fetch('/save-annotations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Annotations saved successfully:', data);
                // Close the current annotation page
                window.close();
            })
            .catch(error => {
                console.error('Error:', error);
            });
        } else {
            // If not all annotations are complete, show the centered message
            const centeredMessage = document.getElementById('centered-message');
            centeredMessage.style.display = 'block';
            setTimeout(() => {
                centeredMessage.style.display = 'none';
            }, 3000);
        }
    };
    
});
