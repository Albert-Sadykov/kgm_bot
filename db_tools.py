from connection import connection


def create_user(id, username, name, category, connection=connection):
    with connection() as conn:
        cur = conn.cursor()

        cur.execute("insert into users (id, username, name, is_signed, has_key) values (?, ?, ?, ?, ?)",
                    (id, username, name, True, True))
        conn.commit()

    set_category(id=id, category=category)

def update_has_key(id):
    with connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET has_key =? WHERE id =?", (True, id))
        conn.commit()

def get_has_key(user_id, connection=connection):
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT has_key FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def user_exist(id, connection=connection):
    with connection() as conn:
        user = conn.cursor().execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
        return user is not None


def upload_users(category, connection=connection):
    with connection() as conn:
        users = conn.cursor().execute("""SELECT users.id, users.username, users.name, users.is_signed
                                        FROM users
                                        JOIN users_category ON users.id = users_category.id
                                        WHERE users_category.category = ?""", (category,)).fetchall()
        return users


def categories_exist(id, connection=connection):
    with connection() as conn:
        ctg = conn.cursor().execute('SELECT * FROM users_category WHERE (id) = (?)', (id,)).fetchone()
        return ctg is not None


def category_exist(id, category, connection=connection):
    with connection() as conn:
        ctg = conn.cursor().execute('SELECT * FROM users_category WHERE (id, category) = (?, ?)',
                                    (id, category,)).fetchone()
        return ctg is not None


def set_category(id, category, connection=connection):
    with connection() as conn:
        categories = conn.cursor().execute('SELECT category FROM users_category WHERE id = ?', (id,)).fetchall()
        if (category,) not in categories:
            conn.cursor().execute("insert into users_category (id, category) values (?, ?)", (id, category,))
            conn.commit()


def add_category(id, category, connection=connection):
    with connection() as conn:
        if not category_exist(id, category):
            conn.cursor().execute("insert into users_category (id, category) values (?, ?)", (id, category,))
            conn.commit()
            return True
        return False


def delete_category(id, category):
    with connection() as conn:
        if category_exist(id, category):
            conn.cursor().execute("delete from users_category where (id, category) = (?, ?)", (id, category,))
            conn.commit()


def get_user_by_user_id(user_id, connection=connection):
    with connection() as conn:
        user = conn.cursor().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return user


def get_categories_str(id, connection=connection):
    with connection() as conn:
        categories = conn.cursor().execute('SELECT category FROM users_category WHERE id = ?', (id,)).fetchall()
        return ', '.join(map(lambda s: str(s).title(), [category[0] for category in categories]))


def set_is_signed(user_id, value: bool, connection=connection):
    with connection() as conn:
        conn.cursor().execute("update users set is_signed=(?) where id=(?)", (value, user_id,))
        conn.commit()


def get_is_signed(user_id, connection=connection):
    with connection() as conn:
        users = conn.cursor().execute('SELECT is_signed FROM users WHERE id = ?', (user_id,)).fetchone()
        return users


def set_photo_menu(tag, file_id, connection=connection):
    with connection() as conn:
        exist = conn.cursor().execute('SELECT * FROM menu_photos WHERE tag = ?', (tag,)).fetchone()

        if exist is not None:
            conn.cursor().execute("update menu_photos set file_id=(?) where tag=(?)", (file_id, tag,))
        else:
            conn.cursor().execute("insert into menu_photos (tag, file_id) values (?, ?)", (tag, file_id,))
        conn.commit()


def get_tag(id, connection=connection):
    with connection() as conn:
        categories = conn.cursor().execute("select category from users_category where id=?", (id,)).fetchall()
        return '_'.join(map(lambda s: str(s), sorted([category[0] for category in categories])))


def get_photo_menu(id, connection=connection):
    tag = get_tag(id)
    with connection() as conn:
        file_id = conn.cursor().execute('SELECT file_id FROM menu_photos WHERE tag = ?', (tag,)).fetchone()
        return file_id


def get_raffles_by_status(status):
    with connection() as conn:
        raffles = conn.cursor().execute('SELECT * FROM raffles WHERE status = ?', (status,)).fetchall()
        return raffles

def get_raffles_for_user():
    with connection() as conn:
        raffles = conn.cursor().execute('SELECT * FROM raffles ORDER BY status').fetchall()
        return raffles

def get_raffle(raffle_id, connection=connection):
    with connection() as conn:
        raffles = conn.cursor().execute('SELECT * FROM raffles WHERE id = ?', (raffle_id,)).fetchone()
        return raffles


def get_raffle_participant(raffle_id, user_id, connection=connection):
    with connection() as conn:
        raffle_participant = conn.cursor().execute(
            'SELECT * FROM raffles_participants WHERE raffle_id = ? AND user_id = ?',
            (raffle_id, user_id)).fetchone()
        return raffle_participant


def get_raffle_participants(raffle_id, connection=connection):
    with connection() as conn:
        raffle_participants = conn.cursor().execute(
            'SELECT user_id FROM raffles_participants WHERE raffle_id = ?',
            (raffle_id,)).fetchall()
        return raffle_participants


def set_finish_raffle(raffle_id):
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("update raffles set status='finish' where id = ?", (raffle_id,))
        conn.commit()
        cursor.close()

def get_winners(raffle_id, connection=connection):
    with connection() as conn:
        cursor = conn.cursor()
        winners = cursor.execute(
            'SELECT username FROM raffles_participants LEFT JOIN users ON users.id = raffles_participants.user_id WHERE raffle_id = ? AND is_winner = TRUE',
            (raffle_id,)).fetchall()
        return winners

def set_winners(raffle_id, winners, connection=connection):
    with connection() as conn:
        cursor = conn.cursor()
        placeholder = ', '.join('?' for _ in winners)
        print(placeholder)
        cursor.execute(
            f"update raffles_participants set is_winner=TRUE where user_id in ({placeholder}) and raffle_id = ?",
            (*winners, raffle_id))
        conn.commit()
        cursor.close()


def create_raffle_participant(raffle_id, user_id, connection=connection):
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("insert into raffles_participants (raffle_id, user_id) values (?, ?)", (raffle_id, user_id))
        conn.commit()
        cursor.close()


def db_create_raffle(raffle, connection=connection):
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "insert into raffles (status, photo, name, description, winners_count, end_time) values ('active', ?,?,?,?,?)",
            (raffle['photo'], raffle['name'], raffle['description'], raffle['winners_count'], raffle['end_time']))

        conn.commit()
        raffle_id = cursor.lastrowid
        cursor.close()
        return raffle_id
