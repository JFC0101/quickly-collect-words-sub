from flask import Flask, request, render_template, redirect, url_for, jsonify, session, flash, abort
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime, timedelta
import re
from image_processor_opencv import process_uploaded_image
from werkzeug.utils import secure_filename
from image_processor_yolo5 import process_uploaded_image_yolo
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from linebot_message_handlers_module import handle_option_1, handle_option_2, show_menu


#LINE
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *


app = Flask(__name__)

app.config['SECRET_KEY'] = 'aiprojectsecretkey'
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储会话数据
Session(app)

#LINEBOTAPI 上面的碼
LINE_CHANNEL_ACCESS_TOKEN = 'o3QtSVE0H6Vqy2cDwyluf56pj90RY9ODCqrj1zVN0dHIhsM1fnMZG+wsVXBbhtDBj97jbI/k1wSdAvu56q/OmnQysfB94SWxZWaSaoektLmpIiFim2KvQs2axOQ4KB8j7hnBbHUfNlZzGLBA1enqFQdB04t89/1O/w1cDnyilFU=' #你的Channel access token
LINE_CHANNEL_SECRET = '74422e40d649aee03dc6a72d2a335ee5' #你的Channel secret
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

#設定圖片上傳後要存到哪個資料夾
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection(database='app_words.db'):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row # row['column_name']允許您使用列名稱存取列，這可以使您的程式碼更具可讀性和可維護性。
    return conn



#-------------------#
# 登入路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        
        user = check_user_credentials(account, password)
        if user:
            session['user_id'] = user['id']
            session['account'] = user['account']  #存储 account 到会话中
            return redirect(url_for('index'))
        else:
            flash('登入失敗，請檢查帳號和密碼是否正確。', 'error')
    
    return render_template('login.html')



#检查用户名和密码是否与存储的凭证匹配。
def check_user_credentials(account, password):
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()

    # 尝试获取用户信息
    cursor.execute("SELECT user_id, account, password FROM user WHERE account = ?", (account,))
    user_record = cursor.fetchone()

    conn.close()

    if user_record:
        user_id, account, hashed_password = user_record
        # 验证密码是否正确
        if check_password_hash(hashed_password, password):
            return {'id': user_id, 'account': account}
    return None
#----------------------#
# 登出路由
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('account', None)  # 清除会话中的 account
    return redirect(url_for('login'))


#---------------------#
# 註冊路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        account = request.form['account'].lower()        
        password = request.form['password']
        #sername = request.form['username']
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO user (account, password, username) VALUES (?, ?, ?)',
                         (account, hashed_password, account))
            conn.commit()
            user = conn.execute('SELECT * FROM user WHERE account = ?', (account,)).fetchone()
            if user:
                session['user_id'] = user['user_id']
                session['account'] = user['account']
                return redirect(url_for('index'))
            else:
                flash('註冊失敗，無法找到用戶資料。', 'error')
                print("Failed to fetch user data after registration")
        except sqlite3.IntegrityError:
            # 捕捉重複帳號異常並顯示錯誤訊息
            flash('註冊失敗：帳號已存在。', 'error')
            print("Account already exists.")        
        except sqlite3.Error as e:
            flash(f'註冊失敗：{e}', 'error')
            print(f"Error during registration: {e}")
        finally:
            conn.close()
    return render_template('register.html')

#---------------------# Gemini api 的部分
# Set up Google Gemini API
api_key = os.getenv('API_KEY')
genai.configure(api_key=api_key)

