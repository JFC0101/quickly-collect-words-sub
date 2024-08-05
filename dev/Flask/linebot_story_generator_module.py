# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 17:05:12 2024

@author: User
"""

import configparser
import google.generativeai as genai
import time

def generate_story(word1, word2, word3, max_retries=3):


    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    system_instruction = f"""指令一： 請為我生成一個約 60字的短篇故事，在開頭給一個吸引人的標題。請讓每次故事內容風格都不一樣，確保故事有完整的起承轉合。

指令二： 故事中必須包含以下三個關鍵詞，請以斜體強化顯示這三個關鍵詞，並讓它們自然融入情節中，發揮關鍵作用：{word1}、{word2}、{word3}。

指令三： 請將英文故事以標點符號斷行，每行後加上中文翻譯。例如：
I woke up this morning feeling
我今天早上醒來感覺
under the weather.
身體不太舒服。

指令四： 故事的情節、角色、背景和結局每次都應有所不同，避免重複。請特別注意故事的邏輯性和連貫性。

指令五： 故事可以設定在各種不同的情境中，例如：旅行、工作、夢境、派對、歷史事件等。鼓勵嘗試創新的情境和風格。"""

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    for attempt in range(max_retries):
        try:
            response = model.generate_content(system_instruction)
            if response.text:
                return response.text
            else:
                print(f"嘗試 {attempt + 1}: 生成的內容為空，重試中...")
        except ValueError as e:
            if "The `response.text` quick accessor requires the response to contain a valid `Part`" in str(e):
                print(f"嘗試 {attempt + 1}: 內容被阻擋，重試中...")
            else:
                raise e
        except Exception as e:
            print(f"嘗試 {attempt + 1} 失敗: {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(2)

    return "無法生成故事，請稍後再試或使用不同的關鍵詞。"
