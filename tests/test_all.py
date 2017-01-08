from unittest import TestCase, main
from unittest.mock import patch, MagicMock
from playhouse.test_utils import test_database
from peewee import *

from models import CallbackEntity, Request, User, Chat, FirstRequest

test_db = SqliteDatabase(':memory:')


class TestModelCreation(TestCase):

    def test_create_user(self):
        with test_database(test_db, (User,)):
            user, created = User.get_or_create(tid=1, name='name')
            self.assertTrue(created)
            user2, created = User.get_or_create(tid=1, name='name')
            self.assertFalse(created)
            self.assertEqual(len(User.select().where(User.tid == 1)), 1)

    def test_create_chat(self):
        with test_database(test_db, (User,)):
            chat, created = Chat.get_or_create(chat_id=1)
            self.assertTrue(created)
            chat2, created = Chat.get_or_create(chat_id=1)
            self.assertFalse(created)
            self.assertEqual(len(Chat.select().where(Chat.chat_id == 1)), 1)
