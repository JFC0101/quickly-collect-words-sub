from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from linebot_message_handlers_module import handle_option_1, handle_option_2, show_menu


app = Flask(__name__)

line_bot_api = LineBotApi('')
handler = WebhookHandler('')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    user_id = 1  # 暫時固定測試
    difficulty_id = 1  # 暫時固定測試
    
    if user_message == "隨選難字":
        handle_option_1(line_bot_api, event, user_id, difficulty_id)
    elif user_message == "隨選短文":
        handle_option_2(line_bot_api, event, user_id, difficulty_id)
    else:
        show_menu(line_bot_api, event)

if __name__ == "__main__":
    app.run()