# Define generation configuration
generation_config = {
    "temperature": 1, 
    "top_p": 0.95,
    "top_k": 64, #當 TopK=1 (A)，代表每一次都是選擇最大可能性的那個字
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# 只要呼叫這個 Function，就是去問 Gemini API 單字_details
def get_word_details(word):
    system_instruction = f'Input: {word}(original form of word)\nExample Output:\n\nword: explore\npos: verb\npronunciation: KK [ɪkˈsplɔːr]\ndefinition_zh: 探測, 勘查, 探索, 研究\ndefinition_en: to search a place and discover things about it; to examine or discuss a subject in detail.\nsynonyms_en: investigate, examine, inquire into, inspect, look into, probe, research\nsynonyms_zh: 調查, 研究, 查明, 檢查, 探討, 探究, 審查\nexample_en: The explorers set out to explore the unknown territory.\nexample_zh: 探索者們出發去探索未知的領土。\nprefixes: ex- / out, from 向外\nroot: plore / to search 探索\nsuffixes: \n (All zh places use traditional Chinese description.) '
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction
    )

    response = model.generate_content({word})
    print('成功呼叫了gemini api 取得單字意思')
    
    if response:
        response_text = response.text
        
        def clean_text(text):  #把一些多餘的字刪除
            return re.sub(r'[\*\*/]', '', text).strip()

        def extract_field(field_name):
            start_index = response_text.find(f'{field_name}:') + len(f'{field_name}:')
            end_index = response_text.find('\n', start_index)
            return clean_text(response_text[start_index:end_index])

        word = extract_field('word')
        pos = extract_field('pos')
        pronunciation = extract_field('pronunciation')
        definition_en = extract_field('definition_en')
        definition_zh = extract_field('definition_zh')
        synonyms_en = extract_field('synonyms_en')
        synonyms_zh = extract_field('synonyms_zh')
        example_en = extract_field('example_en')
        example_zh = extract_field('example_zh')
        prefixes = extract_field('prefixes')
        roots = extract_field('roots')
        suffixes = extract_field('suffixes')

        return {
            'word': word,
            'pos': pos,
            'pronunciation': pronunciation,
            'definition_en': definition_en,
            'definition_zh': definition_zh,
            'synonyms_en': synonyms_en,
            'synonyms_zh': synonyms_zh,
            'example_en': example_en,
            'example_zh': example_zh,
            'prefixes': prefixes,
            'roots': roots,
            'suffixes': suffixes
        }
    return None

#------------------------#
#這個 fetch_filtered_words() function 是去資料庫查找符合篩選條件資格的單字，所以 index() 或 filter() function 都有呼叫這個函數
#原本是預計使用 fetch_all-words()，但因為做了篩選功能，所以每次抓資料庫單字時，都是依據篩選結果(start_date, end_date, difficulties)去查找單字
def fetch_filtered_words(start_date, end_date, difficulties, user_id):
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()
    query = """
    SELECT w.*, uw.difficulty_id
    FROM user_words uw
    JOIN words w ON uw.word_id = w.word_id
    WHERE uw.create_time BETWEEN ? AND ? 
    AND uw.difficulty_id IN ({seq})
    AND uw.user_id = ?
    ORDER BY uw.create_time DESC
    """.format(seq=','.join(['?']*len(difficulties)))
    cursor.execute(query, (start_date, end_date, *difficulties, user_id))
    words = cursor.fetchall()
    conn.close()
    return words


#------------------------#
#当页面加载时，首先通过 html 中的 applyDefaultFilter 函數由前端送預設的篩選內容給後端，後端去找符合篩選結果的單字 (fetch_filtered_words) 包裝成 json 給前端
@app.route('/', methods=['GET', 'POST'])
def index():
        #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲

    if 'user_id' in session:
        user_id = session['user_id']
                
        #从 POST 请求的 JSON 数据中提取 startDate、endDate、difficulties 和 newWords。
        if request.method == 'POST':
            data = request.get_json()
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            difficulties = data.get('difficulties')

            filtered_words = fetch_filtered_words(start_date, end_date, difficulties, user_id)
            response = {
                'words': [{
                    'word_id':word[0],
                    'word': word[1],
                    'pos': word[2],
                    'pronunciation': word[3],
                    'definition_zh': word[5],  #zh
                    'example_en': word[8], #en
                    'difficulty_id': word[13],
                } for word in filtered_words]
            }
            return jsonify(response)
        else:
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d') + 'T00:00:00'
            end_date = datetime.now().strftime('%Y-%m-%d') + 'T23:59:59'
            difficulties = [1, 2, 3]

            filtered_words = fetch_filtered_words(start_date, end_date, difficulties, user_id)
            return render_template('index.html', words=filtered_words, start_date=start_date, end_date=end_date, difficulties=difficulties)
    
    return redirect(url_for('login'))



