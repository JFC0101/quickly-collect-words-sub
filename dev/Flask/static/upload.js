
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
        // After successful upload, process uploaded file if needed
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Redirect to word preview page with image and words data
            window.location.href = `/word-preview?image=${data.image}&words=${data.words}`;
        })
        .catch(error => {
            console.error('Error processing uploaded file:', error);
        });
    })
    .catch(error => {
        console.error('Error uploading file:', error);
    });
}

function uploadFile() {
    const input = document.getElementById('file-upload');
    if (input.files.length > 0) {
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload_file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
             // After successful upload, process uploaded file if needed
             fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Redirect to word preview page with image and words data
                window.location.href = `/word-preview?image=${data.image}&words=${data.words}`;
            })
            .catch(error => {
                console.error('Error processing uploaded file:', error);
            });
        })
        .catch(error => {
            console.error('Error uploading file:', error);
        });
    } else {
        alert('請選擇檔案');
    }
}