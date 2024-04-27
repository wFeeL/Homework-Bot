import sqlite3

con = sqlite3.connect('../../database/homework_bot_database.sqlite', check_same_thread=False)
cur = con.cursor()


class NewHomework:
    def __init__(self, subject='', date='', description='', homework_id=''):
        self.subject = subject
        self.date = date
        self.description = description
        self.id = homework_id

    def apply_to_add(self):
        if self.subject != '' and self.date != '' and self.description != '':
            return True
        return False

    def apply_to_edit(self):
        homework = get_homework_by_id(self.id)[0]
        edited_homework = (self.subject, self.date, self.description)
        return True if homework != edited_homework else False


def get_homework_id(subject, date, description):
    subject_id = get_subject_id(subject)
    cur.execute("SELECT id FROM homework "
                f"WHERE subject_id = {subject_id} and date = '{date}' and description = '{description}'")
    return cur.fetchone()


def get_homework_by_id(homework_id):
    cur.execute("SELECT subject_id, date, description FROM homework "
                f"WHERE id = {homework_id}")
    return cur.fetchall()


def get_subjects():
    cur.execute('select name from subject '
                "where name not like '%/%' and id != 22 and id != 21 "
                "order by id")
    return cur.fetchall()


def get_subject_id(subject):
    cur.execute('SELECT id FROM subject '
                f"WHERE name = '{subject}'")
    return cur.fetchone()[0]


def get_homework(subject):
    cur.execute('SELECT s.id, s.name, h.date, h.description '
                'FROM homework AS h '
                'LEFT JOIN subject AS s '
                'ON h.subject_id = s.id '
                f"WHERE name = '{subject}' "
                'ORDER BY h.date')
    return cur.fetchall()


def add_data_to_database(subject_id, date, description):
    cur.execute(f"INSERT INTO homework (subject_id, date, description) "
                f"VALUES ({subject_id}, '{date}', '{description}')")
    con.commit()


def update_data(homework_id, date, description):
    cur.execute('UPDATE homework '
                f"SET date = '{date}', "
                f"description = '{description}' "
                f"WHERE id = {homework_id}")
    con.commit()


def delete_data(homework_id):
    cur.execute('DELETE FROM homework '
                f"WHERE id = {homework_id}")
    con.commit()


def add_user(user_telegram_id):
    if user_telegram_id not in get_users():
        cur.execute('INSERT INTO users (telegram_id) '
                    f'VALUES ({user_telegram_id})')
        con.commit()

    else:
        raise Exception


def delete_user(user_telegram_id):
    cur.execute('DELETE FROM users '
                f"WHERE telegram_id = '{user_telegram_id}'")
    con.commit()


def get_users():
    result = []
    cur.execute('SELECT telegram_id FROM USERS ')
    cur_result = cur.fetchall()

    for i in range(len(cur_result)):
        result.append(cur_result[i][0])

    return result