#---------------------#
# 前端页面获取用户设置的筛选条件，发送这些条件到服务器(後端)进行数据过滤，然后更新页面上的词汇列表
@app.route('/filter', methods=['POST'])
def filter_words():
    #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲取
    user_id = session['user_id']    

    #从请求体中获取 JSON 数据，并提取 startDate、endDate 和 difficulties
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    difficulties = data.get('difficulties', [])

    #用fetch_filtered_words() 查找資料庫符合結果的單字們
    words = fetch_filtered_words(start_date, end_date, difficulties, user_id)
    
    # 為了看有沒有運作，所以 print 一下有處理了
    print(f"Filtered words: filter_words() success")

    #处理查询结果，将每个单词的信息格式化为 JSON 对象，包括 word、pronunciation、definition、difficulty、difficulty_text 和 type
    response = {
        'words': [{
                'word_id':word[0],
                'word': word[1],
                'pos': word[2],
                'pronunciation': word[3],
                'definition_zh': word[5],  #zh
                'example_en': word[8], #en
                'difficulty_id': word[13],
        } for word in words]
    }
    
    return jsonify(response)



#------------------------#
#前端輸入文字送出搜尋，如果資料庫找得到，那就給前端資料庫的資料(json)
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    word_to_search = data['word'].lower() #前端給的 word assign 給 word_to_search

    #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲取
    user_id = session['user_id']
    
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()

    # 檢查單字是否存在於 words 表中
    cursor.execute("SELECT * FROM words WHERE word = ?", (word_to_search,))
    word_details = cursor.fetchone()

    if word_details:
        # 單字存在於 words 表中，檢查是否已添加到 user_words 表中
        cursor.execute("""
        SELECT w.*, uw.difficulty_id, uw.query_count, uw.last_query_time
        FROM user_words uw
        JOIN words w ON uw.word_id = w.word_id
        WHERE uw.word_id = ? AND uw.user_id = ?
    """, (word_details[0], user_id))
        user_word_details = cursor.fetchone()
        difficulty_id = user_word_details[-3] if user_word_details else 1  # 如果 user_word_details 為空，設置 difficulty_id 為 1

        if user_word_details:
            # 單字已添加到 user_words 表中，更新 query_count 和 last_query_time
            cursor.execute("""
                UPDATE user_words
                SET query_count = query_count + 1, last_query_time = datetime('now', 'localtime')
                WHERE word_id = ? AND user_id = ?
            """, (word_details[0], user_id))

        conn.commit()
        conn.close()

        return jsonify({'word': {
            'word': word_details[1],
            'pos':word_details[2],
            'pronunciation': word_details[3],
            'definition_zh': word_details[5],
            'example_en': word_details[8],
            'difficulty_id' : difficulty_id  # 抓上面 assign 給 difficulty_id 的值來設置 json 的 difficulty_id
        }, 'word_in_db': user_word_details is not None})
    else:
        conn.close()
        return jsonify({'word': None})

