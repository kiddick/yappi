import os
import logging
import requests
import json
import telegram
import pyaspeller
from flask import Flask, request

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

DEBUG = app.config['DEBUG']


global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])


def answer_spellcheck(spellcheck, translate):
    if spellcheck:
        if not spellcheck.correct:
            if spellcheck.spellsafe:
                if translate:
                    return '    _Your request was corrected!_\n' + translate
                return '    _Your request was corrected!_\n'
    return translate


def prepare_message(msg):
    if msg.startswith('/tr'):
        msg = msg[4:]
        if not msg:
            return 'Your request is empty. Try again.'
        check = msg.replace('`', '')
        if not check:
            msg = 'tilde(s)'
        else:
            msg = check
        try:
            spellcheck = pyaspeller.Word(msg)
            if spellcheck.spellsafe:
                msg = spellcheck.spellsafe
        except Exception as err:
            logging.debug(str(err))
            spellcheck = None
        try:
            translate = get_word(msg)
        except Exception as err:
            logging.debug(str(err))
            translate = 'Sorry, something went wrong!'
        if not translate:
            translate = answer_spellcheck(spellcheck, translate)
            translate = translate + u"Sorry, can't find anything for `{}`."
        else:
            translate = answer_spellcheck(spellcheck, translate)
            translate = '`{}`\n' + translate
        return translate.format(msg)


def handle_message(msg, chat_id):
    bot.sendMessage(
        chat_id,
        prepare_message(msg),
        parse_mode=telegram.ParseMode.MARKDOWN
    )


def get_word(src):
    ykey = app.config['YANDEX_KEY']
    data = requests.get(
        'https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key=' + ykey + '&lang=en-ru&text=' + src)
    json_dump = json.loads(data.text)
    if not json_dump:
        return
    # res = '*-> {}*\n'.format(src)
    res = ''
    delimeter = '\n'
    nbsp = u'\xa0'
    for _, topic in enumerate(json_dump['def']):
        res += '_{0}_{1}'.format(topic['pos'], delimeter)
        for tr in topic['tr']:
            res += u'*{nbsps}{text}*{delimeter}'.format(
                nbsps=4 * nbsp, text=tr['text'], delimeter=delimeter)
            if 'ex' in tr:
                res += 8 * nbsp + tr['ex'][0]['text'] + ' --- ' + \
                    '//'.join([etr['text']
                               for etr in tr['ex'][0]['tr']]) + delimeter
    with open('query_list.log', 'a') as query_list:
        try:
            query_list.write(src + '\n')
        except UnicodeEncodeError as err:
            logging.debug(str(err))
    return res


#######

@app.route('/ya', methods=['POST'])
def webhook_handler():
    try:
        if request.method == "POST":
            update = telegram.Update.de_json(request.get_json(force=True))
            text = update.message.text
            chat_id = update.message.chat.id
            handle_message(text, chat_id)
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
