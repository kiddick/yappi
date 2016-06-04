"""
This module provides API functionality for yandex lingvo services.
"""

import logging
import random
import requests
import json

import pyaspeller
import config

from pony.orm import *

logging.getLogger(__name__).addHandler(logging.NullHandler())

YKEY = config.Config.YKEY
ENDPOINT = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup?'

db = Database()
db.bind('sqlite', 'yappi.db', create_db=True)


class Record(db.Entity):
    request = Required(str)
    raw = Required(str)
    counter = Required(int)

db.generate_mapping(create_tables=True)


def answer_spellcheck(spellcheck, translate):
    if spellcheck:
        if not spellcheck.correct:
            if spellcheck.spellsafe:
                if translate:
                    return '    _Your request was corrected!_\n' + translate
                return '    _Your request was corrected!_\n'
    return translate


def prepare_message(msg):
    if not msg:
        return 'Your request is empty. Try again.'
    check = ' '.join(msg).replace('`', '')
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
        translate = get_word(msg)
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


def get_word(src):
    data = requests.get(
        ENDPOINT + requests.compat.urlencode(
            {'key': YKEY, 'lang': 'en-ru', 'text': src})
    )
    json_dump = data.json()
    if not json_dump['def']:
        return ''
    with db_session:
        if not exists(r for r in Record if r.request == src):
            Record(request=src, raw=data.text, counter=1)
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
            logging.exception(str(err))
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


@db_session
def guess():
    tmp = select(r for r in Record)[:]
    ind, source = random.choice(list(enumerate(tmp)))
    variants = random.sample(tmp[0:ind] + tmp[ind + 1:], 3)
    source = Word(json.loads(source.raw)).definitions[0]
    variants = [Word(json.loads(el.raw)).definitions[0].translition for el in variants]
    return source.text, source.translition, variants
