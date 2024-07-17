"""
import sqlite3

connection = sqlite3.connect('word.db')

cursor = connection.cursor()



cursor.execute("create table word ( id INT AUTO_INCREMENT, word VARCHAR(50) UNIQUE, pronunciation VARCHAR(50),	definition VARCHAR(50), example VARCHAR(50), difficulty VARCHAR(50))")

release_list = [
    (1, 'explore', '[ɪkˈsplɔr]','探索', 'The best way to explore the countryside is on foot.'),
	(2, 'placatory', '[pləˈkeɪtəri]', '撫慰的', 'The tone of her voice was placatory.')
]

cursor.executemany("insert into word values(?,?,?,?,?,?)", release_list)

for row in cursor.execute("select * from word"):
    print(row)


connection.close() 
"""

import sqlite3

conn = sqlite3.connect('word.db')
cursor = conn.cursor()

# 創建 word 資料表，如果不存在的話
cursor.execute("CREATE TABLE IF NOT EXISTS word (id INTEGER PRIMARY KEY AUTOINCREMENT, word VARCHAR(50) UNIQUE, pronunciation VARCHAR(50), definition VARCHAR(50), example VARCHAR(50), difficulty INT)")

release_list = [
    ('explore', '[ɪkˈsplɔːr]', '探索', 'The best way to explore the countryside is on foot.', 2),
    ('placatory', '[pləˈkeɪtəri]', '撫慰的', 'She adopted a placatory tone in an attempt to calm the situation.', 1)
]

# 使用 executemany 方法插入多筆資料
cursor.executemany("INSERT INTO word (word, pronunciation, definition, example, difficulty) VALUES (?, ?, ?, ?, ?)", release_list)

# 提交資料庫操作
conn.commit()

# 關閉資料庫連接
conn.close()

