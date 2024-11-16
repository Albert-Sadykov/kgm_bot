import sqlite3
from contextlib import contextmanager


@contextmanager
def connection():
    conn = sqlite3.connect('database.db')
    try:
        yield conn
    finally:
        conn.close()


with connection() as conn:
    cur = conn.cursor()
    cur.execute("create table if not exists users(id INTEGER, username STRING, name STRING, is_signed BOOL)")
    cur.execute(
        "create table if not exists users_category(id INTEGER, category STRING)")
    cur.execute(
        "create table if not exists menu_photos(tag INTEGER, file_id STRING)")
    cur.execute(
        "create table if not exists raffles(id integer primary key autoincrement, photo STRING, name STRING,description STRING, winners_count INTEGER, status STRING, end_time STRING)"
    )
    cur.execute(
        "create table if not exists raffles_participants(raffle_id INTEGER, user_id INTEGER, is_winner BOOL DEFAULT FALSE)"
    )
