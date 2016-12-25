import logging
import re

from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import yadict
import config

if config.Config.DEBUG:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
else:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        filename='yappi.log'
    )


class AnswerOption(object):
    TRANSLATE = '1'
    SKIP = '2'


class MessageTemplate(object):
    TRANSLATE = 'Would you like to translate it?'
    SKIP = 'Nevermind'


def encode_callback_data(answer_option, data):
    return '{}@{}'.format(answer_option, data)


def decode_callback_data(callback_data):
    return re.sub(r'^\d+@', '', callback_data)


def decode_answer_option(callback_data):
    return callback_data.split('@')[0]


def handle_message(bot, update, args):
    try:
        bot.sendMessage(
            update.message.chat_id,
            yadict.prepare_message(args),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as err:
        logging.exception(str(err))


def edit_message(bot, update, text):
    bot.editMessageText(
        text=text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN
    )


def handle_text(bot, update):
    user_message = update.message.text
    encoded_task = encode_callback_data(AnswerOption.TRANSLATE, user_message)

    keyboard = [[
        Button('tr', callback_data=encoded_task),
        Button('skip', callback_data=AnswerOption.SKIP)
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=update.message.chat_id,
        text=MessageTemplate.TRANSLATE,
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN)


def handle_message_dialog(bot, update, answer):
    callback_data = update.callback_query.data

    # translate request
    if answer == AnswerOption.TRANSLATE:
        content = decode_callback_data(callback_data)
        chat_id = update.callback_query.message.chat_id
        reply_text = yadict.prepare_message(content)

    elif answer == AnswerOption.SKIP:
        reply_text = MessageTemplate.SKIP

    edit_message(bot, update, reply_text)


def callback_handler(bot, update):
    answer = decode_answer_option(update.callback_query.data)

    translate_answers = (
        AnswerOption.TRANSLATE,
        AnswerOption.SKIP)

    if answer in translate_answers:
        handle_message_dialog(bot, update, answer)


updater = Updater(config.Config.BTOKEN)

updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler))
updater.dispatcher.add_handler(
    CommandHandler('tr', handle_message, pass_args=True))
updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_text))

updater.start_polling()
updater.idle()
