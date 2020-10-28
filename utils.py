import datetime, sqlite3, pickle, codecs

from math import trunc


class User:
    def __init__(self):
        self.chat_id = None
        self.name = None
        self.age = None
        self.patronymic = None
        self.surname = None
        self.phone = None
        self.status = [None, None]

# Вспомогательные функции, которые не взаимодействуют с БД

def fcs_validator(text):
    """Валидатор ФИО"""
    arr = text.split()
    if len(arr) == 3:
        for title in arr:
            if title.isalpha() and len(title) > 1:
                return True
    return False

def count_age(text):
    """Функция подсчета возраста по дате рождения"""
    today = datetime.datetime.now().date()
    birth_date = datetime.datetime.strptime(text, '%d.%m.%Y').date()
    age = trunc((today-birth_date).days//365.25)
    return age

def birth_date_validator(text):
    """Валидатор даты рождения"""
    try:
        age = count_age(text)
        if age >= 1:
            return True
        return False
    except ValueError:
        return False

# Вспомогательные функции, которые взаимодействуют с БД

def phone_number_validation(text):
    """Валидатор номера телефона"""
    response = [False, False] # [0] - valid, [1] - unique
    if text.isdigit():
        if len(text) > 7 and len(text) < 20:
            response[0] = True
            phone = text
            conn = sqlite3.connect('main_db.sqlite3')
            cursor = conn.cursor()
            cursor.execute('SELECT "PHONE" FROM "BotUser" ORDER BY "ID"')
            results = cursor.fetchall()
            if results:
                for row in results:
                    if phone in row:
                        return response
                response[1] = True
                return response
            else:
                response[1] = True
                return response
    return response

def exist_user(chat_id):
    """Функция, которая проверяет наличие пользователя с таким chat.id в бд. Если его нет - возвращает False,
       если он есть - возвращает инстанс класса User
    """
    conn = sqlite3.connect('main_db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT "TGID", "BotUser"."DUMP" FROM "BotUser" ORDER BY "ID"')
    results = cursor.fetchall()
    if results:
        for row in results:
            if chat_id in row:
                unpickled = pickle.loads(codecs.decode(row[1].encode(), "base64"))
                return unpickled
    else:
        return False
    conn.close()

def user_status(phone):
    """Функция, которая запрашивает в БД информацию о ранге."""
    response = ["Unranked", None]
    conn = sqlite3.connect('main_db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT "PHONE", "RankStatus"."STATUS", "RankStatus"."ID" FROM "GrantUsers" INNER JOIN "RankStatus" ON ("GrantUsers"."STATUS_ID"="RankStatus"."ID")')
    results = cursor.fetchall()
    for row in results:
        if phone in row:
            response[0] = row[1]
            response[1] = row[2]
    if response[1] is None:
        cursor.execute('SELECT "ID" FROM "RankStatus" WHERE "STATUS"="Unranked"')
        row = cursor.fetchone()
        response[1] = row[0]
    conn.close()
    return response

def add_user_db(user):
    """
    Функция, которая вносит пользователя в бд, вместе с сериализованым инстансом класса User.
    """
    dump = codecs.encode(pickle.dumps(user), "base64").decode()

    user_data = (user.name, user.patronymic, user.surname, user.age, user.phone, user.chat_id, user.status[1], dump)

    conn = sqlite3.connect('main_db.sqlite3')
    cursor = conn.cursor()

    try:
        sql_expr = 'INSERT INTO "BotUser" ("NAME", "PATRONYMIC", "SURNAME", "AGE", "PHONE", "TGID", "STATUS_ID", "DUMP") VALUES (?,?,?,?,?,?,?,?);'
        cursor.execute(sql_expr, user_data)
    except Exception as e:
        conn.close()
    else:
        conn.commit()
        conn.close()
