import uuid
import bcrypt
import hyperdiv as hd
from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db


######################
# ACCESSORS
####################

@hd.global_state
class AllUsers(hd.task):
    def run(self):
        super().run(get_users)

    def fetch(self):
        self.run()
        return self.result


######################
# SQL
####################

def create_user(name, email, password=None, avatar_url=None, token=None):
    if get_user_by_email(email):
        raise Exception(f"Email {email} is already being used")

    if password is None: 
        password = uuid.uuid4().hex

    password, salt = gen_salted_password(password)

    if token is None:
        token = uuid.uuid4().hex


    user_id = uuid.uuid4().hex
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            INSERT INTO User (
                user_id, name, email, password, avatar_url, created_at, salt, token
            ) VALUES (
                ?, ?, ?, ?, ?, strftime('%s', 'now'), ?, ?
            )
            """,
            (user_id, name, email, password, avatar_url, salt, token),
        )
    AllUsers().clear()
    return user_id


def get_user(user_id):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM User
            WHERE user_id = ?
            """,
            (user_id,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None

def get_user_by_email(email):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM User
            WHERE email = ?
            """,
            (email,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None

def get_user_by_token(token):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM User
            WHERE token = ?
            """,
            (token,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None


def get_users():
    with sqlite(db) as (_, cursor):
        cursor.execute(
            "SELECT * FROM User"
        )
        return cursor.fetchall()

def get_subset_of_users(users):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            f"""
            SELECT *
            FROM User
            WHERE user_id IN ({','.join(['?']*len(users))})
            """,
            users
        )
        return cursor.fetchall()


######################
# HELPERS
####################

def gen_salted_password(passwd):
    passwd_bytes = passwd.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_passwd = bcrypt.hashpw(passwd_bytes, salt)
    return hashed_passwd.decode("utf-8"), salt.decode("utf-8")




