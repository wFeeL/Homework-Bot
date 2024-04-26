import database
import datetime
import json
import requests
import telebot
import text_message
import telegram_calendar
import locale
import logging
import time

from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar

telegram_calendar.reformatTelegramCalendar()
bot = telebot.TeleBot('6360506500:AAE6NdNI59KoYy5pt01jUJ73bU4VPPMh3tY')  # API Token
weather_API = 'fc99a79328de8b7fa62cec28ebbb5a00'

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def checkPermission(message):
    users = database.get_users()
    if str(message.from_user.id) in users:
        return True
    bot.send_message(message.chat.id, text=text_message.FALSE_PERMISSION, parse_mode='HTML')
    return False


@bot.message_handler(commands=['start', 'help'])
def greetings(message):
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(
        text='💰 Поддержать автора', url='https://www.tinkoff.ru/rm/saburov.daniil23/TTzup21621'))
    bot.send_message(text=text_message.GREETINGS, chat_id=message.chat.id, parse_mode='HTML', reply_markup=markup)


@bot.message_handler(commands=['support'])
def support(message):
    bot.send_message(text=text_message.SUPPORT, chat_id=message.chat.id, parse_mode='HTML')


@bot.message_handler(commands=['bot_message'])
def send_message_to_all(message):
    if str(message.from_user.id) == '416966184':
        msg = bot.send_message(chat_id=message.chat.id, text=text_message.MESSAGE_TO_SEND)
        bot.register_next_step_handler(msg, message_to_send_status)
    else:
        bot.send_message(text=text_message.FALSE_PERMISSION, chat_id=message.chat.id)


@bot.message_handler(commands=['menu'])
def homework_menu(message, callback=False):
    if checkPermission(message):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton('✍ Задания на завтра', callback_data='homework_tomorrow'),
                   types.InlineKeyboardButton('📅 Календарь заданий', callback_data='homework_calendar'),
                   types.InlineKeyboardButton('⚜ Все домашние задания', callback_data='homework_all'))
        if not callback:
            bot.send_message(message.chat.id, '⚡ Выберите категорию:', reply_markup=markup, parse_mode='HTML')
        else:
            bot.edit_message_text(chat_id=message.chat.id, text='⚡ Выберите категорию:',
                                  message_id=message.message_id, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['tomorrow'])
def homework_tomorrow(message, callback=False):
    if checkPermission(message):
        tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
        next_date = datetime.datetime.strftime(tomorrow_date + datetime.timedelta(days=1), '%Y-%m-%d')
        previous_date = datetime.datetime.strftime(tomorrow_date - datetime.timedelta(days=1), '%Y-%m-%d')

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(types.InlineKeyboardButton('🔄 Главное меню', callback_data='menu'))
        markup.add(
            types.InlineKeyboardButton(text='◀ Назад',
                                       callback_data="{\"date\":\"" + f"{previous_date}" + "\"}"),
            types.InlineKeyboardButton(text='Вперед ▶',
                                       callback_data="{\"date\":\"" + f"{next_date}" + "\"}"))

        homework_tomorrow_data = database.get_homework_by_date(tomorrow_date)
        homework_tomorrow_text = ''

        if len(homework_tomorrow_data) > 0:
            for i in range(len(homework_tomorrow_data)):
                subject_name = str(''.join(database.get_subject(homework_tomorrow_data[i][0])))
                subject_description = str(homework_tomorrow_data[i][1])

                homework_tomorrow_text += f'{i + 1}. Предмет: <b>{subject_name}</b>\n' \
                                          f'Описание: <i>{subject_description}</i>\n\n'
            if callback:
                bot.edit_message_text(chat_id=message.chat.id, parse_mode='HTML',
                                      message_id=message.message_id, reply_markup=markup,
                                      text='<b>⚡ Домашние задания на завтра:</b>\n\n' + homework_tomorrow_text)
            else:
                bot.send_message(chat_id=message.chat.id, reply_markup=markup, parse_mode='HTML',
                                 text='<b>⚡ Домашние задания на завтра:</b>\n\n' + homework_tomorrow_text)
        elif callback:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id,
                                  text=text_message.HOMEWORK_TOMORROW_IS_NULL, parse_mode='HTML', reply_markup=markup)
        else:
            bot.send_message(chat_id=message.chat.id, text=text_message.HOMEWORK_TOMORROW_IS_NULL, parse_mode='HTML',
                             reply_markup=markup)


