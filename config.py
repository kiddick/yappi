import os

import yaml

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'settings.yaml')) as ysttgs:
    settings = yaml.load(ysttgs)


class Config(object):
    DEBUG = settings['debug']
    BTOKEN = settings['bot_token']
    YKEY = settings['yandex_key']
