from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime, timedelta


app = Flask(__name__)

#設定圖片上傳後要存到哪個資料夾
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

#---------------------# Gemini api 的部分
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

# 只要呼叫這個 Function，就是去問 Gemini API 單字_details
def get_word_details(word):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=f'input:{word},output ex:Word: explore\nPronunciation: /ɪkˈsplɔːr/\nDefinition: 探索, 調查 \nExample: The best way to explore the countryside is on foot.'
    )

    response = model.generate_content({word})
    print('成功呼叫了gemini api 取得單字意思')
    #這邊要依據 Gemini 回傳的訊息，整理成一個 dictionary，裡面放了單字所有的意思
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
            #照理說這邊還要有一堆
        }
    return None

#------------------------#
#這個 fetch_filtered_words() function 是去資料庫查找符合篩選條件資格的單字，所以 index() 或 filter() function 都有呼叫這個函數
#原本是預計使用 fetch_all-words()，但因為做了篩選功能，所以每次抓資料庫單字時，都是依據篩選結果(start_date, end_date, difficulties)去查找單字
def fetch_filtered_words(start_date, end_date, difficulties):
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    query = "SELECT * FROM word WHERE created_at BETWEEN ? AND ? AND difficulty IN ({seq}) ORDER BY id DESC".format(
        seq=','.join(['?']*len(difficulties))
    )
    cursor.execute(query, (start_date, end_date, *difficulties))
    words = cursor.fetchall()
    conn.close()
    return words

#------------------------#
#当页面加载时，首先通过 html 中的 applyDefaultFilter 函數由前端送預設的篩選內容給後端，後端去找符合篩選結果的單字 (fetch_filtered_words) 包裝成 json 給前端
@app.route('/', methods=['GET', 'POST'])
def index():
    #从 POST 请求的 JSON 数据中提取 startDate、endDate、difficulties 和 newWords。
    if request.method == 'POST':
        data = request.get_json()
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        difficulties = data.get('difficulties')

    else:
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d') + 'T00:00:00'
        end_date = datetime.now().strftime('%Y-%m-%d') + 'T23:59:59'
        difficulties = [1, 2, 3]
    
    filtered_words = fetch_filtered_words(start_date, end_date, difficulties)

    # 把 filtered_words 變成 json 送給前端
    if request.method == 'POST':
        return jsonify({
            'words': [{
                'word': word[1],
                'pronunciation': word[2],
                'definition': word[4],
                'difficulty': word[5],
                'difficulty_text': '困難' if word[5] == 1 else ('中等' if word[5] == 2 else '簡單'),
                'type': word[3]
            } for word in filtered_words],
            'start_date': start_date,
            'end_date': end_date,
            'difficulties': difficulties
        })
    else:
        return render_template('index.html', words=filtered_words, start_date=start_date, end_date=end_date, difficulties=difficulties)




#---------------------#
# 前端页面获取用户设置的筛选条件，发送这些条件到服务器(後端)进行数据过滤，然后更新页面上的词汇列表
@app.route('/filter', methods=['POST'])
def filter_words():

    #从请求体中获取 JSON 数据，并提取 startDate、endDate 和 difficulties
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    difficulties = data.get('difficulties', [])

    #用fetch_filtered_words() 查找資料庫符合結果的單字們
    words = fetch_filtered_words(start_date, end_date, difficulties)
    
    # 為了看有沒有運作，所以 print 一下有處理了
    print(f"Filtered words: filter_words() success")

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



#------------------------#
#前端輸入文字送出搜尋，如果資料庫找得到，那就給前端資料庫的資料(json)
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    word_to_search = data['word']
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM word WHERE word=?", (word_to_search,))
    word_details = cursor.fetchone()
    conn.close()
    if word_details:
        return jsonify({'word': {
            'word': word_details[1],
            'pronunciation': word_details[2],
            'definition': word_details[3],
            'example': word_details[4],
            'difficulty': word_details[5]
        }, 'word_in_db': True})
    else:
        return jsonify({'word': None})

