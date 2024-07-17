document.addEventListener("DOMContentLoaded", function() {
    const fileUpload = document.getElementById('file-upload');
    const fileName = document.getElementById('file-name');
    const video = document.getElementById('webcam');

    // Initialize webcam
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
            })
            .catch(function(error) {
                console.error("Error accessing webcam: " + error);
            });
    }

    // Update file name on file selection
    fileUpload.onchange = function() {
        if (fileUpload.files.length > 0) {
            fileName.textContent = fileUpload.files[0].name;
        } else {
            fileName.textContent = "未選取任何檔案";
        }
    };
});

function captureAndUpload() {
    const video = document.getElementById('webcam');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    // Capture image from webcam
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob and upload
    canvas.toBlob(function(blob) {
        uploadBlob(blob);
    }, 'image/jpeg');
    
}


function uploadBlob(blob) {
    const formData = new FormData();
    formData.append('file', blob, 'capture.jpg');

    fetch('/upload_file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 跳转到单词预览页面，并传递上传的图片和可能的单词
        window.location.href = `/word-preview?image=${data.image}&words=${data.words}`;
    })
    .catch(error => {
        console.error('Error uploading file:', error);
    });

    /*.then(data => {
        alert('Capture uploaded successfully');
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });*/
}


function uploadFile() {
    const input = document.getElementById('file-upload');
    if (input.files.length > 0) {
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 跳转到单词预览页面，并传递上传的图片和可能的单词
            window.location.href = `/word-preview?image=${data.image}&words=${data.words}`;
        })
        .catch(error => {
            console.error('Error uploading file:', error);
        });
    } else {
        alert('請選擇檔案');
    }
}


$(document).ready(function() {
    $('#prev-word').click(function() {
        var word = $(this).data('word');
        console.log('Previous word:', word); // 調試信息
        window.location.href = '/word?word=' + word;
    });

    $('#next-word').click(function() {
        var word = $(this).data('word');
        console.log('Next word:', word); // 調試信息
        window.location.href = '/word?word=' + word;
    });
});



//按了會把確認的單字們上傳與刪除的功能

function deleteWord(word) {
    const wordElement = document.querySelector(`.word-item .word-text:contains('${word}')`).closest('.word-item');
    wordElement.remove();
}

function sendWords() {
    const words = [];
    document.querySelectorAll('.word-text').forEach(element => {
        words.push(element.textContent.trim());
    });
    // 在这里添加发送单词到服务器的逻辑，可以使用 fetch 函数发送 POST 请求
    console.log('Sending words:', words);
}