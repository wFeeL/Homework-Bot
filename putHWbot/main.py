import telebot
import database
import text_message
import json
import datetime
from telegram_bot_calendar import DetailedTelegramCalendar
from telebot import types

bot = telebot.TeleBot('6444163775:AAH2B9AUyy81EwQA_WZPuwi5eXNDbDTN-2U')  # API Token
bot_telegram_id = 6444163775  # Admin Telegram id (only this user can employ bot)
admin_telegram_id = 416966184  # Bot Telegram id (need for callbacks)


def check_permission(message):
    if message.from_user.id == admin_telegram_id or message.from_user.id == bot_telegram_id:
        return True
    return False


@bot.message_handler(commands=['start', 'help'])
def start(message):
    if check_permission(message):
        bot.send_message(message.chat.id, text_message.GREETINGS, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f'Ваш ID ({message.from_user.id}) не соответствует.')


@bot.message_handler(commands=['add'])
def main_menu(message, func='add', callback=False):
    if check_permission(message):
        if not callback:
            create_data()
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)

        if func == 'add':
            markup.add(types.KeyboardButton('Выбрать предмет'), types.KeyboardButton('Выбрать дату'),
                       types.KeyboardButton('Добавить описание'))

            if homework_data.apply_to_add():
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Отправить данные', callback_data='add_data'))
                bot.send_message(message.chat.id, text_message.TEXT_TO_APPLY_HOMEWORK)

        elif func == 'edit' and callback:
            markup.add(types.KeyboardButton('Редактировать дату'), types.KeyboardButton('Редактировать описание'))
            update_markup = types.InlineKeyboardMarkup()
            update_markup.add(types.InlineKeyboardButton('Обновить данные', callback_data='edit_data'))
            if not callback:
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id,
                                      text=text_message.TEXT_TO_EDIT_HOMEWORK, reply_markup=update_markup)
            else:
                bot.send_message(chat_id=message.chat.id, text=text_message.TEXT_TO_EDIT_HOMEWORK,
                                 reply_markup=update_markup)

        bot.send_message(message.chat.id,
                         f'<b>Данные о домашнем задании</b>:\n\n<i>Предмет</i> - {homework_data.subject}\n\n'
                         f'<i>Дата</i> - {homework_data.date}\n\n'
                         f'<i>Описание</i> - {homework_data.description}',
                         reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f'Вы не можете добавлять данные в базу. '
                                          f'Ваш ID ({message.from_user.id}) не соответствует.')


def create_data(subject='', date='', description='', id=''):
    global homework_data
    homework_data = database.NewHomework(subject, date, description, id)


@bot.callback_query_handler(func=lambda call: 'add_data' in call.data)
def send_data(call):
    try:
        subject_id = database.get_subject_id(homework_data.subject)
        homework_date = homework_data.date
        description = homework_data.description

        database.add_data_to_database(subject_id, homework_date, description)

        bot.delete_message(call.message.chat.id, call.message.message_id - 1)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Вы успешно отправили домашнее задание в базу данных.\n\n'
                                               '<b><i>Спасибо за проделанную работу!</i></b>', parse_mode='HTML')
        bot.disable_save_reply_handlers()
        create_data(call.message)
    except TypeError:
        bot.send_message(call.message.chat.id, text_message.TEXT_ERROR2, parse_mode='HTML')


@bot.message_handler(commands=['edit'])
def edit_menu(message, callback=False):
    if check_permission(message):
        try:
            subjects = database.get_subjects()
            markup = types.InlineKeyboardMarkup(row_width=2)
            for i in range(len(subjects)):
                data = database.get_homework(subjects[i][0])
                subject_name = subjects[i][0]

                data_length = len(data)
                page = data_length

                markup.add(types.InlineKeyboardButton(text=subjects[i][0],
                                                      callback_data="{\"subject\":\"" + str(subject_name) +
                                                                    f"\",\"page\":\"{page}\",\"len\":"
                                                                    + str(data_length) + "}"))

            if callback:
                bot.edit_message_text(message_id=message.message_id, text='<b>Выберите школьный предмет:</b>',
                                      chat_id=message.chat.id, reply_markup=markup, parse_mode='HTML')
            else:
                bot.send_message(text='<b>Выберите школьный предмет:</b>',
                                 chat_id=message.chat.id, reply_markup=markup, parse_mode='HTML')
        except NameError:
            bot.send_message(message.chat.id, text_message.TEXT_ERROR2, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, 'Вы не можете редактировать данные. '
                                          f'Ваш ID ({message.from_user.id}) не соответствует.')