#因為後端說資料庫沒有({'word': None})，前端就呼叫後端這個函數，請後端去問 gemini (get_word_details)，把單字的意思包裝json給前端
@app.route('/get_word_details')
def api_get_word_details():
    word_to_search = request.args.get('word')
    if not word_to_search:
        return jsonify({'error': '沒有指定單詞'}), 400
    try:
        word_details = get_word_details(word_to_search)
        return jsonify(word_details) #將 get_word_details() return 的 dictionary 包裝成 JSON 送到前端
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#前端用戶說要新增這個單字，所以後端就去新增到db，然後把新增的單字內容跟 success 結果給前端
@app.route('/add_word', methods=['POST'])
def add_word():
    data = request.get_json()
    word = data['word']
    #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲取
    user_id = session['user_id']

    
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()
    
    # 先檢查單字是否已存在於 words 表中
    cursor.execute("SELECT * FROM words WHERE word = ?", (word,))
    word_details = cursor.fetchone()

    if not word_details:
       # 單字不存在於 words 表中，直接添加到 words 表中
        cursor.execute("""
            INSERT INTO words (word, pos, pronunciation, definition_en, definition_zh, synonyms_en, synonyms_zh, example_en, example_zh, prefixes, roots, suffixes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['word'], data['pos'], data['pronunciation'], data['definition_en'],
            data['definition_zh'], data['synonyms_en'], data['synonyms_zh'],
            data['example_en'], data['example_zh'], data['prefixes'], data['roots'],
            data['suffixes']
        ))
        conn.commit()
        cursor.execute("SELECT * FROM words WHERE word = ?", (word,))
        word_details = cursor.fetchone()

    word_id = word_details[0]  # 在這裡賦值 word_id

    try:
        # 插入到 user_words 表中
        cursor.execute("""
        INSERT INTO user_words (user_id, word_id, difficulty_id)
        VALUES (?, ?, ?)
        """, (user_id, word_id, 1))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({'error': '數據庫錯誤'}), 500
    finally:
        conn.close()

    # 構建返回的 word_details 字典
    word_details_dict = {
        'word_id': word_details[0],
        'word': word_details[1],
        'pos': word_details[2],
        'pronunciation': word_details[3],
        'definition_en': word_details[4],
        'definition_zh': word_details[5],
        'synonyms_en': word_details[6],
        'synonyms_zh': word_details[7],
        'example_en': word_details[8],
        'example_zh': word_details[9],
        'prefixes': word_details[10],
        'roots': word_details[11],
        'suffixes': word_details[12],
        'difficulty_id' : 1 ,
    }


    return jsonify({'success': '新增成功', 'word_details': word_details_dict})

#------------------------#
    
# 上傳圖片或是照相得到的新的單字，在 word-preview.html 頁面按送出執行會呼叫這個路由進行 process_words() function 來 Add a new word to the database
@app.route('/process_words', methods=['POST'])
def process_words():
    words = request.json.get('words', [])
    #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲取
    user_id = session['user_id']
    processed_words = []

    try:
        conn = sqlite3.connect('app_words.db')
        cursor = conn.cursor()

        for word_to_search in words:
            word_to_search = word_to_search.lower()  # 将单词转换为小写
            print('word_to_search1',word_to_search)
            cursor.execute("SELECT * FROM words WHERE word=?", (word_to_search,))
            word_details = cursor.fetchone()

            if word_details:  #如果單字已存在於 words 表中，直接將單字添加到 user_words 表中。
                word_id = word_details[0]
                cursor.execute("INSERT OR IGNORE INTO user_words (user_id, word_id, difficulty_id) VALUES (?, ?, ?)", #使用 INSERT OR IGNORE 確保不會重複插入相同的單字到 user_words 表中。
                               (user_id, word_id, 1)) #難易度預設為1
                conn.commit()
                processed_words.append(word_to_search)
                toast_message = '新增成功'
                
            else: #如果單字不存在於 words 表中，使用 get_word_details 函數獲取單字詳細信息，並將單字添加到 words 表中，然後再將其添加到 user_words 表中。
                print('word_to_search2',word_to_search)
                word = get_word_details(word_to_search)
                if word:
                    print('word_to_search3',word_to_search)
                    cursor.execute("""
                    INSERT OR IGNORE INTO words (word, pos, pronunciation, definition_en, definition_zh, synonyms_en, synonyms_zh, example_en, example_zh, prefixes, roots, suffixes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        word['word'], word['pos'], word['pronunciation'], word['definition_en'], word['definition_zh'], 
                        word['synonyms_en'], word['synonyms_zh'], word['example_en'], word['example_zh'], 
                        word['prefixes'], word['roots'], word['suffixes']
                    ))
                    conn.commit()
                    cursor.execute("SELECT word_id FROM words WHERE word=?", (word_to_search,))
                    result = cursor.fetchone()
                    if result:  # 確保 result 不是 None
                        word_id = result[0]
                        cursor.execute("INSERT INTO user_words (user_id, word_id, difficulty_id) VALUES (?, ?, ?)",
                                       (user_id, word_id, 1))  # 難易度預設為1
                        conn.commit()
                        processed_words.append(word_to_search)
                        toast_message = '新增成功'
                    else:
                        print(f"Error: Could not find word '{word_to_search}' after insertion")
                        toast_message = '連線不穩，請再試一次'
                        return jsonify({'error': f"Could not find word '{word_to_search}' after insertion"}), 500
                    
                    
                else:
                    print(f"Error: Could not fetch details for word '{word_to_search}'")
                    return jsonify({'error': f"Could not fetch details for word '{word_to_search}'"}), 500

        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error processing words'}), 500

    # 返回JSON响应给 word-preview.html 的 js
    new_words_query = ",".join(processed_words)
    return redirect(f'/?new_words={new_words_query}&toast={toast_message}')


#------------------------#
#处理文件上传请求，保存上传的文件到指定的文件夹中
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return jsonify({
            'success': 'File uploaded and processed successfully',
            'filename': filename,
        })

    return jsonify({'error': 'File upload failed'})


