1.app_linebot_main.app 	示範串接圖文選單主程式
	line key
		LineBotApi('')  ----->Channel access token
		WebhookHandler('') -->Channel secret
	db query 預設
		user_id = 1  # 暫時固定測試，須改抓動態user_id
		difficulty_id = 1  # 暫時固定測試
	圖文選單點按呼叫
		隨選難字	handle_option_1(line_bot_api, event, user_id, difficulty_id)
		隨選短文	handle_option_2(line_bot_api, event, user_id, difficulty_id)

2.linebot_database_utils_module.py	搜尋資料庫特定使用者難字

3.linebot_message_handlers_module.py	處理圖文選單的"隨選難字"及"隨選短文"功能

4.linebot_story_generator_module.py		生成"隨選短文"內容

5.config.ini	針對linebot_story_generator_module.py中，AI Studio呼叫所需之API Key