#因為後端說資料庫沒有({'word': None})，前端就呼叫後端這個函數，請後端去問 gemini (get_word_details)，把單字的意思包裝json給前端
@app.route('/get_word_details')
def api_get_word_details():
    word_to_search = request.args.get('word')
    if not word_to_search:
        return jsonify({'error': '沒有指定單詞'}), 400
    try:
        word_details = get_word_details(word_to_search)
        return jsonify(word_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#前端用戶說要新增這個單字，所以後端就去新增到db，然後把新增的單字內容跟 success 結果給前端
@app.route('/add_word', methods=['POST'])
def add_word():
    data = request.get_json()
    word = data['word']
    word_details = get_word_details(word)  # Assume this function fetches word details correctly
    if word_details:
        conn = sqlite3.connect('word.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO word (word, pronunciation, definition, example, difficulty) VALUES (?, ?, ?, ?, ?)",
                           (word_details['word'], word_details['pronunciation'], word_details['definition'], word_details['example'], 1))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': '數據庫錯誤'}), 500
        finally:
            conn.close()
        return jsonify({'success': '新增成功', 'word_details': word_details})
    else:
        return jsonify({'error': '無法獲取單字詳細內容'}), 404

#------------------------#
    
# 上傳圖片或是照相得到的新的單字，在 word-preview.html 頁面按送出執行會呼叫這個路由進行 process_words() function 來 Add a new word to the database
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
                                   (word['word'], word['pronunciation'], word['definition'], word['example'], 1))
                    conn.commit()
                    processed_words.append(word_to_search)

        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error processing words'}), 500

    # 返回JSON响应给 word-preview.html 的 js
    toast_message = '新增成功'
    new_words_query = ",".join(processed_words)
    return redirect(f'/?new_words={new_words_query}&toast={toast_message}')


#------------------------#
#from main import process_uploaded_image  #Monday自己測試的版本
from image_processor import process_uploaded_image
from werkzeug.utils import secure_filename

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
    if request.method == 'POST':
        #這個應該是把處理過的圖片呼叫出來
        uploaded_file = request.files.get('file')

        if uploaded_file:
            # 保存文件到指定目录
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            # 调用process_uploaded_image函数处理上传的图片

#修正return項目
#            selected_texts, ocr_boxes = process_uploaded_image(filepath)
            image, selected_texts, ocr_boxes = process_uploaded_image(filepath)

            processed_image_path = 'processed_image.jpg'

            # 返回处理后的图片和单词列表
            return jsonify({
                'image': processed_image_path,
                'words': selected_texts,
                'ocr_boxes': ocr_boxes
            })#upload.js 接收了 json 內容就會將畫面導到 word-preview 頁面

    #如果不是 post 就是單純的打開 upload 畫面
    return render_template('upload.html')



#進入 word-preview.html
@app.route('/word-preview')
def word_preview():
    return render_template('word-preview.html')

#------------------------#
# 在 word.html 裡面點擊難易度 label 呼叫後端進行 update_difficulty() function 運行，更新難易度
@app.route('/update_difficulty', methods=['POST'])
def update_difficulty():
    data = request.get_json()
    word = data.get('word')
    difficulty = data.get('difficulty')

    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE word SET difficulty=? WHERE word=?", (difficulty, word))
    conn.commit()
    conn.close()

    return jsonify({'message': '難易度已更新'}), 200


# 進到 word.html 時，就執行 word_detail()，為了顯示這個單字所有詳細解釋，以及讓上一頁下一頁的按鈕功能正常
# [尚未完成] 這邊應該要依據首頁當時的篩選結果來設定start_date, end_date, difficulties
@app.route('/word')
def word_detail():
    word_name = request.args.get('word')

    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d') + 'T00:00:00'
    end_date = datetime.now().strftime('%Y-%m-%d') + 'T23:59:59'
    difficulties = [1, 2, 3]

    words = fetch_filtered_words(start_date, end_date, difficulties)
    word_index = next((i for i, w in enumerate(words) if w[1] == word_name), None)
    if word_index is None:
        return "Word not found", 404

    word = words[word_index]
    prev_word = words[word_index - 1] if word_index > 0 else None
    next_word = words[word_index + 1] if word_index < len(words) - 1 else None

    return render_template('word.html', word=word, prev_word=prev_word, next_word=next_word)

#------------------------#

# Route to about page
@app.route('/about')
def about():
    return render_template('about.html')




if __name__ == '__main__':
    app.run()
