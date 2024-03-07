from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db

from database.users import migrations as users_migrations

all_migrations = []
for migrations in [users_migrations]:
    all_migrations += users_migrations


def migrate_db():
    migrate(db, all_migrations)
