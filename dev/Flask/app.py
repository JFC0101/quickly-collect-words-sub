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
#這個 function 是去資料庫查找符合篩選條件資格的單字，所以 index() 或 filter() function 都有呼叫這個函數
#原本是預計使用 fetch_all-words()，但因為做了篩選功能，所以每次抓資料庫單字時，都是依據篩選結果(start_date, end_date, difficulties)去查找單字
def fetch_filtered_words(start_date, end_date, difficulties):
    conn = sqlite3.connect('word.db')
    cursor = conn.cursor()
    query = "SELECT * FROM word WHERE created_at BETWEEN ? AND ? AND difficulty IN ({seq})".format(
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
        new_words = data.get('newWords', '').split(',')  # 从 POST 请求体中获取 new_words
        print('new_words=',new_words)
    else:
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d') + 'T00:00:00'
        end_date = datetime.now().strftime('%Y-%m-%d') + 'T23:59:59'
        difficulties = [1, 2, 3]
        new_words = request.args.get('new_words', '').split(',')  # 从 URL 参数获取 new_words

    
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
            'new_words': new_words,
            'start_date': start_date,
            'end_date': end_date,
            'difficulties': difficulties
        })
    else:
        return render_template('index.html', words=filtered_words, new_words=new_words, start_date=start_date, end_date=end_date, difficulties=difficulties)




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
            'definition': word_details[4],
            'example': word_details[5],
            'difficulty': word_details[6]
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
# [尚未完成] 待修正一次可以傳一堆單字處理，資料庫有的就忽略，且處理完回到首頁，要把新增的單字顯示綠色框
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

    # 返回JSON响应给 word-preview.html 的 js
    toast_message = '新增成功'
    new_words_query = ",".join(processed_words)
    return redirect(f'/?new_words={new_words_query}&toast={toast_message}')


#------------------------#
#當upload.html點擊"擷取上傳"就會把圖片存起來，命名為capture.jpg
@app.route('/upload_capture', methods=['POST'])
def upload_capture():
    # 保存捕获的 JPEG 图片
    file = request.files.get('file')
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'capture.jpg'))
        return jsonify({'success': True})
    return jsonify({'error': 'No file uploaded'})


#处理文件上传请求，保存上传的文件到指定的文件夹中
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


#將處理過的圖片，傳到前端呈現、並顯示單字，目前暫用 words list 寫死有哪些單字
#[尚未處理] 不知道如何串接 Jeff 的東西
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')

        if uploaded_file:
            # Process uploaded file if needed
            # Example: recognizing words from the image
            words = ['show', 'nothing','maybe','explore']
            image_name = uploaded_file.filename
            uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

            # Redirect to word preview page with image and words data
            return jsonify({'image': image_name, 'words': words})  #upload.js 接收了 json 內容就會將畫面導到 word-preview 頁面

    return render_template('upload.html')

#呈現圖片的單字、上傳的圖片 (應該要標註哪些地方有抓到了)
#[尚未完成] 實際上圖片應該是 Jeff 處理完的圖片放到 word-preview 畫面中，但目前是抓上傳的圖片
@app.route('/word-preview')
def word_preview():
    image_name = request.args.get('image')
    words = request.args.get('words').split(',')
    return render_template('word-preview.html', image_name=image_name, words=words)



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
    app.run(debug=True)