#將處理過的圖片， json 保存 image 路徑、selected_texts, ocr_boxes 傳給前端，並將 json 存到 session 中給 word-preview.html 使用
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' in session:


        if request.method == 'POST':
            #這個應該是把處理過的圖片呼叫出來
            uploaded_file = request.files.get('file')
            model = request.form.get('model')

            if uploaded_file:
                # 保存文件到指定目录
                filename = secure_filename(uploaded_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(filepath)

                # 调用process_uploaded_image函数处理上传的图片         
                if model == 'YOLOv5':
                    image, selected_texts, ocr_boxes, file_path = process_uploaded_image_yolo(filepath)
                elif model == 'openCV':
                    image, selected_texts, ocr_boxes, file_path = process_uploaded_image(filepath)
                else:
                    return jsonify({"error": "Unknown model selected"}), 400

                processed_image_path = 'processed_image.jpg'

                # 返回处理后的图片和单词列表
                return jsonify({
                    'image': processed_image_path,
                    'words': selected_texts,
                    'ocr_boxes': ocr_boxes
                })#upload.js 接收了 json 內容就會將畫面導到 word-preview 頁面

        #如果不是 post 就是單純的打開 upload 畫面
        return render_template('upload.html')

    return redirect(url_for('login'))

#進入 word-preview.html
@app.route('/word-preview')
def word_preview():
    if 'user_id' in session:
        return render_template('word-preview.html')
        
    return redirect(url_for('login'))


#------------------------#
# 在 word.html 裡面點擊難易度 label 呼叫後端進行 update_difficulty() function 運行，更新難易度
@app.route('/update_difficulty', methods=['POST'])
def update_difficulty():
    #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲取
    user_id = session['user_id']
    data = request.get_json()
    word = data.get('word')
    difficulty_id = data.get('difficulty_id')

    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()

    # 先找到對應的 word_id
    cursor.execute("SELECT word_id FROM words WHERE word=?", (word,))
    word_id = cursor.fetchone()

    if word_id:
        cursor.execute("UPDATE user_words SET difficulty_id=?, last_update_difficulty_time=datetime('now', 'localtime') WHERE user_id=? AND word_id=?", (difficulty_id, user_id, word_id[0]))
        conn.commit()
        conn.close()
        return jsonify({'message': '難易度已更新'}), 200
    else:
        conn.close()
        return jsonify({'error': '單字未找到'}), 404


# 進到 word.html 時，就執行 word_detail()，為了顯示這個單字所有詳細解釋，以及讓上一頁下一頁的按鈕功能正常
# [尚未完成] 這邊應該要依據首頁當時的篩選結果來設定start_date, end_date, difficulties
@app.route('/word')
def word_detail():
    if 'user_id' in session:
        
        word_name = request.args.get('word') #先解讀 url 上面的 word，並將 word assign 給 word_name
        #user_id = 1  # 假設用戶ID為1，可以根據實際情況動態獲取
        user_id = session['user_id']

        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d') + 'T00:00:00'
        end_date = datetime.now().strftime('%Y-%m-%d') + 'T23:59:59'
        difficulties = [1, 2, 3]

        words = fetch_filtered_words(start_date, end_date, difficulties, user_id)  #呼叫 fetch_filtered_words 將所有符合條件的單字列出來 assign 給 words
        word_index = next((i for i, w in enumerate(words) if w[1] == word_name), None)
        if word_index is None:
            return "Word not found", 404

        word = words[word_index] #words[word_index]會把第 n 個單字，這個單字的所有意思都抓出來，把這個單字都 assign 給 word
        print(word)
        prev_word = words[word_index - 1] if word_index > 0 else None
        next_word = words[word_index + 1] if word_index < len(words) - 1 else None

        return render_template('word.html', word=word, prev_word=prev_word, next_word=next_word) #將單字內容、上一頁、下一頁的內容，以 jinja2 的方式傳給前端，屬於 python 與 html 一種溝通方式

    return redirect(url_for('login'))
#------------------------#

# Route to about page
@app.route('/about')
def about():
    return render_template('about.html')




#-------------------------#
# for LINE 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)

#LINE 只要收到文字訊息，發現用戶還沒綁定任何 user_id，就問 user 他的 account
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    line_user_id = event.source.user_id
    msg = str(event.message.text).strip().lower()
    
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, account FROM user WHERE line_uid=?", (line_user_id,))
    user = cursor.fetchone()
    difficulty_id = 1  # 暫時固定測試

    if user:
        user_id, account = user
        if msg == "隨選難字":
            handle_option_1(line_bot_api, event, user_id, difficulty_id)
        elif msg == "隨選短文":
            handle_option_2(line_bot_api, event, user_id, difficulty_id)
        else:
            #reply_text = f"Hi {account} , 點擊下方'複習選單'功能，或傳送圖片新增單字"
            show_menu(line_bot_api, event)
    else:
        if msg.startswith("account:"):
            account = msg.split(":", 1)[1].strip().lower()
            cursor.execute("SELECT user_id FROM user WHERE lower(account)=?", (account,))
            user = cursor.fetchone()
            
            if user:
                user_id = user[0]
                cursor.execute("UPDATE user SET line_uid=? WHERE user_id=?", (line_user_id, user_id))
                conn.commit()
                reply_text = f"已記錄您的 account：{account}"
            else:
                reply_text = "帳號不存在，請重新輸入或註冊新帳號。"
        else:
            reply_text = "您尚未綁定帳號唷!\n請輸入「account: __ (填入帳號)」"
    
    conn.close()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_text))

