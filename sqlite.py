import sqlite3 as sq
from dictor import users


async def sql_start():
    global base, cur
    base = sq.connect('bot_users.db')
    cur = base.cursor()
    if base:
        print('База данных подключена')
    base.execute('CREATE TABLE IF NOT EXISTS ids(user_id integer PRIMARY KEY)')
    base.commit()


async def sql_add_user(user_id):
    cur.execute("INSERT INTO ids VALUES (?)", (user_id,))
    base.commit()