@bot.callback_query_handler(func=lambda call: 'subject' in call.data and 'page' in call.data)
def edit_menu_pagination(call):
    try:
        json_string = json.loads(call.data.split('_')[0])

        length = json_string['len']
        page = int(json_string['page'])
        data = database.get_homework(json_string['subject'])

        subject, date, description = data[page - 1][1], data[page - 1][2], data[page - 1][3]
        homework_id = database.get_homework_id(subject, date, description)[0]
        create_data(subject=subject, date=date, description=description, id=homework_id)

        markup = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Вперед ▶',
                                                 callback_data="{\"subject\":\"" + str(homework_data.subject) +
                                                               "\",\"page\":" + str(page + 1) + ",\"len\":"
                                                               + str(length) + "}")
        back_button = types.InlineKeyboardButton(text='◀ Назад',
                                                 callback_data="{\"subject\":\"" +
                                                               str(homework_data.subject) + "\",\"page\":" +
                                                               str(page - 1) + ",\"len\":" + str(length) + "}")

        count_button = types.InlineKeyboardButton(text=f'{page}/{length}',
                                                  callback_data="{\"subject\":\"" + str(homework_data.subject) +
                                                                "\",\"choose\":" + str(page + 1) + ",\"len\":"
                                                                + str(length) + "}")
        edit_date_button = types.InlineKeyboardButton(text='📝 Изменить домашнее задание',
                                                      callback_data='edit_homework')
        delete_homework_button = types.InlineKeyboardButton(text='🗑️ Удалить домашнее задание',
                                                            callback_data='delete_homework')
        menu_button = types.InlineKeyboardButton('🔄 К выбору предметов', callback_data='edit_menu')

        if page == 1 and length == 1:
            markup.add(count_button)

        elif page == 1:
            markup.add(count_button, next_button)

        elif page == length:
            markup.add(back_button, count_button)

        else:
            markup.add(back_button, count_button, next_button)

        markup.row(edit_date_button)
        markup.row(delete_homework_button)
        markup.row(menu_button)

        bot.edit_message_text(
            text=f'Предмет: <b>{homework_data.subject}</b>'
                 f'\n\nДата: <i>{homework_data.date}</i>\n\nОписание: {homework_data.description}',
            parse_mode="HTML", reply_markup=markup, chat_id=call.message.chat.id, message_id=call.message.message_id)
    except IndexError:
        bot.send_message(call.message.chat.id, text_message.TEXT_ERROR1, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: 'delete_homework' in call.data)
def delete_homework(call):
    bot.delete_message(call.message.chat.id, message_id=call.message.message_id)
    database.delete_data(homework_data.id)
    bot.send_message(call.message.chat.id, text_message.TEXT_TO_DELETE_HOMEWORK)


