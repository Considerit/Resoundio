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
            SELECT * FROM Song
            WHERE vid = ?
            """,
            (vid,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None



def get_songs():
    with sqlite(db) as (_, cursor):
        cursor.execute(
            "SELECT * FROM Song"
        )
        return cursor.fetchall()

def update_production_notes(song_key, value):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            UPDATE Song SET
                production_notes = ?
            WHERE song_key = ?
            """,
            (value, song_key),
        )
    AllSongs().clear()




######################
# HELPERS
####################



