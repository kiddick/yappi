# -*- coding: utf-8 -*-


class MessageTemplate(object):
    TRANSLATE = 'Would you like to translate it?'
    SKIP = 'Nevermind'
    CALLBACK_DATA_MISSING = 'Can\'t identify your request :('
    USER_STATS_LINE = '*{}:* {}'
    ALREADY_REQUESTED = 'You\'ve already requested that!'
    CANT_FIND = 'Sorry, can\'t find anything for `{}`.'
    EMPTY_REQUEST = 'Your request is empty. Try again.'
    ONLY_TILDE = 'There is only tilde, so check your input.'
    BOOKMARK = '❤'


class Translate(object):
    HEAD = '`>>> {caption}`\n{answer}'
    POS = '_{}_'
    TRANSCRIPTION = '   `[{}]`{}'
    TRANSLATION = '{nbsps}*{text}*'
    MEANING = '    `({})`{}'
    MEANING_UNIT = '{m}; '
    EXAMPLE = '{nbsps}{ex} — {ex_tr}{delimeter}'
