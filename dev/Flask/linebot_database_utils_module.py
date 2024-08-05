# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 17:06:04 2024

@author: User
"""

import sqlite3
import random

def query_words(user_id, difficulty_id, sample_size):
    conn = sqlite3.connect('app_words.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT w.word, w.pos, w.pronunciation, w.definition_en, w.definition_zh, w.example_en, w.example_zh
        FROM user_words uw
        JOIN words w ON uw.word_id = w.word_id
        WHERE uw.user_id = ? AND uw.difficulty_id = ?;
        """, (user_id, difficulty_id))
    words = cursor.fetchall()
    conn.close()
    
    word_list = [
        {
            'word': row[0],
            'pos': row[1],
            'pronunciation': row[2],
            'definition_en': row[3],
            'definition_zh': row[4],
            'example_en': row[5],
            'example_zh': row[6]
        } for row in words
    ]
    
    if len(word_list) > sample_size:
        selected_words = random.sample(word_list, sample_size)
    else:
        selected_words = word_list

    return selected_words
