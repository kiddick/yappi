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

    @classmethod
    def create(cls, **query):
        user_query = User.select().where(User.tid == query['tid'])
        if not user_query:
            return super().create(**query)
        else:
            return user_query[0]


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
    user = ForeignKeyField(User, related_name='user_requests', db_column='user')

    @classmethod
    def get_request(cls, content):
        with db.transaction():
            query = Request.select().where(Request.content == content.lower())
            if not query:
                return
            if len(query) > 1:
                raise exceptions.MultipleRecords
            query[0].counter += 1
            query[0].save()
            return query[0]

    @classmethod
    def statistics(cls):
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


def create_tables():
    with db.transaction():
        for model in [CallbackEntity, Request, User]:
            if not model.table_exists():
                db.create_table(model)

create_tables()
