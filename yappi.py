import logging

from telegram import ParseMode
from telegram.ext import Updater, CommandHandler

import yadict
import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='yappi.log'
)


def handle_message(bot, update, args):
    try:
        bot.sendMessage(
            update.message.chat_id,
            yadict.prepare_message(args),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as err:
        logging.exception(str(err))

updater = Updater(config.Config.BTOKEN, job_queue_tick_interval=60 * 60)

updater.dispatcher.add_handler(CommandHandler('tr', handle_message))

updater.start_polling()
updater.idle()
