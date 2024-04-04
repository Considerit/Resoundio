import hyperdiv as hd
from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db
from auth.auth_model import CurrentUser
import json
import uuid
import time


######################
# ACCESSORS
####################

aside_candidates_by_song_key = {}


def asides_for_song(song_key, new_task=False):
    if new_task or song_key not in aside_candidates_by_song_key:
        tsk = hd.task()
        tsk.run(get_aside_candidates_for_song, song_key)
        aside_candidates_by_song_key[song_key] = tsk

    return aside_candidates_by_song_key[song_key]


######################
# SQL
####################


def create_aside_candidate(
    song_key, reaction_id, time_start, base_anchor, time_end=None, note=None
):
    user_id = CurrentUser().fetch()["user_id"]
    vals = {
        "id": uuid.uuid4().hex,
        "song_key": song_key,
        "reaction_id": reaction_id,
        "user_id": user_id,
        "created_at": int(time.time()),
        "time_start": time_start,
        "time_end": time_end,
        "base_anchor": base_anchor,
        "note": note,
        "votes": json.dumps([user_id]),
        "used_in_concert": False,
        "exported_at": 0,
    }

    print("INSERTING ASIDE CANDIDATE", vals)
    print(base_anchor, type(base_anchor))

    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            INSERT INTO AsideCandidate 
                VALUES (:id, :song_key, :reaction_id, :user_id, :created_at, 
                        :note, :time_start, :time_end, :base_anchor,
                        :votes, :used_in_concert, :exported_at)
            """,
            vals,
        )

    asides_for_song(song_key).clear()

    return vals


def get_aside_candidate(candidate_id):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select *
            from AsideCandidate
            where id = ?
            """,
            (candidate_id,),
        )
        results = cursor.fetchall()
        return results[0] if len(results) > 0 else None


def get_aside_candidates(reaction_id):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM AsideCandidate
            WHERE reaction_id = ?
            """,
            (reaction_id,),
        )
        return cursor.fetchall()


def get_aside_candidates_for_song(song_key):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM AsideCandidate
            WHERE song_key = ?
            """,
            (song_key,),
        )
        return cursor.fetchall()


def update_aside_candidate(
    candidate_id, time_start, base_anchor, time_end=None, note=None
):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            UPDATE AsideCandidate SET
                time_start = ?,
                time_end = ?,
                base_anchor= ?,
                note = ?
            WHERE id = ?
            """,
            (time_start, time_end, base_anchor, note, candidate_id),
        )

    candidate = get_aside_candidate(candidate_id)
    asides_for_song(candidate["song_key"]).clear()


def delete_aside_candidate(candidate_id):
    candidate = get_aside_candidate(candidate_id)

    votes = json.loads(candidate["votes"])
    if (
        not votes
        or len(votes) == 0
        or (
            len(votes) == 1
            and votes[0] == candidate["user_id"] == CurrentUser().fetch()["user_id"]
        )
    ):
        with sqlite(db) as (_, cursor):
            cursor.execute(
                "DELETE from AsideCandidate where id = ?",
                (candidate_id,),
            )

    asides_for_song(candidate["song_key"]).clear()


######################
# HELPERS
####################
