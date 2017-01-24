"""
This module provides API functionality for yandex lingvo services.
"""

import json
import logging
import requests
import string

import pyaspeller
import config

from models import Request
from templates import MessageTemplate, Translate


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
    warning = True
    if not data:
        return MessageTemplate.EMPTY_REQUEST, warning
    if isinstance(data,  list):
        data = ' '.join(data)
    data = str(data).replace('`', '')
    if not data:
        return MessageTemplate.ONLY_TILDE, warning
    else:
        warning = False
        data = data.translate(str.maketrans('', '', string.punctuation))
        return data.lower().strip(), warning


def format_dict_message(data):
    res = ''
    delimeter = '\n'
    nbsp = u'\xa0'
    for _, topic in enumerate(data):
        res += Translate.POS.format(topic['pos'])
        if 'ts' in topic:
            res += Translate.TRANSCRIPTION.format(topic['ts'], delimeter)
        else:
            res += delimeter
        for tr in topic['tr']:
            res += Translate.TRANSLATION.format(nbsps=4 * nbsp, text=tr['text'])
            if 'mean' in tr:
                mean = ''
                for m in tr['mean']:
                    mean += Translate.MEANING_UNIT.format(m=m['text'])
                mean = Translate.MEANING.format(mean.rstrip('; '), delimeter)
                res += mean
            else:
                res += delimeter
            if 'ex' in tr:
                tmp = Translate.EXAMPLE.format(
                    nbsps=8 * nbsp,
                    ex=tr['ex'][0]['text'],
                    ex_tr='/ '.join([etr['text'] for etr in tr['ex'][0]['tr']]),
                    delimeter=delimeter
                )
                res += tmp
    return res


def dicservice_request(src):
    request = requests.compat.urlencode(
        {'key': YKEY, 'lang': 'en-ru', 'text': src})
    return requests.get('{}{}'.format(ENDPOINT, request))


def load_content_from_db(request):
    data = request.raw
    json_dump = json.loads(data)
    return format_dict_message(json_dump['def'])


def load_content_from_api(content):
    data = dicservice_request(content)
    json_dump = data.json()
    defenition = json_dump['def']
    if not defenition:
        return '', None
    request = Request.create(content=content, raw=data.text)
    return format_dict_message(defenition), request


class Word(object):

    def __init__(self, data):
        self.definitions = [Defenition(d) for d in data['def']]


class Defenition(object):

    def __init__(self, data):
        self.text = data['text']
        self.translition = data['tr'][0]['text']
        self.part_of_speech = data['pos']
        self.transcription = data.get('ts')
