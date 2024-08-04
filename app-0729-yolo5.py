import cv2
import torch
from ultralytics import YOLO

# 加載訓練好的模型
inference_model = YOLO('D:/pj/try3/hilight_model.pt')

# 讀取測試圖像
test_image_path = 'D:/pj/try2/457762.jpg'
image = cv2.imread(test_image_path)

# 進行推理
results = inference_model(image)

# 在圖像上繪製結果
for r in results:
    boxes = r.boxes
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

# 顯示結果
cv2.imshow('Result', image)
cv2.waitKey(0)
cv2.destroyAllWindows()