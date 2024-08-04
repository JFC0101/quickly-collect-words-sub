# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 17:03:18 2024

@author: User
"""

from linebot.models import TextMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction
from linebot_database_utils_module import query_words
from linebot_story_generator_module import generate_story

def handle_option_1(line_bot_api, event, user_id, difficulty_id):
    words = query_words(user_id, difficulty_id, sample_size=1)
    if words:
        reply_text = "隨機英文難字:\n"
        for word_info in words:
            word = word_info['word']
            pos = word_info['pos']
            pronunciation = word_info['pronunciation']
            definition_en = word_info['definition_en']
            definition_zh = word_info['definition_zh']
            example_en = word_info['example_en']
            example_zh = word_info['example_zh']
            
            reply_text += (
                f"[單字]：{word}\n"
                f"[詞性]：{pos}\n"
                f"[音標]：{pronunciation}\n"
                f"[字義(英)]：\n    {definition_en}\n"
                f"[字義(中)]：\n    {definition_zh}\n"
                f"[例句]：\n    {example_en}\n"
                f"[翻譯]：\n    {example_zh}\n"
            )
    else:
        reply_text = "沒有找到符合條件的單字。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=reply_text)
    )

def handle_option_2(line_bot_api, event, user_id, difficulty_id):
    words = query_words(user_id, difficulty_id, sample_size=3)
    if len(words) >= 3:
        word_values = [f"*{word_info['word']}*" for word_info in words]  # 將單字加上 * 符號
        story = generate_story(word_values[0], word_values[1], word_values[2])
        
        if story:
            reply_text = "隨選英文難字：\n" + "\n".join(word_values)
            reply_text += "\n\n難字短文：\n" + story
        else:
            reply_text = "無法生成故事。"
    else:
        reply_text = "沒有足夠的單字來生成故事。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=reply_text)
    )
    
def show_menu(line_bot_api, event):
    buttons_template = ButtonsTemplate(
        title='難字隨選應用',
        text='請選擇一個選項(任意鍵回選單):',
        actions=[
            MessageTemplateAction(label='1.隨選難字複習', text='選項 1'),
            MessageTemplateAction(label='2.隨選難字短文', text='選項 2'),
        ]
    )
    template_message = TemplateSendMessage(
        alt_text='難字隨選應用',
        template=buttons_template
    )
    line_bot_api.reply_message(event.reply_token, template_message)
