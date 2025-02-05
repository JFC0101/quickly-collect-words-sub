// 加載完成後的初始化
// fileUpload: 選取上傳文件的 <input> 元素。
// fileName: 顯示文件名稱的 <span> 或 <div> 元素。
// video: 顯示網絡攝像頭影像的 <video> 元素。
document.addEventListener("DOMContentLoaded", function() {
    const fileUpload = document.getElementById('file-upload');
    const fileName = document.getElementById('file-name');
    const video = document.getElementById('webcam');
    const modelSelect = document.querySelector('.user-options');
    const webcamSection = document.getElementById('desktop-webcam-section');
    const divider = document.getElementById('desktop-divider');

    // Function to check if the device is mobile
    function isMobileDevice() {
        return window.innerWidth <= 767; // Change this value as needed
    }

    // Hide webcam section on mobile devices
    if (isMobileDevice()) {
        webcamSection.style.display = 'none';
        divider.style.display = 'none';
    } else {
        // Initialize webcam only if the device is not mobile
        const video = document.getElementById('webcam');
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(stream) {
                    video.srcObject = stream; //將攝像頭的視頻流設置為 <video> 元素的來源
                    video.play(); // 確保視頻播放
                })
                .catch(function(error) {
                    console.error("Error accessing webcam: " + error);
                });
        } else {
            console.error("getUserMedia not supported on your browser!");
        }
    }

    //當文件選取改變時 (fileUpload.onchange)，更新 fileName 元素的文本內容。
    fileUpload.onchange = function() {
        if (fileUpload.files.length > 0) {
            fileName.textContent = fileUpload.files[0].name;
        } else {
            fileName.textContent = "未選取任何檔案";
        }
    };

    function getSelectedModel() {
        return modelSelect.value;
    }

    //捕捉webcam畫面和呼叫執行上傳圖像的function
    function captureAndUpload() {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        // Capture image from webcam
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height); //將視頻流畫到 <canvas> 上

        // 將 <canvas> 的內容轉換為 blob，並調用 uploadBlob 函數上傳。
        canvas.toBlob(function(blob) {
            if(blob) {
                uploadBlob(blob);
            } else {
                console.error('Failed to convert canvas to blob.');
            }
        }, 'image/jpeg');
    }

    //將webcam畫面執行上傳圖像，並且執行 upload 函數處理後續要顯示的單字
    function uploadBlob(blob) {
        const formData = new FormData(); //創建 FormData 對象，並將 blob 文件添加到 FormData 中。
        const model = getSelectedModel();
        formData.append('file', blob, 'capture.jpg');
        formData.append('model', model);

        //載入 loading 動畫
        document.getElementById('loadingSpinner').style.display = 'flex';
        
        fetch('/upload_file', { //使用 fetch 向 /upload_file 發送 POST 請求，上傳圖像文件。
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 請求成功後，繼續向 /upload 發送 POST 請求，處理上傳的文件。
            if (data.success) {
                
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // 将数据存储在 sessionStorage
                    sessionStorage.setItem('processedImage', data.image);
                    sessionStorage.setItem('selectedWords', JSON.stringify(data.words));
                    sessionStorage.setItem('ocrBoxes', JSON.stringify(data.ocr_boxes));
                    window.location.href = `/word-preview`;
                })
                .catch(error => {
                    document.getElementById('loadingSpinner').style.display = 'none';
                    console.error('Error:', error);
                });
            } else {
                document.getElementById('loadingSpinner').style.display = 'none';
                console.error('Error:', data.error);
            }
        })
    }

    //將選取的圖片上傳，並且執行 upload 函數處理後續要顯示的單字
    function uploadFile() {
        const input = document.getElementById('file-upload');
        const model = getSelectedModel();

        //載入 loading 動畫
        document.getElementById('loadingSpinner').style.display = 'flex';

        if (input.files.length > 0) {
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('model', model);

            fetch('/upload_file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // After successful upload, process uploaded file if needed
                    fetch('/upload', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        // 将数据存储在 sessionStorage
                        sessionStorage.setItem('processedImage', data.image);
                        sessionStorage.setItem('selectedWords', JSON.stringify(data.words));
                        sessionStorage.setItem('ocrBoxes', JSON.stringify(data.ocr_boxes));
                        window.location.href = `/word-preview`;
                    })
                    .catch(error => {
                        document.getElementById('loadingSpinner').style.display = 'none';
                        console.error('Error:', error);
                    });
                } else {
                    document.getElementById('loadingSpinner').style.display = 'none';
                    console.error('Error:', data.error);
                }
            })
            .catch(error => {
                document.getElementById('loadingSpinner').style.display = 'none';
                console.error('Error:', error);
            });
        } else {
            document.getElementById('loadingSpinner').style.display = 'none';
            alert('請選擇檔案');
        }
    }

    window.captureAndUpload = captureAndUpload;
    window.uploadFile = uploadFile;
});