@bot.message_handler(commands=['calendar'])
def homework_calendar(message, callback=False):
    if checkPermission(message):
        calendar, step = DetailedTelegramCalendar(min_date=datetime.date(year=2023, month=9, day=1),
                                                  max_date=datetime.date(year=2024, month=5, day=29)).build()
        if callback:
            bot.edit_message_text(message_id=message.message_id,
                                  chat_id=message.chat.id, text='⚡ Выберите дату:', reply_markup=calendar)
        else:
            bot.send_message(chat_id=message.chat.id, text='⚡ Выберите дату:', reply_markup=calendar)


@bot.message_handler(commands=['homework'])
def homework_all(message, callback=False):
    if checkPermission(message):
        subjects = database.get_subjects()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(len(subjects)):
            data = database.get_homework(subjects[i][0])
            subject_name = subjects[i][0]
            subject_sticker = database.get_subject_sticker(subject_name)[0]
            data_length = len(data)
            page = data_length

            markup.add(types.InlineKeyboardButton(text=f'{subject_sticker} {subjects[i][0]}',
                                                  callback_data="{\"subject\":\"" + str(subject_name) +
                                                                f"\",\"page\":\"{page}\",\"len\":"
                                                                + str(data_length) + "}"))

        markup.row(types.InlineKeyboardButton('🔄 Главное меню', callback_data='menu'))
        if callback:
            bot.edit_message_text(message_id=message.message_id, text='⚡ Выберите школьный предмет:',
                                  chat_id=message.chat.id, reply_markup=markup, parse_mode='HTML')
        else:
            bot.send_message(text='⚡ Выберите школьный предмет:',
                             chat_id=message.chat.id, reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: 'subject' in call.data and 'page' in call.data)
