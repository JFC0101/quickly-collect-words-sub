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
