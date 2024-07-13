document.addEventListener("DOMContentLoaded", () => {
    // Example words data
    const words = [
        {
            word: "placatory",
            pronunciation: "pləˈkeɪtəri",
            definition: "撫慰的",
            example: "The tone of her voice was placatory."
        },
        {
            word: "explore",
            pronunciation: "ɪkˈsplɔr",
            definition: "探索",
            example: "The best way to explore the countryside is on foot."
        }
    ];

    const wordList = document.getElementById("word-list");
    if (wordList) {
        words.forEach(word => {
            const wordItem = document.createElement("div");
            wordItem.classList.add("word-item");
            wordItem.innerHTML = `
                <h3>${word.word}</h3>
                <p><strong>KK:</strong> ${word.pronunciation}</p>
                <p><strong>解釋:</strong> ${word.definition}</p>
                <p><strong>例句:</strong> ${word.example}</p>
            `;
            wordItem.addEventListener("click", () => openWordDetail(word));
            wordList.appendChild(wordItem);
        });
    }
});

function searchWord() {
    const query = document.getElementById("search-input").value.toLowerCase();
    const wordItems = document.querySelectorAll(".word-item");
    wordItems.forEach(item => {
        const word = item.querySelector("h3").textContent.toLowerCase();
        if (word.includes(query)) {
            item.style.display = "block";
        } else {
            item.style.display = "none";
        }
    });
}

function openFilterPopup() {
    document.getElementById("filter-popup").style.display = "flex";
}

function closeFilterPopup() {
    document.getElementById("filter-popup").style.display = "none";
}

function applyFilter() {
    // Implement filter logic here
    closeFilterPopup();
}

function uploadPhoto() {
    const fileInput = document.getElementById("image-upload");
    const file = fileInput.files[0];
    if (file) {
        // Implement upload logic here
        window.location.href = "confirm.html";
    }
}

function retakePhoto() {
    const fileInput = document.getElementById("image-upload");
    fileInput.value = "";
}

function submitPhoto() {
    // Implement submit logic here
    showSuccessMessage();
}

function saveWords() {
    // Implement save logic here
    window.location.href = "index.html";
}

function showSuccessMessage() {
    const message = document.getElementById("success-message");
    message.style.display = "block";
    setTimeout(() => {
        message.style.display = "none";
    }, 3000);
}

function openWordDetail(word) {
    const detailWindow = window.open("", "_blank");
    detailWindow.document.write(`
        <html>
        <head>
            <title>${word.word}</title>
            <link rel="stylesheet" href="styles.css">
        </head>
        <body>
            <div class="word-detail">
                <h1>${word.word}</h1>
                <p><strong>KK:</strong> ${word.pronunciation}</p>
                <p><strong>解釋:</strong> ${word.definition}</p>
                <p><strong>例句:</strong> ${word.example}</p>
                <button onclick="window.close()">關閉</button>
            </div>
        </body>
        </html>
    `);
}
