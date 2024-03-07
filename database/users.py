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
        salt = bcrypt.gensalt()
    else: 
        password, salt = gen_salted_password(password)

    if token is None:
        token = uuid.uuid4().hex


    user_id = uuid.uuid4().hex
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            insert into User (
                user_id, name, email, password, avatar_url, created_at, salt, token
            ) values (
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
            select * from User
            where user_id = ?
            """,
            (user_id,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None

def get_user_by_email(email):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select * from User
            where email = ?
            """,
            (email,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None

def get_user_by_token(token):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select * from User
            where token = ?
            """,
            (token,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None


def get_users():
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select *
            from User
            """
        )
        return cursor.fetchall()


# def save_user(user_id, note_title, note_body):
#     with sqlite(db) as (_, cursor):
#         cursor.execute(
#             """
#             update Note set
#                 note_body = ?,
#                 note_title = ?,
#                 ts = strftime('%s', 'now')
#             where user_id = ?
#             """,
#             (note_body, note_title, user_id),
#         )


# def delete_user(user_id):
#     with sqlite(db) as (_, cursor):
#         cursor.execute(
#             """
#             delete from Note where user_id = ?
#             """,
#             (user_id,),
#         )


######################
# HELPERS
####################

def gen_salted_password(passwd):
    """
    This function is unused in the app but was used to generate the
    hashed password and salt stored for each user in the
    'database'. Here for reference.
    """

    # Encode password to bytes
    passwd_bytes = passwd.encode("utf-8")

    # Generate salt
    salt = bcrypt.gensalt()

    # Hash the password with the salt
    hashed_passwd = bcrypt.hashpw(passwd_bytes, salt)

    # Return the hashed password and salt both as decoded strings
    return hashed_passwd.decode("utf-8"), salt.decode("utf-8")



######################
# MIGRATIONS
####################

# Never delete a migration once its been applied
migrations = [
    sql(
        """
        create table User (
            user_id text primary key,
            name text,
            email text,
            created_at int,
            avatar_url text,
            password text,
            salt text,
            token text            
        )
        """
    )
]
