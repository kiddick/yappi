"""
This module provides API functionality for yandex lingvo services.
"""

import json
import logging
import requests

import pyaspeller
import config

from models import Request

logging.getLogger(__name__).addHandler(logging.NullHandler())

YKEY = config.Config.YKEY
ENDPOINT = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup?'


def answer_spellcheck(spellcheck, translate):
    if spellcheck:
        if not spellcheck.correct:
            if spellcheck.spellsafe:
                if translate:
                    return '    _Your request was corrected!_\n' + translate
                return '    _Your request was corrected!_\n'
    return translate


def check_spelling(data):
    try:
        spellcheck = pyaspeller.Word(data)
        if spellcheck.spellsafe:
            data = spellcheck.spellsafe
    except Exception as err:
        logging.exception(str(err))
        spellcheck = None

    return data, spellcheck


def normalize(data):
    if isinstance(data,  list):
        data = ' '.join(data)
    check = str(data).replace('`', '')
    if not check:
        data = 'tilde(s)'
    else:
        data = check

    return data


def prepare_message(msg):
    warning = False
    if not msg:
        warning = True
        return 'Your request is empty. Try again.', warning
    msg, spellcheck = check_spelling(normalize(msg))
    try:
        translate = get_word(msg)
    except Exception as err:
        logging.exception(str(err))
        translate = 'Sorry, something went wrong!'
        warning = True
    if not translate:
        translate = answer_spellcheck(spellcheck, translate)
        translate = translate + u"Sorry, can't find anything for `{}`."
        warning = True
    else:
        translate = answer_spellcheck(spellcheck, translate)
        translate = '`{}`\n' + translate
    return translate.format(msg), warning


def format_dict_message(data):
    res = ''
    delimeter = '\n'
    nbsp = u'\xa0'
    for _, topic in enumerate(data):
        res += '_{0}_{1}'.format(topic['pos'], delimeter)
        for tr in topic['tr']:
            res += u'*{nbsps}{text}*{delimeter}'.format(
                nbsps=4 * nbsp, text=tr['text'], delimeter=delimeter)
            if 'ex' in tr:
                res += 8 * nbsp + tr['ex'][0]['text'] + ' --- ' + \
                    '//'.join([etr['text']
                               for etr in tr['ex'][0]['tr']]) + delimeter
    return res


def get_word(src):
    request = Request.get_request(content=src)
    if request:
        data = request.raw
        json_dump = json.loads(data)
    else:
        data = requests.get(
            ENDPOINT + requests.compat.urlencode(
                {'key': YKEY, 'lang': 'en-ru', 'text': src})
        )
        json_dump = data.json()
    defenition = json_dump['def']
    if not defenition:
        return ''
    if not request:
        request = Request.create(content=src, raw=data.text)
    return format_dict_message(defenition)


class Word(object):

    def __init__(self, data):
        self.definitions = [Defenition(d) for d in data['def']]


class Defenition(object):

    def __init__(self, data):
        self.text = data['text']
        self.translition = data['tr'][0]['text']
        self.part_of_speech = data['pos']
        self.transcription = data.get('ts')
