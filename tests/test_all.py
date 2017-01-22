# -*- coding: utf-8 -*-
import json

from unittest import TestCase, main
from unittest.mock import patch, MagicMock, call
from playhouse.test_utils import test_database
from peewee import *

import exceptions
import yadict

from yappi import translate
from models import CallbackEntity, Request, User, Chat, FirstRequest, Message
from templates import MessageTemplate


db = SqliteDatabase(':memory:')

ORIGINAL = {
    'load_content_from_db': yadict.load_content_from_db,
}


def wrapped_load_content_from_db(request):
    return ORIGINAL['load_content_from_db'](request)


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
    @patch('yadict.load_content_from_db')
    @patch('yadict.format_dict_message')
    @patch('yadict.dicservice_request')
    def test_translate(self, dicservice_request, format_dict_message, load_content_from_db):
        with test_database(db, (Chat, User, Request, Message, FirstRequest)):
            content = 'test'
            user = User.create(tid=1, name='name')
            chat = Chat.create(chat_id=1)
            # request = Request.create(content=content, raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, message_id=1, time=1)
            bot = MagicMock()
            reply = MagicMock()
            def dummy_reply(_):
                reply_message = MagicMock()
                reply_message.message_id = 2
                return reply_message
            reply.side_effect = dummy_reply
            # print(reply.message_id)

            # test with empty content
            translate(
                content='',
                user=user,
                chat=chat,
                message=message,
                bot=bot,
                reply=reply
            )
            reply.assert_called_with(MessageTemplate.EMPTY_REQUEST)

            # test with tilde
            translate(
                content='```',
                user=user,
                chat=chat,
                message=message,
                bot=bot,
                reply=reply
            )
            reply.assert_called_with(MessageTemplate.ONLY_TILDE)

            def dummy_dicservice(_):
                response_mock = MagicMock()
                response_raw = '{"def": "test"}'
                response_mock.json = lambda: json.loads(response_raw)
                response_mock.text = response_raw
                return response_mock

            dicservice_request.side_effect = dummy_dicservice
            format_dict_message.side_effect = lambda x: x

            # test with no request in db
            translate(
                content=content,
                user=user,
                chat=chat,
                message=message,
                bot=bot,
                reply=reply
            )
            reply.assert_called_with(content)
            request_query = Request.get_request(content='test')
            self.assertEqual(len(Request.select()), 1)
            self.assertEqual(request_query.raw, '{"def": "test"}')

            # request and first request were created
            # so we need to remove first request

            # print(len(FirstRequest.select()))
            FirstRequest.delete().execute()
            load_content_from_db.side_effect = wrapped_load_content_from_db
            # print(len(FirstRequest.select()))

            # test with existing request in db
            translate(
                content=content,
                user=user,
                chat=chat,
                message=message,
                bot=bot,
                reply=reply
            )
            self.assertTrue(load_content_from_db.called)
            # load_content_from_db.assert_called_with(content)
            reply.assert_called_with(content)
            request_query = Request.get_request(content='test')
            self.assertEqual(len(Request.select()), 1)
            self.assertEqual(request_query.raw, '{"def": "test"}')

            def dummy_send_message(*args, **kwargs):
                return kwargs['reply_to_message_id']
            # bot.send_message = dummy_send_message
            bot.send_message = MagicMock()

            # test with existing first request
            translate(
                content=content,
                user=user,
                chat=chat,
                message=message,
                bot=bot,
                reply=reply
            )
            reply.assert_called_with(MessageTemplate.ALREADY_REQUESTED)
            # fr_query, _ = FirstRequest.get_first_request_and_request(
                    # chat=chat, user=user, content=content)
            # args, kwargs = bot.send_message.call_args
            reply_to_message_id = bot.send_message.call_args[1]['reply_to_message_id']
            self.assertEqual(reply_to_message_id, 2)


            # print(kwargs)
            # print(bot.send_message.mock_calls[0][2])
            # print(bot.send_message.call_args)
            # print(bot.send_message.call_args_list)
            # print(len(bot.send_message.call_args))
            # bot.send_message.assert_called_with(MessageTemplate.ALREADY_REQUESTED)
