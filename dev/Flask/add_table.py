'''最原始只有一個 Table 的時候
import sqlite3
from datetime import datetime

# 連接資料庫
conn = sqlite3.connect('word.db')
cursor = conn.cursor()

# 創建 word 資料表，如果不存在的話
cursor.execute("""
CREATE TABLE IF NOT EXISTS word (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(50) UNIQUE,
    pronunciation VARCHAR(50),
    definition VARCHAR(50),
    example VARCHAR(50),
    difficulty INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# 更新資料表結構，如果已存在資料表，添加 created_at 欄位
try:
    cursor.execute("ALTER TABLE word ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
except sqlite3.OperationalError as e:
    print("Column already exists or another error occurred:", e)

# 準備插入的資料
release_list = [
    ('explore', '[ɪkˈsplɔːr]', '探索', 'The best way to explore the countryside is on foot.', 2),
    ('placatory', '[pləˈkeɪtəri]', '撫慰的', 'She adopted a placatory tone in an attempt to calm the situation.', 1)
]

# 使用 executemany 方法插入多筆資料，包含 created_at 欄位
cursor.executemany("INSERT INTO word (word, pronunciation, definition, example, difficulty, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
    [(word, pronunciation, definition, example, difficulty, datetime.now()) for word, pronunciation, definition, example, difficulty in release_list])

# 提交資料庫操作
conn.commit()

# 關閉資料庫連接
conn.close()
'''


import sqlite3
from datetime import datetime
import random

# 連接資料庫
conn = sqlite3.connect('app_words.db')
cursor = conn.cursor()
'''插入words table
# 創建 word 資料表，如果不存在的話
cursor.execute("""
CREATE TABLE IF NOT EXISTS words (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(50) UNIQUE,
    pos VARCHAR(50),
    pronunciation VARCHAR(50),
    definition_en VARCHAR(50),
    definition_zh VARCHAR(50),
    synonyms_en VARCHAR(50),
    synonyms_zh VARCHAR(50),
    example_en VARCHAR(50),
    example_zh VARCHAR(50),
    prefixes VARCHAR(50),
    roots VARCHAR(50),
    suffixes VARCHAR(50),
    difficulty_id INT
)
""")

# 插入的資料
release_list = [
    ('apple', 'noun', 'ˈæpəl', 'a fruit', '一种水果', 'fruit', '水果', 'I like to eat an apple.', '我喜欢吃苹果。', 'ap-', 'root', '-le', random.randint(1, 3)),
    ('banana', 'noun', 'bəˈnænə', 'a long curved fruit', '一种长弯水果', 'fruit', '水果', 'Bananas are yellow.', '香蕉是黄色的。', 'ba-', 'root', '-na', random.randint(1, 3))
]

# 插入多筆資料
cursor.executemany("""
INSERT INTO words (word, pos, pronunciation, definition_en, definition_zh, synonyms_en, synonyms_zh, example_en, example_zh, prefixes, roots, suffixes, difficulty_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", release_list)

# 提交資料庫操作
conn.commit()

# 關閉資料庫連接
conn.close()
'''
#-----------------------------------
''' 創建 user_words 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_words (
    user_id INTEGER,
    word_id INTEGER,
    difficulty_id INTEGER,
    last_update_difficulty_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    query_count INT DEFAULT 1,
    last_query_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_note VARCHAR(50),
    PRIMARY KEY (user_id, word_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (word_id) REFERENCES words(word_id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty(difficulty_id)
)
""")

# 插入 user_words 資料
user_words_list = [
    (1, 1, 1, 'First note'),
    (2, 2, 2, 'Second note'),
    (1, 2, 1, '3 note')
    (2, 1, 2, '4 note'),
]

cursor.executemany("""
INSERT INTO user_words (user_id, word_id, difficulty_id, user_note)
VALUES (?, ?, ?, ?)
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
    account VARCHAR(50) UNIQUE,
    password VARCHAR(50),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
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

# 插入 user_words 資料
user_words_list = [
    (1, 2, 1, '3 note'),
    (2, 1, 2, '4 note')
]

cursor.executemany("""
INSERT INTO user_words (user_id, word_id, difficulty_id, user_note)
VALUES (?, ?, ?, ?)
""", user_words_list)

# 提交資料庫操作
conn.commit()

# 關閉資料庫連接
conn.close()