@bot.message_handler(commands=['users'])
def edit_user_menu(message):
    if check_permission(message):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        add_user_button = types.KeyboardButton(text='Добавить пользователя')
        delete_user_button = types.KeyboardButton(text='Удалить пользователя')
        show_users_button = types.KeyboardButton(text='Список всех пользователей')
        markup.add(add_user_button, delete_user_button, show_users_button)

        bot.send_message(chat_id=message.chat.id, text=text_message.USERS_CHANGE_MENU, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Вы не можете просматривать данные пользователей. '
                                          f'Ваш ID ({message.from_user.id}) не соответствует.')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if check_permission(message):
        if message.text == 'Выбрать предмет':
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            subjects = database.get_subjects()

            for i in range(len(subjects)):
                subject_name = subjects[i][0]
                if subject_name and '/' not in subject_name:
                    markup.add(types.KeyboardButton(subject_name))

            bot.send_message(text='<b>Предмет:</b>', chat_id=message.chat.id, reply_markup=markup,
                             parse_mode='HTML')
            bot.register_next_step_handler(message, set_subject)

        elif message.text == 'Выбрать дату':
            calendar, step = DetailedTelegramCalendar(min_date=datetime.date.today(),
                                                      max_date=datetime.date(year=2024, month=5, day=29),
                                                      calendar_id=1).build()
            bot.send_message(text=f'<b>Дата:</b>', chat_id=message.chat.id, parse_mode='HTML',
                             reply_markup=calendar)

        elif message.text == 'Добавить описание':
            bot.send_message(text='<b>Описание:</b>', chat_id=message.chat.id, parse_mode='HTML')
            bot.register_next_step_handler(message, set_description, 'add')

        elif message.text == 'Редактировать описание':
            bot.send_message(text='<b>Описание:</b>', chat_id=message.chat.id, parse_mode='HTML')
            bot.register_next_step_handler(message, set_description, 'edit')

        elif message.text == 'Редактировать дату':
            calendar, step = DetailedTelegramCalendar(min_date=datetime.date.today(),
                                                      max_date=datetime.date(year=2024, month=5, day=29),
                                                      calendar_id=2).build()
            bot.send_message(text='<b>Дата:</b>', chat_id=message.chat.id, parse_mode='HTML', reply_markup=calendar)

        elif message.text == 'Добавить пользователя':
            bot.send_message(chat_id=message.chat.id, text=text_message.USERS_ID)
            bot.register_next_step_handler(message, add_user)

        elif message.text == 'Удалить пользователя':
            bot.send_message(chat_id=message.chat.id, text=text_message.USERS_ID)
            bot.register_next_step_handler(message, delete_user)

        elif message.text == 'Список всех пользователей':
            users = database.get_users()
            users_stroke = '\n'.join(users)
            bot.send_message(chat_id=message.chat.id, text='⚡ Список всех пользователей:\n' + users_stroke)

    else:
        bot.send_message(message.chat.id, 'Вы не можете использовать этого бота. '
                                          f'Ваш ID ({message.from_user.id}) не соответствует.')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def set_date(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru', min_date=datetime.date.today(),
                                                 max_date=datetime.date(year=2024, month=5, day=29)).process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите дату:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        homework_data.date = result
        main_menu(call.message, func='add', callback=True)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def set_date(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru', min_date=datetime.date.today(),
                                                 max_date=datetime.date(year=2024, month=5, day=29)).process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите дату:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        homework_data.date = result
        main_menu(call.message, func='edit', callback=True)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if call.data == 'edit_homework':
        main_menu(call.message, func='edit', callback=True)

    if call.data == 'edit_menu':
        edit_menu(call.message, callback=True)

    if call.data == 'edit_data':
        edit_data(call)


def set_subject(message):
    try:
        subject = message.text
        homework_data.subject = subject
        main_menu(message, func='add', callback=True)
    except NameError:
        bot.send_message(message.chat.id, text_message.TEXT_ERROR2)


def set_description(message, func='add'):
    description = message.text
    if len(description) > 360:
        bot.send_message(message.chat.id, '⚡ Ты превысил длину описания в 360 символов.'
                                          '\n Возвращаю тебя в главное меню.')
        main_menu(message, callback=True)
    else:
        homework_data.description = description
        main_menu(message, func='add', callback=True) if func == 'add' else \
            main_menu(message, func='edit', callback=True)


def add_user(message):
    try:
        user_id = message.text
        database.add_user(user_id)
        bot.send_message(message.chat.id, f'⚡ Пользователь <b>{user_id}</b> был успешно добавлен в базу данных!',
                         parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, text_message.TEXT_ERROR3, parse_mode='HTML')


def delete_user(message):
    try:
        user_id = message.text
        database.delete_user(user_id)
        bot.send_message(message.chat.id, f'⚡ Пользователь <b>{user_id}</b> был успешно удален из базы данных!',
                         parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, text_message.TEXT_ERROR3, parse_mode='HTML')


def edit_data(call):
    try:
        homework_id = homework_data.id
        date = homework_data.date
        description = homework_data.description

        database.update_data(homework_id, date, description)

        bot.delete_message(call.message.chat.id, call.message.message_id + 1)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Вы успешно обновили домашнее задание в базе данных.\n\n'
                                               '<b><i>Спасибо за проделанную работу!</i></b>', parse_mode='HTML')
        bot.disable_save_reply_handlers()
    except NameError:
        bot.send_message(call.message.chat.id, text_message.TEXT_ERROR2, parse_mode='HTML')


if __name__ == '__main__':
    bot.infinity_polling()
