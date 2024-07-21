#比較複雜的版本，包含可以點新增單字，就把 gemini 查到的單字內容insert into資料庫
from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import google.generativeai as genai
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = 'static/uploads'

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
    print(response)
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
    cursor.execute("INSERT INTO word (word, pronunciation, definition, example, difficulty) VALUES (?, ?, ?, ?, ?)", (word, pronunciation, definition, example, 1))
    conn.commit()
    conn.close()

# Function to fetch all words from the database
def fetch_all_words():
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM word ORDER BY id DESC")
    words = cursor.fetchall()
    conn.close()
    return words

def fetch_word_details(word):
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("SELECT  * FROM word WHERE word=?", (word,))
    word_details = cursor.fetchone()
    conn.close()
    return word_details



@app.route('/update_difficulty', methods=['POST'])
def update_difficulty():
    data = request.get_json()
    word = data.get('word')
    difficulty = data.get('difficulty')


    # 在這裡處理更新資料庫的動作，例如：
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE word SET difficulty=? WHERE word=?", (difficulty, word))
    conn.commit()
    conn.close()

    return jsonify({'message': '難易度已更新'}), 200





# Home page, display all words and search functionality
@app.route('/', methods=['GET', 'POST'])
def index():
    new_words = request.args.get('new_words', '').split(',')
    ##error = None (改由前端判斷與給 error)
    word = None  # Initialize word to None
    word_in_db = False

    
    if request.method == 'POST':  #處理 POST 請求

        word_to_search = request.form.get('word')
        # 仅在前端验证失效时，进行后端验证
        if not word_to_search or not all(char.isalpha() or char == ',' for char in word_to_search):
                    error = "請輸入有效的英文字符或逗號。"
                    ##return render_template('index.html', words=fetch_all_words(), error=error) (改由前端判斷與給 error，如果要前端能接收後端的 Error 要重新寫 index.heml 內有接收的位置)


        try:
            conn = sqlite3.connect('word.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM word WHERE word=?", (word_to_search,)) #連接資料庫並查詢該單字是否存在於資料庫中
            word_details = cursor.fetchone()
            conn.close()

            if word_details:  #如果資料庫中找到該單字，將其詳細信息存儲在 word 變數中
                word = {
                    'word': word_details[1],
                    'pronunciation': word_details[2],
                    'definition': word_details[3],
                    'example': word_details[4]
                }
                word_in_db = True
            else:
                word = get_word_details(word_to_search)  # Use get_word_details function here 如果資料庫中未找到該單字，使用 get_word_details 函數從 Google Gemini API 獲取單字的詳細信息。

                if word: 
                    word_in_db = False
            
        except Exception as e:
            print(f"Error: {e}")

        # 这里不传递 error 参数
        return render_template('index.html', words=fetch_all_words(), word=word, word_in_db=word_in_db) #渲染模板 index.html，並將所有單字（從資料庫中獲取）和查詢結果（如果有）傳遞到前端。

    return render_template('index.html', words=fetch_all_words(), word=word, word_in_db=word_in_db, new_words=new_words) #

# Add a new word to the database
@app.route('/add_word', methods=['POST'])
def add_word():
    word = request.form['word']
    word_details = get_word_details(word)  # 呼叫 get_word_details 函數從 Google Gemini API 獲取單字詳細信息
    if word_details:
        insert_word_details(word_details['word'], word_details['pronunciation'], word_details['definition'], word_details['example'])  # 將獲取到的單字詳細信息插入資料庫
    return redirect(url_for('index'))  # 重定向到首頁



# 照相得到的新的單字 Add a new word to the database
@app.route('/process_words', methods=['POST'])
def process_words():
    words = request.json.get('words', [])
    processed_words = []

    try:
        conn = sqlite3.connect('word.db')
        cursor = conn.cursor()

        for word_to_search in words:
            cursor.execute("SELECT * FROM word WHERE word=?", (word_to_search,))
            word_details = cursor.fetchone()

            if word_details:
                processed_words.append(word_to_search)
            else:
                word = get_word_details(word_to_search)
                if word:
                    cursor.execute("INSERT INTO word (word, pronunciation, definition, example, difficulty) VALUES (?, ?, ?, ?, ?)",
                                   (word['word'], word['pronunciation'], word['definition'], word['example'], 3))
                    conn.commit()
                    processed_words.append(word_to_search)

        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error processing words'}), 500

    # 返回 JSON 响应
    return jsonify({'new_words': processed_words, 'toast': '新增成功'})













@app.route('/word')
def word_detail():
    word_name = request.args.get('word')
    words = fetch_all_words()
    word_index = next((i for i, w in enumerate(words) if w[1] == word_name), None)
    if word_index is None:
        return "Word not found", 404

    word = words[word_index]
    prev_word = words[word_index - 1] if word_index > 0 else None
    next_word = words[word_index + 1] if word_index < len(words) - 1 else None

    return render_template('word.html', word=word, prev_word=prev_word, next_word=next_word)


@app.route('/upload_capture', methods=['POST'])
def upload_capture():
    # 保存捕获的 JPEG 图片
    file = request.files.get('file')
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'capture.jpg'))
        return jsonify({'success': True})
    return jsonify({'error': 'No file uploaded'})


#处理文件上传请求，保存上传的文件到指定的文件夹中，并返回上传状态的 JSON 响应
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


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')

        if uploaded_file:
            # Process uploaded file if needed
            # Example: recognizing words from the image
            words = ['show', 'choose','maybe','explore']
            image_name = uploaded_file.filename
            uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

            # Redirect to word preview page with image and words data
            return jsonify({'image': image_name, 'words': words})

    return render_template('upload.html')




@app.route('/word-preview')
def word_preview():
    image_name = request.args.get('image')
    words = request.args.get('words').split(',')
    return render_template('word-preview.html', image_name=image_name, words=words)





# Route to about page
@app.route('/about')
def about():
    return render_template('about.html')




if __name__ == '__main__':
    app.run(debug=True)
