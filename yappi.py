"""
A main module with Yappi translator bot powered by Telegram Bot API.
"""

from functools import partial, wraps
import logging

from telegram import InlineKeyboardButton as Button
from telegram import Emoji, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import yadict
import config

from models import db, CallbackEntity, Request, User, Chat, FirstRequest, Message
from templates import MessageTemplate

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


def save_callback_data(data):
    return CallbackEntity.create(data=data)


def encode_callback_data(answer_option, index):
    return '{}@{}'.format(answer_option, index)


def decode_callback_data(callback_data):
    index = int(callback_data.split('@')[1])
    return CallbackEntity.get_callback(index)


def decode_answer_option(callback_data):
    return callback_data.split('@')[0]


def userify(func):
    @wraps(func)
    @db.atomic()
    def wrapper(*args, **kwargs):
        update = args[1]
        request = update.callback_query or update.message
        tid = request.from_user.id
        name = request.from_user.first_name
        user, _ = User.get_or_create(tid=tid, name=name)
        kwargs['user'] = user
        return func(*args, **kwargs)
    return wrapper


def chatify(func):
    @wraps(func)
    @db.atomic()
    def wrapper(*args, **kwargs):
        update = args[1]
        request = update.callback_query or update
        chat_id = request.message.chat_id
        chat, _ = Chat.get_or_create(chat_id=chat_id)
        kwargs['chat'] = chat
        return func(*args, **kwargs)
    return wrapper


def messagify(func):
    @wraps(func)
    @db.atomic()
    def wrapper(*args, **kwargs):
        update = args[1]
        request = update.callback_query or update
        message_id = request.message.message_id
        time = request.message.to_dict()['date']
        message = Message.create(
            chat=kwargs['chat'],
            user=kwargs['user'],
            message_id=message_id,
            time=time
        )
        kwargs['message'] = message
        return func(*args, **kwargs)
    return wrapper


def edit_message(bot, update, text):
    return bot.edit_message_text(
        text=text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN
    )


def send_message(bot, update, text):
    return bot.send_message(
        chat_id=update.message.chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )


@db.atomic()
def translate(content, user, chat, message, bot, reply):
    def reply_and_save(request):
        reply_message = reply(answer)
        message.request = request
        message.save()
        FirstRequest.create(
            request=request,
            chat=chat,
            user=user,
            message=reply_message.message_id
        )
    content, warning = yadict.normalize(content)
    if warning:
        reply(content)
        return
    fr_query, request = FirstRequest.get_first_request_and_request(
        chat=chat, user=user, content=content)
    if fr_query:
        reply(MessageTemplate.ALREADY_REQUESTED)
        bot.send_message(
            chat.chat_id,
            Emoji.WHITE_UP_POINTING_INDEX,
            reply_to_message_id=fr_query.message.message_id
        )
    else:
        if request:
            answer = yadict.load_content_from_db(request)
            reply_and_save(request)
        else:
            answer, created_request = yadict.load_content_from_api(content)
            if not answer:
                reply(MessageTemplate.CANT_FIND.format(content))
            else:
                reply_and_save(created_request)


@chatify
@userify
@messagify
def translate_command(bot, update, args, **kwargs):
    user = kwargs['user']
    chat = kwargs['chat']
    message = kwargs['message']
    reply = partial(send_message, bot, update)
    translate(args, user, chat, message, bot, reply)


def handle_text(bot, update):
    user_message = update.message.text
    data_id = save_callback_data(user_message)
    encode_translate = encode_callback_data(AnswerOption.TRANSLATE, data_id)
    encode_skip = encode_callback_data(AnswerOption.SKIP, data_id)

    keyboard = [[
        Button('tr', callback_data=encode_translate),
        Button('skip', callback_data=encode_skip)
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=update.message.chat_id,
        text=MessageTemplate.TRANSLATE,
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN)


@chatify
@userify
@messagify
def handle_message_dialog(bot, update, answer, **kwargs):
    reply = partial(edit_message, bot, update)
    callback_data = update.callback_query.data
    content = decode_callback_data(callback_data)
    user = kwargs['user']
    chat = kwargs['chat']
    message = kwargs['message']

    if not content:
        reply(MessageTemplate.CALLBACK_DATA_MISSING)

    # translate request
    elif answer == AnswerOption.TRANSLATE:
        translate(content, user, chat, message, bot, reply)

    elif answer == AnswerOption.SKIP:
        reply(MessageTemplate.SKIP)


def callback_handler(bot, update):
    answer = decode_answer_option(update.callback_query.data)

    translate_answers = (
        AnswerOption.TRANSLATE,
        AnswerOption.SKIP)

    if answer in translate_answers:
        handle_message_dialog(bot, update, answer)


def stats(bot, update):
    stats_message = '\n'.join(
        MessageTemplate.USER_STATS_LINE.format(k, v)
        for k, v in Request.statistics().items()
    )

    bot.sendMessage(
        update.message.chat_id,
        stats_message,
        parse_mode=ParseMode.MARKDOWN
    )


updater = Updater(config.Config.BTOKEN)

updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler))
updater.dispatcher.add_handler(
    CommandHandler('tr', translate_command, pass_args=True))
# updater.dispatcher.add_handler(CommandHandler('stats', stats))
updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_text))

updater.start_polling()
updater.idle()