#LINE只要收到圖片就做 1.儲存圖片 2.執行process_words_fromline dunction (內含process_uploaded_image)
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    line_user_id = event.source.user_id
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    
    filepath = f'static/uploads/{message_id}.jpg'
    with open(filepath, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM user WHERE line_uid=?", (line_user_id,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        process_words_fromline(filepath, user_id, event.reply_token)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("帳號: ___/n 送出範例「帳號: account1」"))

    conn.close()


#針對LINE新增的 function，將LINE收到的圖片進行opencv顏色辨識，將單字存入資料庫在顯示到LINE中
def process_words_fromline(filepath, user_id, reply_token):
    image, selected_texts, ocr_boxes, file_path = process_uploaded_image(filepath)
    
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()
    processed_words = []
    error_messages = []

    for word_to_search in selected_texts:
        word_to_search = word_to_search.lower()
        cursor.execute("SELECT * FROM words WHERE word=?", (word_to_search,))
        word_details = cursor.fetchone()
        
        if word_details:
            word_id = word_details[0]
            cursor.execute("INSERT OR IGNORE INTO user_words (user_id, word_id, difficulty_id) VALUES (?, ?, ?)", 
                           (user_id, word_id, 1))  # 難易度預設為1
            conn.commit()
            processed_words.append({
                'word': word_details[1],
                'pos': word_details[2],
                'pronunciation': word_details[3],
                'definition_zh': word_details[5]
            })
        else:
            word = get_word_details(word_to_search)
            if word:
                cursor.execute("""
                INSERT OR IGNORE INTO words (word, pos, pronunciation, definition_en, definition_zh, synonyms_en, synonyms_zh, example_en, example_zh, prefixes, roots, suffixes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    word['word'], word['pos'], word['pronunciation'], word['definition_en'], word['definition_zh'], 
                    word['synonyms_en'], word['synonyms_zh'], word['example_en'], word['example_zh'], 
                    word['prefixes'], word['roots'], word['suffixes']
                ))
                conn.commit()
                cursor.execute("SELECT word_id FROM words WHERE word=?", (word_to_search,))
                result = cursor.fetchone()
                if result:
                    word_id = result[0]
                    cursor.execute("INSERT INTO user_words (user_id, word_id, difficulty_id) VALUES (?, ?, ?)",
                                   (user_id, word_id, 1))  # 難易度預設為1
                    conn.commit()
                    processed_words.append({
                        'word': word['word'],
                        'pos': word['pos'],
                        'pronunciation': word['pronunciation'],
                        'definition_zh': word['definition_zh']
                    })
            else:
                error_messages.append(f"{word_to_search} 單字無法儲存")

    conn.close()

    if processed_words:
        reply_text = "以下單字已新增至您的單字書"
        for word_info in processed_words:
            reply_text += f"\n\n{word_info['word']}\n{word_info['pronunciation']} | {word_info['pos']} \n意思: {word_info['definition_zh']}"
    else:
        reply_text = "沒有單字被儲存"

    if error_messages:
        reply_text += "\n" + "\n".join(error_messages)
    
    line_bot_api.reply_message(reply_token, TextSendMessage(reply_text))









if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port,debug=True)
