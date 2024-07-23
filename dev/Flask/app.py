#比較複雜的版本，包含可以點新增單字，就把 gemini 查到的單字內容insert into資料庫
from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime, timedelta


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
def fetch_all_words(start_date=None, end_date=None, difficulties=None):
    if start_date is None or end_date is None:
        # Default filtering
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if difficulties is None:
        difficulties = [1, 2, 3]

    try:
        conn = sqlite3.connect('word.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM word
            WHERE created_at BETWEEN ? AND ?
            AND difficulty IN (?, ?, ?)
        """, (start_date, end_date, *difficulties))
        words = cursor.fetchall()
        conn.close()
        print(f"Fetched words: {words}")  # Debug statement

        return words
    
    except Exception as e:
        print(f"Error: {e}")
        words = []

def fetch_word_details(word):
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("SELECT  * FROM word WHERE word=?", (word,))
    word_details = cursor.fetchone()
    conn.close()
    return word_details


# Function to fetch filtered words from the database
def fetch_filtered_words(start_date, end_date, difficulties):
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()

    #一个总是为真的条件，方便动态添加其他筛选条件
    query = "SELECT * FROM word WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND created_at >= ?"
        params.append(start_date)
    if end_date:
        query += " AND created_at <= ?"
        params.append(end_date)
    if difficulties:
        query += " AND difficulty IN ({})".format(','.join(['?'] * len(difficulties)))
        params.extend(difficulties)
    
    #将 params 作为参数传递给 SQL 查询
    cursor.execute(query, params)
    words = cursor.fetchall()
    conn.close()
    return words


@app.route('/filter', methods=['POST'])
def filter_words():

    #从请求体中获取 JSON 数据，并提取 startDate、endDate 和 difficulties
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    difficulties = data.get('difficulties', [])

    words = fetch_filtered_words(start_date, end_date, difficulties)
    
    # 打印返回的数据
    print(f"Filtered words: {words}")

    #处理查询结果，将每个单词的信息格式化为 JSON 对象，包括 word、pronunciation、definition、difficulty、difficulty_text 和 type
    response = {'words': [
        {
            'word': word[1],
            'pronunciation': word[2],
            'definition': word[4],
            'difficulty': word[5],
            'difficulty_text': '困難' if word[5] == 1 else ('中等' if word[5] == 2 else '簡單'),
            'type': word[3]
        } for word in words
    ]}
    
    return jsonify(response)




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


@app.route('/', methods=['GET', 'POST'])
def index():
    new_words = request.args.get('new_words', '').split(',')
    word = None  # Initialize word to None
    word_in_db = False

    # 设置默认的筛选条件：60天前到当前日期的时间范围，以及所有难度级别（1, 2, 3）。
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d 00:00:00')
    end_date = datetime.now().strftime('%Y-%m-%d 23:59:59')
    difficulties = [1, 2, 3]
                                
    if request.method == 'POST':  # Handle POST request
        if 'word' in request.form:
            # 当请求中包含 'word' 表单字段时，执行单词搜索逻辑
            word_to_search = request.form.get('word')
            if not word_to_search or not all(char.isalpha() or char == ',' for char in word_to_search):
                error = "請輸入有效的英文字符或逗號。"
                #return render_template('index.html', words=fetch_all_words(), error=error)

            try:
                # 连接到数据库，并查询单词详情。
                conn = sqlite3.connect('word.db')
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM word WHERE word=?", (word_to_search,))
                word_details = cursor.fetchone()
                conn.close()

                if word_details:
                    word = {
                        'word': word_details[1],
                        'pronunciation': word_details[2],
                        'definition': word_details[3],
                        'example': word_details[4],
                        'difficulty': word_details[5]
                    }
                    word_in_db = True
                else:
                    # 如果没有在数据库中找到单词，则调用 `get_word_details` 获取单词的详细信息。
                    word = get_word_details(word_to_search)
                    
                    if word:
                        word_in_db = False

            except Exception as e:
                print(f"Error: {e}")

            # 处理 GET 请求，渲染模板并返回默认单词列表和其他变量。
            #return render_template('index.html', words=words, word=word, word_in_db=word_in_db)
    words = fetch_all_words(start_date=start_date, end_date=end_date, difficulties=difficulties)
    return render_template('index.html', words=words, word=word, word_in_db=word_in_db, new_words=new_words, start_date=start_date, end_date=end_date, difficulties=difficulties)


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
            words = ['show', 'tomorrow','maybe','explore']
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
