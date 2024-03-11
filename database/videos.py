import hyperdiv as hd
from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db


######################
# ACCESSORS
####################

@hd.global_state
class AllVideos(hd.task):
    def run(self):
        super().run(get_videos)

    def fetch(self):
        self.run()
        return self.result



######################
# SQL
####################


def get_video(vid):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select * from Video
            where vid = ?
            """,
            (vid,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None



def get_videos():
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select *
            from Video
            """
        )
        return cursor.fetchall()



######################
# HELPERS
####################



