from telegram_bot_calendar import base


def reformatTelegramCalendar():
    base.TelegramCalendar.empty_year_button = "×"
    base.TelegramCalendar.empty_month_button = "×"
    base.TelegramCalendar.empty_nav_button = "×"
    base.TelegramCalendar.size_year_column = 1
