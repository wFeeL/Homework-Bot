import sqlite3

con = sqlite3.connect('../database/homework_bot_database.sqlite', check_same_thread=False)
cur = con.cursor()


def get_subjects():
    return cur.execute('select name from subject '
                       "where name not like '%/%' and id != 22 and id != 21 "
                       "order by id").fetchall()


def get_subject(subject_id):
    cur.execute('SELECT name FROM subject '
                f"WHERE id = {subject_id} ")
    return cur.fetchone()


def get_subject_sticker(subject_name):
    cur.execute('SELECT sticker FROM subject '
                f"WHERE name = '{subject_name}'")
    return cur.fetchone()


def get_weekend():
    cur.execute('SELECT id, name FROM weekday '
                'ORDER BY id')
    return cur.fetchall()


def get_weekday(weekday_id):
    cur.execute('SELECT name FROM weekday '
                f'WHERE id = {weekday_id}')
    return cur.fetchone()


def get_schedule(day):
    cur.execute(f"SELECT id FROM weekday WHERE name = '{day}'")
    weekday_id = cur.fetchone()[0]
    cur.execute('SELECT s.id, s.name '
                'FROM schedule AS t '
                'LEFT JOIN subject AS s '
                'ON s.id = t.subject_id '
                f'WHERE t.weekday_id = {weekday_id} '
                'ORDER BY weight ASC')

    result = []
    count = 0
    for elem in cur.fetchall():
        count += 1
        result.append(f'{count}.  {elem[1]}')

    return '\n'.join(result)


def get_homework(subject):
    cur.execute('SELECT s.id, s.name, h.date, h.description '
                'FROM homework AS h '
                'LEFT JOIN subject AS s '
                'ON h.subject_id = s.id '
                f"WHERE name = '{subject}' "
                'ORDER BY h.date')
    return cur.fetchall()


def get_homework_by_date(date):
    print(date)
    cur.execute("SELECT subject_id, description FROM homework "
                f"WHERE date = '{date}'")
    return cur.fetchall()


def get_teachers():
    cur.execute('SELECT teachers.name, subject.name FROM teachers '
                'LEFT JOIN subject '
                'ON subject_id = subject.id '
                'ORDER BY subject.name')
    return cur.fetchall()


def get_timetable():
    cur.execute('SELECT time FROM timetable')
    return cur.fetchall()


def get_weekday_timetable(weekday_id):
    beginningOfDay = 'Начало учебного дня - '
    endOfDay = 'Конец учебного дня - '
    cur.execute('SELECT subject_id, weight FROM schedule '
                f'WHERE weekday_id = {weekday_id} '
                'ORDER BY weight')
    result = cur.fetchall()

    len_beginning = 1
    len_end = len(result)

    for num, weekday in enumerate(result):
        if weekday[0] == 21:
            len_beginning += 1

    cur.execute('SELECT time FROM timetable '
                f'WHERE id = {len_beginning}')
    beginningOfDay += cur.fetchone()[0].split(' ')[0]

    cur.execute('SELECT time FROM timetable '
                f'WHERE id = {len_end}')
    endOfDay += cur.fetchone()[0].split(' ')[2]

    return f'⏰ <b>{beginningOfDay}.</b>\n\n🏠 <b>{endOfDay}</b>.'


def get_users():
    result = []
    cur.execute('SELECT telegram_id FROM USERS ')
    cur_result = cur.fetchall()

    for i in range(len(cur_result)):
        result.append(cur_result[i][0])
    return result
