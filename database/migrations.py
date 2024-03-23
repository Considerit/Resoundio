from hyperdiv.sqlite import sqlite, migrate, sql
from database.db import db

# Note: never delete or reorder a migration once its been applied
migrations = [
    sql(
        """
            CREATE TABLE User (
                user_id text primary key,
                name text,
                email text,
                created_at int,
                avatar_url text,
                password text,
                salt text,
                token text            
            );
        """
    ),
    sql(
        """
            CREATE TABLE Video (
                vid TEXT PRIMARY KEY,
                channel TEXT,
                channel_id TEXT,
                title TEXT,
                description TEXT,
                published_on INTEGER,
                views INTEGER,
                likes INTEGER,
                metrics_updated_at INTEGER,
                duration TEXT
            );
        """
    ),
    sql(
        """
            CREATE TABLE Song (
                vid TEXT PRIMARY KEY,
                song_key TEXT,
                status INTEGER,
                added_by TEXT,
                production_notes TEXT,
                FOREIGN KEY(vid) REFERENCES Video(vid),
                FOREIGN KEY(added_by) REFERENCES User(user_id)
            );
        """
    ),
    sql(
        """   
            CREATE INDEX song_key_index ON Song (song_key);
        """
    ),
    sql(
        """
            CREATE TABLE Reaction (
                vid TEXT PRIMARY KEY,
                song_key TEXT,
                channel TEXT,
                keypoints TEXT,
                FOREIGN KEY(vid) REFERENCES Video(vid),
                FOREIGN KEY(song_key) REFERENCES Song(song_key),
                FOREIGN KEY(channel) REFERENCES Video(channel)
            );
        """
    ),
    sql(
        """
            CREATE TABLE AsideCandidate (
                id TEXT,
                song_key TEXT,
                reaction_id TEXT,
                user_id TEXT,
                created_at INTEGER,
                note TEXT,
                time_start REAL,
                time_end REAL,
                base_anchor REAL,
                votes TEXT, 
                used_in_concert INTEGER DEFAULT 0,
                exported_at INTEGER,
                FOREIGN KEY(song_key) REFERENCES Song(song_key),
                FOREIGN KEY(reaction_id) REFERENCES Reaction(vid)
                FOREIGN KEY(user_id) REFERENCES User(user_id)
            );
        """
    ),
]


def migrate_db():
    migrate(db, migrations)