def homework_all_pagination(call):
    json_string = json.loads(call.data.split('_')[0])

    length = json_string['len']
    page = int(json_string['page'])
    subject_name = json_string['subject']
    subject_sticker = database.get_subject_sticker(subject_name)[0]
    data = database.get_homework(json_string['subject'])

    markup = types.InlineKeyboardMarkup()

    next_button = types.InlineKeyboardButton(text='Вперед ▶',
                                             callback_data="{\"subject\":\"" + str(subject_name) +
                                                           "\",\"page\":" + str(page + 1) + ",\"len\":"
                                                           + str(length) + "}")
    back_button = types.InlineKeyboardButton(text='◀ Назад',
                                             callback_data="{\"subject\":\"" + str(subject_name) + "\",\"page\":" +
                                                           str(page - 1) + ",\"len\":" + str(length) + "}")

    count_button = types.InlineKeyboardButton(text=f'{page}/{length}',
                                              callback_data="{\"subject\":\"" + str(subject_name) +
                                                            "\",\"choose\":" + str(page + 1) + ",\"len\":"
                                                            + str(length) + "}")

    menu_button = types.InlineKeyboardButton('🔄 К выбору предметов', callback_data='homework_all')

    if page == 1 and length == 1:
        markup.add(count_button)

    elif page == 1:
        markup.add(count_button, next_button)

    elif page == length:
        markup.add(back_button, count_button)

    else:
        markup.add(back_button, count_button, next_button)

    markup.row(menu_button)
    bot.edit_message_text(
        text=f'Предмет: {subject_sticker} <b>{str(data[page - 1][1])}</b>'
             f'\n\nДата: <i>{data[page - 1][2].strftime("%A, %d.%m.%Y")}</i>\n\nДомашнее задание: {data[page - 1][3]}',
        parse_mode="HTML", reply_markup=markup, chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.message_handler(commands=['schedule'])
def timetable_menu(message, callback=False):
    if checkPermission(message):
        weekend = database.get_weekend()

        markup = types.InlineKeyboardMarkup(row_width=1)

        for i in range(len(weekend)):
            weekday_name = weekend[i][1]
            weekday_id = weekend[i][0]
            markup.add(types.InlineKeyboardButton(f'{text_message.SCHEDULE_DICTIONARY_RUS[weekday_name]}'.capitalize(),
                                                  callback_data="{\"weekday_id\":\"" + f"{weekday_id}" + "\"}"))

        if not callback:
            bot.send_message(text='⚡ Выберите день недели:', chat_id=message.chat.id,
                             reply_markup=markup, parse_mode='HTML')
        else:
            bot.edit_message_text(text='⚡ Выберите день недели:', chat_id=message.chat.id,
                                  reply_markup=markup, parse_mode='HTML', message_id=message.message_id)


@bot.callback_query_handler(func=lambda call: 'weekday_id' in call.data)
def timetable_day(call):
    json_str = int(json.loads(call.data)['weekday_id'][0])

    weekday_id = 1 if json_str == 7 else 6 if json_str == 0 else json_str
    weekday_name = database.get_weekday(weekday_id)[0]

    next_button = types.InlineKeyboardButton(text='Вперед ▶',
                                             callback_data="{\"weekday_id\":\"" + f"{weekday_id + 1}" + "\"}")
    back_button = types.InlineKeyboardButton(text='◀ Назад',
                                             callback_data="{\"weekday_id\":\"" + f"{weekday_id - 1}" + "\"}")
    menu_button = types.InlineKeyboardButton('🔄 Главное меню', callback_data='timetable_menu')

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.row(menu_button)
    markup.add(back_button, next_button)

    text = f'⚡ <b>Расписание на {text_message.SCHEDULE_DICTIONARY_RUS[weekday_name]}:</b>\n\n' \
           f'{database.get_schedule(weekday_name)}\n\n' \
           f'{database.get_weekday_timetable(weekday_id)}'

    bot.edit_message_text(message_id=call.message.message_id, chat_id=call.message.chat.id,
                          text=text, parse_mode='HTML', reply_markup=markup)


@bot.message_handler(commands=['teachers'])
def show_teachers(message):
    if checkPermission(message):
        teachers = database.get_teachers()
        result = text_message.TEACHERS
        for i in range(len(teachers)):
            teacher = teachers[i][0]
            subject = teachers[i][1]

            result += f'{i + 1}. <b>{subject}</b> - {teacher}\n'
        bot.send_message(chat_id=message.chat.id, text=result, parse_mode='HTML')


@bot.message_handler(commands=['site'])
def site(message):
    if checkPermission(message):
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Перейти по ссылке',
                                                                             url='https://petersburgedu.ru/'))
        bot.send_message(text=text_message.SITE, chat_id=message.chat.id, parse_mode='HTML', reply_markup=markup)


@bot.message_handler(commands=['donate'])
def donate(message):
    bot.send_message(chat_id=message.chat.id, text=text_message.DONATE, parse_mode='HTML')


@bot.message_handler(commands=['weather'])
def get_weather(message):
    if checkPermission(message):
        request = requests.get(
            url=f'https://api.openweathermap.org/data/2.5/weather?q=Saint%20Petersburg&appid={weather_API}&units=metric')
        if request.status_code == 200:
            data = json.loads(request.text)

            weather = data['weather'][0]['description']
            temperature = data['main']['temp']
            feels_like = data['main']['feels_like']
            wind_speed = data['wind']['speed']

            if 'clear sky' in weather:
                text_weather = text_message.CLEAR_SKY_WEATHER
            elif 'overcast clouds' in weather:
                text_weather = text_message.OVERCAST_CLOUDS_WEATHER
            elif 'rain' in weather:
                text_weather = text_message.RAIN_WEATHER
            elif 'few clouds' in weather:
                text_weather = text_message.FEW_CLOUDS_WEATHER
            elif weather == 'shower rain' or weather == 'thunderstorm':
                text_weather = text_message.SHOWER_RAIN_WEATHER
            elif 'snow' in weather:
                text_weather = text_message.SNOW_WEATHER
            else:
                text_weather = text_message.WEATHER

            bot.send_message(chat_id=message.chat.id,
                             text=f'<b>⚡ Прогноз погоды в Санкт-Петербурге</b>:\n\n<i>Температура:</i> {temperature}ºC\n'
                                  f'<i>Ощущается, как:</i> {feels_like}ºC\n<i>Ветер:</i> {wind_speed} м/c\n\n'
                                  + text_weather,
                             parse_mode='HTML')

        else:
            bot.send_message(chat_id=message.chat.id, text=text_message.TEXT_ERROR, parse_mode='HTML')


