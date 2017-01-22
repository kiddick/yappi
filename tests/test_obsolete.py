# -*- coding: utf-8 -*-
from unittest import TestCase, main
from unittest.mock import patch, MagicMock
from playhouse.test_utils import test_database
from peewee import *

from models import CallbackEntity, Request, User, Chat, FirstRequest, Message
db = SqliteDatabase(':memory:')


class TestObsolete(TestCase):

    @db.atomic()
    def test_get_first_request(self):
        with test_database(db, (Chat, User, Request, Message, FirstRequest)):
            user, _ = User.get_or_create(tid=1, name='name')
            chat, _ = Chat.get_or_create(chat_id=1)
            request = Request.create(content='test', raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, request=request, message_id=1, time=1)

            # check when table is empty
            ##
            FirstRequest.create(
                request=request, chat=chat, user=user, message=message)
            ##
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user, content='test')
            self.assertIsNone(fr_request_query)

            # check when first request exists
            FirstRequest.create(
                request=request, chat=chat, user=user, message=message)
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user, request=request)
            self.assertEqual(fr_request_query.request, request)
            self.assertEqual(fr_request_query.user, user)
            self.assertEqual(fr_request_query.chat, chat)

            # check with another user
            user2, _ = User.get_or_create(tid=2, name='name2')
            Message.create(
                chat=chat, user=user2, request=request, message_id=2, time=2)
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user2, request=request)
            self.assertIsNone(fr_request_query)

            # check with another chat
            chat2, _ = Chat.get_or_create(chat_id=2)
            Message.create(
                chat=chat2, user=user, request=request, message_id=3, time=3)
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user2, request=request)
            self.assertIsNone(fr_request_query)

            # check with another request
            request2 = Request.create(content='test2', raw='{"def": "test2"}')
            Message.create(
                chat=chat, user=user, request=request2, message_id=4, time=4)
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user, request=request2)
            self.assertIsNone(fr_request_query)

    @db.atomic()
    def test_tranlate_db_logic(self):
        with test_database(db, (Chat, User, Request, Message, FirstRequest)):
            user, _ = User.get_or_create(tid=1, name='name')
            chat, _ = Chat.get_or_create(chat_id=1)
            request, created = Request.get_or_create(
                content='test', raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, message_id=1, time=1)
            self.assertTrue(created)

            # check when there is no first request
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user, content='test')
            self.assertIsNone(fr_request_query)

            message.request = request
            message.save()
            self.assertEqual(message.request, request)

            first_request = FirstRequest.create(
                request=request, chat=chat, user=user, message=message)
            self.assertEqual(first_request.message, message)

            # not created
            fr_request_query = FirstRequest.get_first_request(
                chat=chat, user=user, content='test')
            self.assertIsNotNone(fr_request_query)
            self.assertEqual(fr_request_query.message, message)

    @db.atomic()
    def test_ss(self):
        with test_database(db, (Chat, User, Request, Message, FirstRequest)):
            user, _ = User.get_or_create(tid=1, name='name')
            chat, _ = Chat.get_or_create(chat_id=1)
            request = Request.create(content='test', raw='{"def": "test"}')
            message = Message.create(
                chat=chat, user=user, request=request, message_id=1, time=1)
