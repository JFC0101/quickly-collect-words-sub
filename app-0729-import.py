from flask import Flask, request, render_template, redirect, url_for
from image_processor import process_uploaded_image

app = Flask(__name__)

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
        image, selected_texts, ocr_boxes, file_path = process_uploaded_image(file)
        #最後選取的單字
        print('selected_texts=',selected_texts)
        return redirect(url_for('index', image_url=file_path))

if __name__ == '__main__':
    app.run()