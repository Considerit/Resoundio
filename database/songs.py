import hyperdiv as hd

from hyperdiv.sqlite import sqlite, migrate, sql

from database.db import db


######################
# ACCESSORS
####################

@hd.global_state
class AllSongs(hd.task):
    def run(self):
        super().run(get_songs)

    def fetch(self):
        self.run()
        return self.result



######################
# SQL
####################


def get_song(vid):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select * from Song
            where vid = ?
            """,
            (vid,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None



def get_songs():
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select *
            from Song
            """
        )
        return cursor.fetchall()


######################
# HELPERS
####################



