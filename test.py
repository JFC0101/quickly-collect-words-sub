from flask import Flask, request, jsonify, render_template
from google.cloud import vision
import io
import os

app = Flask(__name__)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'd:/pj/google API 金鑰.json'
client = vision.ImageAnnotatorClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    image_file = request.files['image']
    image = vision.Image(content=image_file.read())

    # Perform text detection on the image file
    response = client.text_detection(image=image)
    texts = response.text_annofrom flask import Flask, request, jsonify
import cv2
import numpy as np
from google.cloud import vision
from google.cloud.vision_v1 import types
import base64

app = Flask(__name__)
client = vision.ImageAnnotatorClient()

@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.json
    image_data = base64.b64decode(data['image'])
    np_image = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    # 偵測黃色高亮區域
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    yellow_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        yellow_boxes.append((x, y, x+w, y+h))

    # OCR偵測
    _, encoded_image = cv2.imencode('.png', image)
    content = encoded_image.tobytes()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    word_boxes = []
    for text in texts[1:]:
        vertices = text.bounding_poly.vertices
        word_boxes.append({
            'text': text.description,
            'bounds': [(vertex.x, vertex.y) for vertex in vertices]
        })

    selected_words = []
    for word_box in word_boxes:
        word_coords = np.array(word_box['bounds'])
        word_x1, word_y1 = np.min(word_coords, axis=0)
        word_x2, word_y2 = np.max(word_coords, axis=0)
        word_rect = (word_x1, word_y1, word_x2, word_y2)

        for yellow_box in yellow_boxes:
            overlap_area = compute_overlap_area(word_rect, yellow_box)
            word_area = (word_x2 - word_x1) * (word_y2 - word_y1)
            if overlap_area / word_area > 0.5:
                selected_words.append(word_box['text'])
                break

    return jsonify({'selected_words': selected_words})

def compute_overlap_area(rect1, rect2):
    x1 = max(rect1[0], rect2[0])
    y1 = max(rect1[1], rect2[1])
    x2 = min(rect1[2], rect2[2])
    y2 = min(rect1[3], rect2[3])
    overlap_width = max(0, x2 - x1)
    overlap_height = max(0, y2 - y1)
    return overlap_width * overlap_height

if __name__ == '__main__':
    app.run(debug=True)
tations

    # Extract bounding boxes of detected texts
    detected_words = []
    for text in texts[1:]:  # First result is the entire text block
        vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        word_info = {
            'word': text.description,
            'bounds': vertices
        }
        detected_words.append(word_info)

    return jsonify(detected_words)

@app.route('/highlight', methods=['POST'])
def highlight_text():
    data = request.json
    selected_bounds = data['bounds']
    detected_words = data['detected_words']

    highlighted_words = []
    for word in detected_words:
        word_bounds = word['bounds']
        overlap_width = min(word_bounds[2][0], selected_bounds[2][0]) - max(word_bounds[0][0], selected_bounds[0][0])
        word_width = word_bounds[2][0] - word_bounds[0][0]
        if overlap_width >= word_width / 2:
            highlighted_words.append(word['word'])

    return jsonify(highlighted_words)

if __name__ == '__main__':
    app.run()





test