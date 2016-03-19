import os
import logging
from flask import Flask, request

import telegram
import yadict

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

DEBUG = app.config['DEBUG']

yadict.YKEY = app.config['YANDEX_KEY']


global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])


def handle_message(msg, chat_id):
    try:
        bot.sendMessage(
            chat_id,
            yadict.prepare_message(msg),
            parse_mode=telegram.ParseMode.MARKDOWN
        )
    except Exception as err:
        logging.exception(str(err))


@app.route('/ya', methods=['POST'])
def webhook_handler():
    try:
        if request.method == "POST":
            update = telegram.Update.de_json(request.get_json(force=True))
            text = update.message.text
            chat_id = update.message.chat.id
            handle_message(text, chat_id)
        return 'ok'
    except Exception:
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

                handle_message(text, chat_id)
                last_update_id = update_id + 1
        else:
            last_update_id = get_last_update_id()

if not DEBUG:
    set_webhook()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='bot.log'
)
logging.debug('>>> Bot is started!\n')

if __name__ == '__main__':
    if DEBUG:
        unset_webhook()
        get_updates()
    else:
        app.run(host='0.0.0.0')
