
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from google.cloud import vision
from google.cloud.vision_v1 import types
from PIL import ExifTags
import re
from ultralytics import YOLO

# 加載訓練好的模型
inference_model = YOLO('hilight_model.pt')

#接收上傳的文件，處理圖像，保存處理後的圖像，並返回文件路徑
#合併process_uploaded_image與process_image，保留process_uploaded_image名稱和process_image的內容
def process_uploaded_image_yolo(file):

    #打開圖像文件，調整方向
    image = cv2.imread(file)
    image = correct_image_orientation(image)
    # 進行推理
    results = inference_model(image)
    
    #對圖像進行編碼，然後使用Google Cloud Vision API進行OCR處理
    _, img_encoded = cv2.imencode('.jpg', image)
    ocr_results, ocr_boxes = call_google_ocr_api(img_encoded.tobytes())

    if ocr_results:
        ocr_results = ocr_results[1:]

    # 將 YOLO 結果轉換為 yellow_boxes 矩行框座標格式
    yellow_boxes = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x = int(x1)
            y = int(y1)
            w = int(x2 - x1)
            h = int(y2 - y1)
            yellow_boxes.append((x, y, w, h))
 
    #依Y座標、X座標小到大的順序排列
    yellow_boxes = sorted(yellow_boxes, key=lambda b: (b[1], b[0]))     
 
    #合併yellow_box矩形框
    merged_yellow_boxes = merge_yellow_boxes(yellow_boxes)
  
    #在圖像上繪製矩形框，並處理每個框內的文字    
    selected_texts = []
    for box in merged_yellow_boxes:
        x, y, w, h = box
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
        selected_texts.extend(process_text_in_box(ocr_results, box, image))

    selected_texts = process_selected_texts(selected_texts)
    file_path = save_processed_image(image)        

    return image, selected_texts, ocr_boxes, file_path
#根據EXIF數據調整圖像的方向 
def correct_image_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())

        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

#用Google Cloud Vision API來進行文字檢測 
#Monnday 增加 ocr_boxes，並在使用call_google_ocr_api()的地方設定 output 有 ocr_boxes
def call_google_ocr_api(image):
    client = vision.ImageAnnotatorClient()
    image = types.Image(content=image)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    ocr_boxes = []

    for i, text in enumerate(texts):
        if i == 0:
            continue  # 跳過第一個大框框
        vertices = ([(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices])
        x_min = min(vertex[0] for vertex in vertices)
        y_min = min(vertex[1] for vertex in vertices)
        x_max = max(vertex[0] for vertex in vertices)
        y_max = max(vertex[1] for vertex in vertices)
        ocr_boxes.append((x_min, y_min, x_max, y_max, text.description))

    return texts, ocr_boxes

#文字框與黃色框如果重疊，就將文字添加到selected_texts
def process_text_in_box(ocr_results, yellow_box, image):
    selected_texts = []
    for text in ocr_results:
        min_x = min(vertex.x for vertex in text.bounding_poly.vertices)
        max_x = max(vertex.x for vertex in text.bounding_poly.vertices)
        min_y = min(vertex.y for vertex in text.bounding_poly.vertices)
        max_y = max(vertex.y for vertex in text.bounding_poly.vertices)
        text_box = (min_x, min_y, max_x - min_x, max_y - min_y)

        if check_overlap_box2text(yellow_box, text_box):
            selected_texts.append(text.description)
            cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 1)
            cv2.putText(image, text.description, (min_x, min_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)   
    return selected_texts

#檢查黃色框和文字框是否重疊(黃色框x軸方向重疊1/2以上，Y軸方向重疊1/3以上，視為重疊)
def check_overlap_box2text(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    if h1 / h2 < 0.5:
        y1 = y1 - h2
        h1 = h2  
    overlap_w = min(x1 + w1, x2 + w2) - max(x1, x2)
    overlap_h = min(y1 + h1, y2 + h2) - max(y1, y2)
    if overlap_w > 0 and overlap_h > 0:
        return overlap_w >= w2 / 2 and overlap_h >= h2 / 3
    return False

#合併所有重疊的黃色框
def merge_yellow_boxes(yellow_boxes):
    merged_yellow_boxes = []
    while yellow_boxes:
        box = yellow_boxes.pop(0)
        merged = False
        for i in range(len(merged_yellow_boxes)):
            if check_overlap_box2box(box, merged_yellow_boxes[i]):
                merged_yellow_boxes[i] = merge_boxes(box, merged_yellow_boxes[i])
                merged = True
                break
        if not merged:
            merged_yellow_boxes.append(box)
    return merged_yellow_boxes

#檢查兩個黃色框是否重疊(h相似、y軸方向重疊且X軸距離40像素內，視為重疊)
def check_overlap_box2box(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    overlap_w = min(x1 + w1, x2 + w2) - max(x1, x2)
    overlap_h = min(y1 + h1, y2 + h2) - max(y1, y2)
    similar_h = True if min(h1, h2) / max(h1, h2) >= 0.5 else False
    return overlap_w > -40 and overlap_h > 0 and similar_h

#合併兩個重疊的矩形框
def merge_boxes(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    new_x = min(x1, x2)
    new_y = min(y1, y2)
    new_w = max(x1 + w1, x2 + w2) - new_x
    new_h = max(y1 + h1, y2 + h2) - new_y
    return (new_x, new_y, new_w, new_h)

#去除selected_texts中，重複和無效單字，並按字母順序排序
def process_selected_texts(selected_texts):
    processed_texts = []
    seen = set()
    
    for text in selected_texts:
        # 分割文字為單詞
        words = re.findall(r'\b\w+\b', text)
        
        for word in words:
            # 檢查是否為純數字或特殊符號
            if word.isdigit() or not re.search(r'[a-zA-Z]', word):
                continue
            
            # 轉換為小寫以避免大小寫導致的重複
            word_lower = word.lower()
            
            # 如果單字沒有出現過，則添加到結果中
            if word_lower not in seen:
                seen.add(word_lower)
                processed_texts.append(word)
    # 按字母順序排序
    #processed_texts.sort(key=str.lower)
    return processed_texts

#將處理後的圖像保存為 JPEG 文件。
def save_processed_image(image):
    is_success, buffer = cv2.imencode('.jpg', image)
    io_buf = BytesIO(buffer)
    #固定圖檔檔名如下
    file_path = 'static/uploads/processed_image.jpg'
    with open(file_path, 'wb') as f:
        f.write(io_buf.getbuffer())
    return file_path