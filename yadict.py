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


def prepare_message(msg, user):
    if not msg:
        return 'Your request is empty. Try again.'
    if isinstance(msg,  list):
        msg = ' '.join(msg)
    check = str(msg).replace('`', '')
    if not check:
        msg = 'tilde(s)'
    else:
        msg = check
    try:
        spellcheck = pyaspeller.Word(msg)
        if spellcheck.spellsafe:
            msg = spellcheck.spellsafe
    except Exception as err:
        logging.exception(str(err))
        spellcheck = None
    try:
        translate = get_word(msg, user)
    except Exception as err:
        logging.exception(str(err))
        translate = 'Sorry, something went wrong!'
    if not translate:
        translate = answer_spellcheck(spellcheck, translate)
        translate = translate + u"Sorry, can't find anything for `{}`."
    else:
        translate = answer_spellcheck(spellcheck, translate)
        translate = '`{}`\n' + translate
    return translate.format(msg)


def get_word(src, user):
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
    if not json_dump['def']:
        return ''
    if not request:
        Request.create(content=src, raw=data.text, user=user)
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
    return res


class Word(object):

    def __init__(self, data):
        self.definitions = [Defenition(d) for d in data['def']]


class Defenition(object):

    def __init__(self, data):
        self.text = data['text']
        self.translition = data['tr'][0]['text']
        self.part_of_speech = data['pos']
        self.transcription = data.get('ts')
