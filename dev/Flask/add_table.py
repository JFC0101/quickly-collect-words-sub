"""
import sqlite3

connection = sqlite3.connect('word.db')

cursor = connection.cursor()



cursor.execute("create table word ( id INT, word VARCHAR(50), pronunciation VARCHAR(50),	definition VARCHAR(50), example VARCHAR(50))")

release_list = [
    (1, 'explore', '[ɪkˈsplɔr]','探索', 'The best way to explore the countryside is on foot.'),
	(2, 'placatory', '[pləˈkeɪtəri]', '撫慰的', 'The tone of her voice was placatory.')
]

cursor.executemany("insert into word values(?,?,?,?,?)", release_list)

for row in cursor.execute("select * from word"):
    print(row)


connection.close() 
"""

import sqlite3

conn = sqlite3.connect('word.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS word (id INT, word VARCHAR(50), pronunciation VARCHAR(50), definition VARCHAR(50), example VARCHAR(50))")
release_list = [
    (1, 'explore', '[ɪkˈsplɔːr]', '探索', 'The best way to explore the countryside is on foot.'),
    (2, 'placatory', '[pləˈkeɪtəri]', '撫慰的', 'She adopted a placatory tone in an attempt to calm the situation.')
]
cursor.executemany("INSERT INTO word (id, word, pronunciation, definition, example) VALUES (?, ?, ?, ?, ?)", release_list)
conn.commit()
conn.close()
