from peewee import *

import config

DB_NAME = config.Config.DB_NAME

db = SqliteDatabase(DB_NAME)


class BaseModel(Model):

    class Meta:
        database = db


class Request(BaseModel):
    content = CharField(default='')
    raw = CharField(default='')
    counter = IntegerField(default=1)

    @classmethod
    def find_request(self, content):
        try:
            return Request.get(Request.content == content)
        except DoesNotExist:
            return None

    @classmethod
    def create(self, content, raw):
        request = Request.find_request(content)
        if not request:
            with db.transaction():
                new_request = Request(content=content, raw=raw)
                new_request.save()
            return new_request
        else:
            with db.transaction():
                request.counter += 1
                request.save()
            return request


def create_tables():
    with db.transaction():
        for model in [Request]:
            if not model.table_exists():
                db.create_table(model)

create_tables()
