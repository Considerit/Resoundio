import hyperdiv as hd
from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db
from auth.auth_model import CurrentUser
import json

######################
# ACCESSORS
####################


######################
# SQL
####################

def create_aside_candidate(song_key, reaction_id, time_start, time_end=None, note=None):

    vals = {
        'id': uuid.uuid4().hex,
        'song_key': song_key,
        'reaction_id': reaction_id, 
        'user_id': CurrentUser().fetch()['user_id'], 
        'created_at': strftime('%s', 'now'),
        'time_start': time_start, 
        'time_end': time_end,
        'note': note,
        'votes': json.dumps( [vals['user_id']] )
    }

    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            INSERT INTO AsideCandidate 
                VALUES (:id, :song_key, :reaction_id, :user_id, :created_at, 
                        :note, :time_start, :time_end, :votes)
            """, vals)

    # AllAsideCandidates().clear()
    return vals


def get_aside_candidate(candidate_id):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            select *
            from AsideCandidate
            where id = ?
            """, 
            (candidate_id,)
        )
        return cursor.fetchall()


def get_aside_candidates(reaction_id):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM AsideCandidate
            WHERE reaction_id = ?
            """, (reaction_id,)
        )
        return cursor.fetchall()


def update_aside_candidate(candidate_id, time_start, time_end=None, note=None):
    with sqlite(db) as (_, cursor):
        cursor.execute(
            """
            UPDATE AsideCandidate SET
                time_start = ?,
                time_end = ?,
                note = ?
            WHERE id = ?
            """,
            (candidate_id, time_start, time_end, note),
        )


def delete_aside_candidate(candidate_id):
    candidate = get_aside_candidate(candidate_id)
    votes = json.loads(candidate['votes'])
    if not votes or len(votes) == 0 or (len(votes) == 1 and votes[0] == candidate['user_id'] == CurrentUser().fetch()['user_id']):
        with sqlite(db) as (_, cursor):
            cursor.execute(
                "DELETE from AsideCandidate where id = ?", (candidate_id,),
            )


######################
# HELPERS
####################



