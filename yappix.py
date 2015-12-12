import os

import telegram
from flask import Flask, request

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

DEBUG = False


global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])


@app.route('/ya', methods=['POST'])
def webhook_handler():
    try:
        if request.method == "POST":
            update = telegram.Update.de_json(request.get_json(force=True))
            chat_id = update.message.chat.id
            text = '*`' + update.message.text.encode('utf-8') + '`*'
            bot.sendMessage(
                chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
        return 'ok'
    except Exception as e:
        raise


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    with open(os.path.join(__location__, 'ngrok.host'), 'r') as nh:
        webhook_url = nh.read()
    print webhook_url
    s = bot.setWebhook(webhook_url='https://{}/ya'.format(webhook_url))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

def unset_webhook():
    bot.setWebhook(webhook_url=None)


@app.route('/')
def index():
    return '.'


def get_last_update_id():
    new_updates = bot.getUpdates(timeout=10)
    if new_updates:
        return new_updates[0].update_id


def get_updates():
    last_update_id = get_last_update_id()
    while True:
        if last_update_id:
            for update in bot.getUpdates(offset=last_update_id, timeout=10):
                text = update.message.text
                chat_id = update.message.chat_id
                update_id = update.update_id

                bot.sendMessage(chat_id=chat_id, text=text)
                last_update_id = update_id + 1
                if text == 'exit':
                    bot.getUpdates(offset=last_update_id)
                    return
        else:
            last_update_id = get_last_update_id()

if not DEBUG:
    set_webhook()

if __name__ == '__main__':
    if DEBUG:
        unset_webhook()
        get_updates()
    else:
        app.run(host='0.0.0.0')