@bot.message_handler(commands=['timetable'])
def get_schedule(message):
    if checkPermission(message):
        result = text_message.TIMETABLE
        data = database.get_timetable()
        for i in range(len(data)):
            time = data[i][0]
            result += f'{i + 1}. <b>{time}</b>\n'

        bot.send_message(chat_id=message.chat.id, text=result + text_message.TIMETABLE_ADVICE, parse_mode='HTML')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def set_date(call):
    result, key, step = DetailedTelegramCalendar(locale='ru',
                                                 min_date=datetime.date(year=2023, month=9, day=1),
                                                 max_date=datetime.date(year=2024, month=5, day=29)).process(call.data)
    if not result and key:
        bot.edit_message_text(f"⚡ Выберите дату:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        get_homework_calendar(call, datetime.date.strftime(result, '%Y-%m-%d'))


@bot.message_handler(content_types=['text'])
def random_text(message):
    bot.send_message(chat_id=message.chat.id, text=text_message.RANDOM_TEXT_FROM_USER, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: 'date' in call.data)
def calendar_date(call):
    json_str = json.loads(call.data)['date']
    get_homework_calendar(call, json_str)


def message_to_send_status(message):
    global new_message
    new_message = message.text

    markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton(text='🚫 Отменить отправку', callback_data='cancel_send_message')
    send_message_button = types.InlineKeyboardButton(text='✔ Отправить сообщение',
                                                     callback_data='message_for_users')

    markup.add(cancel_button, send_message_button)

    bot.send_message(message.chat.id, text=f'⚡ Сообщение, для отправки ВСЕМ пользователям:\n\n{new_message}',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: 'cancel_send_message' in call.data)
def send_message_for_users(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Отправка отменена!')


@bot.callback_query_handler(func=lambda call: 'message_for_users' in call.data)
def send_message_for_users(call):
    users = database.get_users()
    for user_id in users:
        try:
            bot.send_message(user_id, text=new_message)
        except Exception:
            print(user_id)
    bot.edit_message_text(text='⚡ Сообщение успешно отправлено!', chat_id=call.message.chat.id,
                          message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'menu':
        homework_menu(call.message, True)

    if call.data == 'homework_tomorrow':
        homework_tomorrow(call.message, True)

    if call.data == 'homework_all':
        homework_all(call.message, True)

    if call.data == 'homework_calendar':
        homework_calendar(call.message, True)

    if call.data == 'timetable_menu':
        timetable_menu(call.message, True)


def get_homework_calendar(call, result):
    markup = types.InlineKeyboardMarkup(row_width=3)

    date = datetime.datetime.strptime(result, '%Y-%m-%d')

    next_date = datetime.datetime.strftime(date + datetime.timedelta(days=1), '%Y-%m-%d')
    previous_date = datetime.datetime.strftime(date - datetime.timedelta(days=1), '%Y-%m-%d')

    markup.row(types.InlineKeyboardButton('🔄 Главное меню', callback_data='menu'))
    markup.add(
        types.InlineKeyboardButton(text='◀ Назад',
                                   callback_data="{\"date\":\"" + f"{previous_date}" + "\"}"),
        types.InlineKeyboardButton(text='Вперед ▶',
                                   callback_data="{\"date\":\"" + f"{next_date}" + "\"}"))

    homework_data = database.get_homework_by_date(date)
    homework_text = ''

    if len(homework_data) > 0:
        for i in range(len(homework_data)):
            subject_name = ''.join(database.get_subject(homework_data[i][0]))
            subject_description = str(homework_data[i][1])

            homework_text += f'{i + 1}. Предмет: <b>{subject_name}</b>\n' \
                             f'Домашнее задание: <i>{subject_description}</i>\n\n'

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup,
                              parse_mode='HTML',
                              text=f'⚡ <b>Домашние задания на {date.strftime("%A, %d.%m.%Y")}:</b>\n\n'
                                   + homework_text)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup,
                              text=text_message.HOMEWORK_IS_NULL.format(date.strftime("%d.%m.%Y")),
                              parse_mode='HTML')


class Message:
    def __init__(self, text):
        self.message_text = text


if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)

    except Exception as err:
        logging.error(err)
        time.sleep(5)
        print('Internet Error')
