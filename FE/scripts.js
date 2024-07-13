document.addEventListener("DOMContentLoaded", () => {
    // Example words data
    const words = [
        {
            word: "placatory",
            pronunciation: "pləˈkeɪtəri",
            definition: "撫慰的",
            example: "The tone of her voice was placatory.",
            derivatives: "",
            synonyms: "",
            roots: "",
            more: ""
        },
        {
            word: "explore",
            pronunciation: "ɪkˈsplɔr",
            definition: "探索",
            example: "The best way to explore the countryside is on foot.",
            derivatives: "exploration, explorer",
            synonyms: "investigate, look into",
            roots: "ex- (向外), -plor (哭叫)",
            more: "The word 'explore' is derived from the Latin word 'explorare', meaning 'to cry out', which was later used metaphorically to refer to 'looking for information or searching for something'."
        }
    ];

    // Render word list on index.html
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

 
    
    // Render word detail on word.html
    const wordDetail = document.getElementById("word-detail");
    if (wordDetail) {
        const urlParams = new URLSearchParams(window.location.search);
        const wordParam = urlParams.get("word");
        const word = words.find(w => w.word === wordParam);
        if (word) {
            wordDetail.innerHTML = `
                <h1>${word.word}</h1>
                <p><strong>KK:</strong> ${word.pronunciation}</p>
                <p><strong>解釋:</strong> ${word.definition}</p>
                <p><strong>例句:</strong> ${word.example}</p>
                <p><strong>衍生詞:</strong> ${word.derivatives}</p>
                <p><strong>同義詞:</strong> ${word.synonyms}</p>
                <p><strong>字根字首:</strong> ${word.roots}</p>
                <p><strong>更多說明:</strong> ${word.more}</p>
            `;
        }
    }



    // Function to navigate to previous or next word
    const navigateWord = (direction) => {
        const currentIndex = words.findIndex(word => word.word === wordDetail.querySelector('h1').textContent);
        let nextIndex = currentIndex + direction;
        if (nextIndex < 0) {
            nextIndex = words.length - 1; // Wrap around to last word
        } else if (nextIndex >= words.length) {
            nextIndex = 0; // Wrap around to first word
        }
        const nextWord = words[nextIndex];
        displayWordDetail(nextWord);
        updateUrlParam(nextWord.word);
    };

    // Function to display word detail
    const displayWordDetail = (word) => {
        if (word) {
            wordDetail.innerHTML = `
                <h1>${word.word}</h1>
                <p><strong>KK:</strong> ${word.pronunciation}</p>
                <p><strong>解釋:</strong> ${word.definition}</p>
                <p><strong>例句:</strong> ${word.example}</p>
                <p><strong>衍生詞:</strong> ${word.derivatives}</p>
                <p><strong>同義詞:</strong> ${word.synonyms}</p>
                <p><strong>字根字首:</strong> ${word.roots}</p>
                <p><strong>更多說明:</strong> ${word.more}</p>
            `;
        }
    };

    // Function to update URL parameter
    const updateUrlParam = (word) => {
        const newUrl = `${window.location.pathname}?word=${encodeURIComponent(word)}`;
        window.history.pushState({path: newUrl}, '', newUrl);
    };

    // Bind navigation buttons
    document.getElementById("prevWordBtn").addEventListener("click", () => navigateWord(-1));
    document.getElementById("nextWordBtn").addEventListener("click", () => navigateWord(1));


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


    // Handle webcam and photo upload process
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    const fileInput = document.getElementById('image-upload');
    const fileInfo = document.querySelector('.file-info');

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
            video.srcObject = stream;
            video.play();
        });
    }

    window.capturePhoto = function() {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
            const file = new File([blob], "webcam_photo.png", { type: "image/png" });
            uploadToBackend(file);
        });
    }

    window.submitPhoto = function() {
        const file = fileInput.files[0];
        if (file) {
            uploadToBackend(file);
        }
    }

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            fileInfo.textContent = file.name;
        } else {
            fileInfo.textContent = '未選取任何檔案';
        }
    });

    function uploadToBackend(file) {
        const formData = new FormData();
        formData.append('image', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            window.location.href = 'confirm.html';
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
});



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

function openWordDetail(word) {
    const wordQuery = encodeURIComponent(word.word);
    location.href = `word.html?word=${wordQuery}`;
}



function submitWords() {
    const inputElement = document.getElementById('wordInput');
    const words = inputElement.value.trim();
    
    if (!validateWords(words)) {
        alert('請輸入英文單字，並以「,」分隔');
        return;
    }
    
    // 送純文字給後端的處理邏輯
    // 可以使用 fetch 或其他方法將文字送給後端
    
    // 清空輸入框
    inputElement.value = '';
}

function validateWords(words) {
    // 檢查是否是英文單字且以「,」分隔
    const wordArray = words.split(',');
    
    for (let word of wordArray) {
        if (!/^[a-zA-Z]+$/.test(word.trim())) {
            return false;
        }
    }
    
    return true;
}

// 監聽 Enter 鍵事件
document.getElementById('wordInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        submitWords();
    }
});
