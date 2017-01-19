from peewee import *

import config
import exceptions

DB_NAME = config.Config.DB_NAME

db = SqliteDatabase(DB_NAME)


class BaseModel(Model):

    class Meta:
        database = db


class User(BaseModel):
    tid = IntegerField(unique=True)
    name = CharField()


class Chat(BaseModel):
    chat_id = IntegerField(default=0)


class CallbackEntity(BaseModel):
    data = CharField()

    @classmethod
    def create(cls, **query):
        inst = super().create(**query)
        return inst.id

    @classmethod
    def get_callback(cls, index):
        query = CallbackEntity.select().where(CallbackEntity.id == index)
        if not query:
            return
        data = query[0].data
        query[0].delete_instance()
        return data


class Request(BaseModel):
    content = CharField(default='')
    raw = CharField(default='')
    counter = IntegerField(default=1)

    @classmethod
    @db.atomic()
    def get_request(cls, content):
        query = Request.select().where(Request.content == content.lower())
        if not query:
            return
        if len(query) > 1:
            raise exceptions.MultipleRecords
        query[0].counter += 1
        query[0].save()
        return query[0]

    @classmethod
    def statistics(cls):  # TODO Fix this method
        subquery = (Request
                    .select(fn.COUNT(Request.id))
                    .where(Request.user == User.id))
        query = (User
                 .select(User, Request, subquery.alias('request_count'))
                 .join(Request, JOIN.LEFT_OUTER)
                 .order_by(User.tid))

        # for user in query.aggregate_rows():
        #     print(user.name, user.request_count)\

        return {user.name: user.request_count
                for user in query.aggregate_rows()}


class Message(BaseModel):
    chat = ForeignKeyField(Chat, related_name='chat', db_column='chat')
    user = ForeignKeyField(User, related_name='user', db_column='user')
    request = ForeignKeyField(Request, related_name='request', db_column='request', default=0)
    message_id = IntegerField(default=0)
    time = IntegerField(default=0)


class FirstRequest(BaseModel):
    request = ForeignKeyField(Request, related_name='fr_request', db_column='request')
    chat = ForeignKeyField(Chat, related_name='fr_chat', db_column='chat')
    user = ForeignKeyField(User, related_name='fr_user', db_column='user', unique=True)
    message = ForeignKeyField(Message, related_name='fr_message', db_column='message')

    @classmethod
    def get_first_request(cls, content, chat, user):
        request = Request.get_request(content=content)
        if not request:
            return
        query = (FirstRequest
                 .select()
                 .where(
                     (FirstRequest.request == request.id) &
                     (FirstRequest.chat == chat.id) &
                     (FirstRequest.user == user.id))
                 )
        if not query:
            return
        return query[0]


def create_tables():
    with db.transaction():
        for model in [CallbackEntity, Request, User, Chat, FirstRequest, Message]:
            if not model.table_exists():
                db.create_table(model)

create_tables()
