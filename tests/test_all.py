# -*- coding: utf-8 -*-
from unittest import TestCase, main
from unittest.mock import patch, MagicMock, call
from playhouse.test_utils import test_database
from peewee import *

from yappi import translate
from models import CallbackEntity, Request, User, Chat, FirstRequest, Message
import exceptions
db = SqliteDatabase(':memory:')


class TestModels(TestCase):

    @db.atomic()
    def test_create_user(self):
        with test_database(db, (User,)):
            user, created = User.get_or_create(tid=1, name='name')
            self.assertTrue(created)
            user2, created = User.get_or_create(tid=1, name='name')
            self.assertFalse(created)
            self.assertEqual(len(User.select().where(User.tid == 1)), 1)

    @db.atomic()
    def test_create_chat(self):
        with test_database(db, (Chat,)):
            chat, created = Chat.get_or_create(chat_id=1)
            self.assertTrue(created)
            chat2, created = Chat.get_or_create(chat_id=1)
            self.assertFalse(created)
            self.assertEqual(len(Chat.select().where(Chat.chat_id == 1)), 1)

    @db.atomic()
    def test_create_request(self):
        with test_database(db, (Request,)):
            request = Request.create(content='test', raw='{"def": "test"}')
            self.assertEqual(request.content, 'test')
            self.assertEqual(request.raw, '{"def": "test"}')
            self.assertEqual(request.counter, 1)

    @db.atomic()
    def test_get_request(self):
        with test_database(db, (Request,)):
            # check when table is empty
            request_query = Request.get_request(content='test')
            self.assertIsNone(request_query)

            # check when only 1 unique record exists
            Request.create(content='test', raw='{"def": "test"}')
            request_query = Request.get_request(content='test')
            self.assertEqual(request_query.raw, '{"def": "test"}')
            self.assertEqual(request_query.counter, 2)

            # check when duplicates exist
            Request.create(content='test', raw='{"def": "test"}')
            with self.assertRaises(exceptions.MultipleRecords) as context:
                request_query = Request.get_request(content='test')

    @db.atomic()
    def test_create_message(self):
        with test_database(db, (Chat, User, Request, Message)):
            user, _ = User.get_or_create(tid=1, name='name')
            chat, _ = Chat.get_or_create(chat_id=1)
            request = Request.create(content='test', raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, request=request, message_id=1, time=1)
            self.assertEqual(message.chat.chat_id, 1)
            self.assertEqual(message.user.tid, 1)
            self.assertEqual(message.request.content, 'test')
            self.assertEqual(message.message_id, 1)
            self.assertEqual(message.time, 1)

    @db.atomic()
    def test_create_first_request(self):
        with test_database(db, (Chat, User, Request, Message, FirstRequest)):
            user, _ = User.get_or_create(tid=1, name='name')
            chat, _ = Chat.get_or_create(chat_id=1)
            request = Request.create(content='test', raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, request=request, message_id=1, time=1)
            first_request = FirstRequest.create(
                request=request, chat=chat, user=user, message=message)
            self.assertEqual(first_request.chat.chat_id, 1)
            self.assertEqual(first_request.user.tid, 1)
            self.assertEqual(first_request.request.content, 'test')
            self.assertEqual(first_request.message_id, 1)

            # check uniqueness of first request by user
            with self.assertRaises(IntegrityError) as context:
                first_request = FirstRequest.create(
                    request=request, chat=chat, user=user, message=message)


class TestTranslate(TestCase):

    @db.atomic()
    # @patch('yappi.updater.bot')
    # @patch('yappi.updater.bot')
    def test_translate(self):
        with test_database(db, (Chat, User, Request, Message, FirstRequest)):
            content = 'test'
            user = User.create(tid=1, name='name')
            chat = Chat.create(chat_id=1)
            # request = Request.create(content=content, raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, message_id=1, time=1)
            bot = MagicMock()
            # reply = MagicMock(side_effect=lambda x: x)
            reply = MagicMock()

            # test with empty content
            response = translate(
                content='',
                user=user,
                chat=chat,
                message=message,
                bot=bot,
                reply=reply
            )

            # print(response, '!!', reply, reply.side_effect, reply.call_count, reply.return_value, reply.mock_calls)
            print(response, '!!', reply.call_count, reply.mock_calls)
            print(reply.call_args)
            reply('test')
            print(reply.call_args)
            print(reply.call_args == call('test'))
