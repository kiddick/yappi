from playhouse.migrate import *

import config
from models import User

DB_NAME = config.Config.DB_NAME

db = SqliteDatabase(DB_NAME)
migrator = SqliteMigrator(db)

user = User.create(tid=69137762, name='ring!')

user_field = ForeignKeyField(
    User, related_name='user_requests', to_field=User.id, default=user.id)

migrate(
    migrator.add_column('request', 'user', user_field),
)
