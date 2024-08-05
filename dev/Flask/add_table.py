'''新增app_words.py的table
import sqlite3
from datetime import datetime
import random

# 連接資料庫
conn = sqlite3.connect('app_words.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS words (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(50) UNIQUE NOT NULL,
    pos VARCHAR(50),
    pronunciation VARCHAR(256),
    definition_en VARCHAR(256),
    definition_zh VARCHAR(256),
    synonyms_en VARCHAR(256),
    synonyms_zh VARCHAR(256),
    example_en VARCHAR(256),
    example_zh VARCHAR(256),
    prefixes VARCHAR(256),
    roots VARCHAR(256),
    suffixes VARCHAR(256)
)
""")

# 插入的資料
release_list = [
    ('independent', 'adjective', 'KK [ˌɪndɪˈpɛndənt]', 'not controlled or influenced by others; free to make your own decisions.', '獨立的，自主的，不受約束的', 'autonomous, self-governing, self-reliant, self-sufficient, free, sovereign', '自治的，自主的，自立的，獨立的，自由的，主權的', 'The country declared its independence from the colonial power.', '這個國家宣布脫離殖民統治，並宣布獨立。', 'in- / not 不', 'depend / to rely on 依靠', 'ent / having the quality of  具有…的性質'),
    ('defender', 'noun', 'KK [dɪˈfɛndər]', 'a person or thing that protects someone or something from attack or harm.', '防守者，保護者，辯護人', 'protector, guardian, shield, champion, advocate', '保護者，守護者，盾牌，擁護者，辯護者', 'The soldiers were valiant defenders of their country.', '士兵們是他們國家的勇敢衛士。', '', 'fend / to ward off 抵擋', 'er / one who  …的人')
]

# 插入多筆資料
cursor.executemany("""
INSERT INTO words (word, pos, pronunciation, definition_en, definition_zh, synonyms_en, synonyms_zh, example_en, example_zh, prefixes, roots, suffixes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", release_list)



cursor.execute("""
CREATE TABLE IF NOT EXISTS user_words (
    user_id INTEGER,
    word_id INTEGER,
    difficulty_id INTEGER DEFAULT 1,
    last_update_difficulty_time TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    create_time TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    query_count INTEGER DEFAULT 0,
    last_query_time TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (user_id, word_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (word_id) REFERENCES words(word_id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty(difficulty_id)
)
""")

# 插入 user_words 資料
user_words_list = [
    (1, 1, 1),
    (2, 2, 2),
    (1, 2, 1)
]

cursor.executemany("""
INSERT INTO user_words (user_id, word_id, difficulty_id)
VALUES (?, ?, ?)
""", user_words_list)

# 創建 difficulty 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS difficulty (
    difficulty_id INTEGER PRIMARY KEY,
    difficulty_level_zh VARCHAR(50)
)
""")

# 插入 difficulty 資料
difficulty_list = [
    (1, '困難'),
    (2, '中等'),
    (3, '簡單')
]

cursor.executemany("""
INSERT INTO difficulty (difficulty_id, difficulty_level_zh)
VALUES (?, ?)
""", difficulty_list)

# 創建 user 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50),
    account VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    create_time TIMESTAMP DEFAULT (datetime('now', 'localtime'))
)
""")

# 插入 user 資料
user_list = [
    ('user1', 'account1', 'password1'),
    ('user2', 'account2', 'password2')
]

cursor.executemany("""
INSERT INTO user (username, account, password)
VALUES (?, ?, ?)
""", user_list)

# 提交資料庫操作
conn.commit()

# 關閉資料庫連接
conn.close()
'''

#刪除某個單字
import sqlite3

def delete_word_and_related_entries(word_id):
    try:
        conn = sqlite3.connect('app_words.db')
        cursor = conn.cursor()
        
        # 刪除 user_words 表中相關的行
        cursor.execute("DELETE FROM user_words WHERE word_id = ?", (word_id,))
        
        # 刪除 words 表中的行
        cursor.execute("DELETE FROM words WHERE word_id = ?", (word_id,))
        
        conn.commit()
        print(f"Deleted word and related entries for word_id = {word_id}")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

# 刪除 word_id = 3 的行
#delete_word_and_related_entries(4)



#--------------------------#
#刪除 user_words 表中相關的行
import sqlite3

# 連接資料庫
conn = sqlite3.connect('app_words.db')
cursor = conn.cursor()

# 執行要打開  刪除 user_words 表中相關的行
#cursor.execute("DELETE FROM user_words WHERE user_id = ? AND word_id = ?", ('6', 13))

# 提交更改
conn.commit()
# 關閉資料庫連接
conn.close()

#--------------#
#生成帳號密碼填入
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def store_password(username, account, password):
    # 生成哈希密碼
    hashed_password = generate_password_hash(password)
    
    # 假設使用 SQLite 數據庫
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()
    
    # 將用戶名和哈希密碼插入到數據庫中
    cursor.execute("INSERT INTO user (username, account, password) VALUES (?, ?, ?)", (username, account, hashed_password))
    conn.commit()
    conn.close()
#如要執行請輸入下面這行
#store_password('username4', 'user4', 'PappyHaha')

#--------------#
#更改密碼
def update_password(account, new_password):
    # 生成哈希密碼
    hashed_password = generate_password_hash(new_password)
    
    # 假設使用 SQLite 數據庫
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()
    
    # 更新用戶的哈希密碼
    cursor.execute("UPDATE user SET password = ? WHERE account = ?", (hashed_password, account))
    conn.commit()
    conn.close()

#如要執行請輸入下面這行
#update_password('account1', 'AIproject')

''' 密码存储：绝对不应以明文形式存储密码。使用像 Werkzeug 这样的库来生成和验证密码哈希。

from werkzeug.security import generate_password_hash

password = 'PappyHaha'
hashed_password = generate_password_hash(password)
print(hashed_password)
'''

#新增 line_uid

def add_line_uid_column():
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()

    cursor.execute("ALTER TABLE user ADD COLUMN line_uid TEXT")
    conn.commit()
    conn.close()

# 呼叫此函數來新增欄位
#add_line_uid_column()



import sqlite3

conn = sqlite3.connect('app_words.db')
cursor = conn.cursor()

# 執行要打開
#cursor.execute("UPDATE user SET account =?, username=? WHERE user_id = ?", ('banana','banana',8))

conn.commit()
conn.close()