from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import cv2
import numpy as np
from google.cloud import vision
from google.cloud.vision_v1 import types
from io import BytesIO
from PIL import Image, ExifTags

app = Flask(__name__)

# 設置環境變數以使用本地 JSON 憑證檔案
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'c:/pj/google API 金鑰.json'

def call_google_ocr_api(image):
    client = vision.ImageAnnotatorClient()
    image = types.Image(content=image)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts

def check_overlap_box2text(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    #如果是細螢光底線將色塊框高度比照字框高度加高，Y座標上移    
    if h1 / h2 < 0.5:
        y1 = y1 - h2
        h1 = h2  
    overlap_w = min(x1 + w1, x2 + w2) - max(x1, x2)
    overlap_h = min(y1 + h1, y2 + h2) - max(y1, y2)
    if overlap_w > 0 and overlap_h > 0:
        return overlap_w >= w2 / 2 and overlap_h >= h2 / 3
    return False

def check_overlap_box2box(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    overlap_w = min(x1 + w1, x2 + w2) - max(x1, x2)
    overlap_h = min(y1 + h1, y2 + h2) - max(y1, y2)
    #避免高度差異太大之大小框合併
    similar_h = True if min(h1, h2) / max(h1, h2) >= 0.5 else False
    return overlap_w > -40 and overlap_h > 0 and similar_h

def merge_boxes(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    new_x = min(x1, x2)
    new_y = min(y1, y2)
    new_w = max(x1 + w1, x2 + w2) - new_x
    new_h = max(y1 + h1, y2 + h2) - new_y
    return (new_x, new_y, new_w, new_h)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        image = Image.open(file)
        image = correct_image_orientation(image)
        image = np.array(image)    
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#        lower_yellow = np.array([25, 60, 100])
#        upper_yellow = np.array([40, 255, 255])
        #去黑白，其餘顏色全取
        lower_yellow = np.array([0, 80, 150])
        upper_yellow = np.array([180, 255, 255])
        mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        _, img_encoded = cv2.imencode('.jpg', image)
        ocr_results = call_google_ocr_api(img_encoded.tobytes())

        if ocr_results:
            ocr_results = ocr_results[1:]

        selected_texts = []
        yellow_boxes = [cv2.boundingRect(contour) for contour in contours]

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

        for box in merged_yellow_boxes:
            x, y, w, h = box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
            for text in ocr_results:
                vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
                min_x = min(vertex.x for vertex in text.bounding_poly.vertices)
                max_x = max(vertex.x for vertex in text.bounding_poly.vertices)
                min_y = min(vertex.y for vertex in text.bounding_poly.vertices)
                max_y = max(vertex.y for vertex in text.bounding_poly.vertices)
                text_box = (min_x, min_y, max_x - min_x, max_y - min_y)
                yellow_box = (x, y, w, h)

                if check_overlap_box2text(yellow_box, text_box):
                    selected_texts.append(text.description)
                    cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 1)
                    cv2.putText(image, text.description, (min_x, min_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

        is_success, buffer = cv2.imencode('.jpg', image)
        io_buf = BytesIO(buffer)
        file_path = 'static/processed_image.jpg'
        with open(file_path, 'wb') as f:
            f.write(io_buf.getbuffer())

        return redirect(url_for('index', image_url=file_path))

if __name__ == '__main__':
    app.run()
