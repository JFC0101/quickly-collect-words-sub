# quickly-collect-words
Artificial Intelligence Projects Created by Beginners in Taiwan

.env 檔內有 key 資料，因此無分享出來，若希望實際運行 app.py 且可以正常操作，可以自行準備 .env 檔：
LINE_CHANNEL_ACCESS_TOKEN=輸入自己的 token
LINE_CHANNEL_SECRET=輸入自己的 token
GEMINI_API_KEY=輸入自己的 token
GOOGLE_APPLICATION_CREDENTIALS=填入 key.json 檔案位置
SECRET_KEY=輸入自己的設定
SESSION_TYPE=輸入自己的設定

如果希望 LINE 可以正常運行，需再安裝 ngrok.exe

檔案說明：
1. app.py 為 agent & flask 寫在一起的檔案，使用 app.py 運行所有的副程式
2. app_words.db 是資料庫
3. image_processor_opencv 是 opencv 顏色辨識區塊 交集 OCR 的區塊，將單字與繪製的圖片送給 Agent 處理
4. image_processor_yolo5 是 使用 yolo model 進行顏色偵測 交集 OCR 的區塊，將單字與繪製的圖片送給 Agent 處理
5. linebot 部分分別有三個副程式及 Agent 最底下都有寫 LIEN BOT 互動方式~

