import hyperdiv as hd
from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db


######################
# ACCESSORS
####################

@hd.global_state
class AllReactions(hd.task):
    def run(self):
        super().run(get_reactions)

    def fetch(self):
        self.run()
        return self.result



######################
# SQL
####################


def get_reaction(vid):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select * from Reaction
            where vid = ?
            """,
            (vid),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None


def get_reactions_by_song(song):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select *
            from Reaction
            where song_key = ?
            """, (song)
        )
        return cursor.fetchall()



######################
# HELPERS
####################


