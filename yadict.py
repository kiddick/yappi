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
    warning = True
    if not data:
        return 'Your request is empty. Try again.', warning
    if isinstance(data,  list):
        data = ' '.join(data)
    data = str(data).replace('`', '').lower()
    if not data:
        return 'only tilde :(', warning
    else:
        warning = False
        return data, warning


# translate = translate + u"Sorry, can't find anything for `{}`."


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
