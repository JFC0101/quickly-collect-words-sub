#比較複雜的版本，包含可以點新增單字，就把 gemini 查到的單字內容insert into資料庫
from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import google.generativeai as genai
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set up Google Gemini API
api_key = os.getenv('API_KEY')
genai.configure(api_key=api_key)

# Define generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Function to get word details from Gemini API
def get_word_details(word):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=f'input:{word},output ex:Word: explore\nPronunciation: /ɪkˈsplɔːr/\nDefinition: 探索, 調查 \nExample: The best way to explore the countryside is on foot.'
    )

    response = model.generate_content({word})
    print( response)
    if response:
        response_text = response.text
        
        # Find word
        start_index = response_text.find('Word:') + len('Word:')
        end_index = response_text.find('\n', start_index)
        word = response_text[start_index:end_index].strip()
        
        # Find pronunciation
        start_index = response_text.find('Pronunciation:') + len('Pronunciation:')
        end_index = response_text.find('\n', start_index)
        pronunciation = response_text[start_index:end_index].strip()
        
        # Find definition
        start_index = response_text.find('Definition:') + len('Definition:')
        end_index = response_text.find('Example:', start_index)
        definition = response_text[start_index:end_index].strip()
        
        # Find example
        start_index = response_text.find('Example:') + len('Example:')
        example = response_text[start_index:].strip()
        return {
            'word': word,
            'pronunciation': pronunciation,
            'definition': definition,
            'example': example
        }
    return None

# Function to insert word details into the database
def insert_word_details(word, pronunciation, definition, example):
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO word (word, pronunciation, definition, example) VALUES (?, ?, ?, ?)", (word, pronunciation, definition, example))
    conn.commit()
    conn.close()

# Function to fetch all words from the database
def fetch_all_words():
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word, pronunciation, definition, example FROM word ORDER BY id DESC")
    words = cursor.fetchall()
    conn.close()
    return words

# Flask routes

# Home page, display all words and search functionality
@app.route('/', methods=['GET', 'POST'])
def index():
    word = None  # Initialize word to None
    word_in_db = False

    
    if request.method == 'POST':  #處理 POST 請求
        word_to_search = request.form['word']  #從表單中獲取單字:

        try:
            conn = sqlite3.connect('word.db')
            cursor = conn.cursor()
            cursor.execute("SELECT word, pronunciation, definition, example FROM word WHERE word=?", (word_to_search,)) #連接資料庫並查詢該單字是否存在於資料庫中
            word_details = cursor.fetchone()
 
            if word_details:  #如果資料庫中找到該單字，將其詳細信息存儲在 word 變數中
                word = {
                    'word': word_details[0],
                    'pronunciation': word_details[1],
                    'definition': word_details[2],
                    'example': word_details[3]
                }
                word_in_db = True
            else:
                word = get_word_details(word_to_search)  # Use get_word_details function here 如果資料庫中未找到該單字，使用 get_word_details 函數從 Google Gemini API 獲取單字的詳細信息。

                #if word: #如果 API 成功返回詳細信息，將其插入到資料庫中。
                    
                    #insert_word_details(word['word'], word['pronunciation'], word['definition'], word['example'])

            conn.close()
        except Exception as e:
            print(f"Error: {e}")

        return render_template('index.html', words=fetch_all_words(), word=word, word_in_db=word_in_db) #渲染模板 index.html，並將所有單字（從資料庫中獲取）和查詢結果（如果有）傳遞到前端。

    return render_template('index.html', words=fetch_all_words(), word=word, word_in_db=word_in_db)

# Add a new word to the database
@app.route('/add_word', methods=['POST'])
def add_word():
    word = request.form['word']
    word_details = get_word_details(word)  # 呼叫 get_word_details 函數從 Google Gemini API 獲取單字詳細信息
    if word_details:
        insert_word_details(word_details['word'], word_details['pronunciation'], word_details['definition'], word_details['example'])  # 將獲取到的單字詳細信息插入資料庫
    return redirect(url_for('index'))  # 重定向到首頁

# Route to upload page
@app.route('/upload')
def upload():
    return render_template('upload.html')


@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return jsonify({'success': 'File uploaded successfully', 'filename': file.filename})
    return jsonify({'error': 'File upload failed'})


if __name__ == '__main__':
    app.run(debug=True)
