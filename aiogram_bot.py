from __future__ import print_function

import logging

from aiogram import types, Bot, executor, Dispatcher
import datetime
import time
import random
from telegram_bot_calendar import WMonthTelegramCalendar
import config
from dictor import users
import logging
from sqlite import sql_start, sql_add_user
from google_calendar_api import calendar

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.token)
dp = Dispatcher(bot)


event_id = ''
back = types.KeyboardButton('В начало')
wrong_time = types.KeyboardButton('Изменить время')
wrong_date = types.KeyboardButton('Изменить дату')



@dp.message_handler(commands=['start'])
async def start(message):
    name = f'Здравствуйте, {message.from_user.first_name}! Выберите услугу, на которую хотите записаться: '
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    manikur = types.KeyboardButton('Маникюр')
    pedicur = types.KeyboardButton('Педикюр')
    markup.add(manikur, pedicur, back)
    await bot.send_message(message.chat.id, name, reply_markup=markup)
    print(message.chat.id)
    users[message.chat.id] = {}
    users[message.chat.id]["username"] = message.from_user.username
    users[message.chat.id]["first_name"] = message.from_user.first_name
    await sql_add_user(user_id=message.from_user.id)


@dp.message_handler(content_types=['text'])
async def bot_message(message):
    if message.chat.type == 'private':
        if message.text == 'Маникюр' or message.text == 'Педикюр':
            users[message.chat.id]["event_summary"] = message.text
            print(users[message.chat.id]["event_summary"])
            await start_calendar(message)
        elif message.text == 'Верно!':
            await calendar.get_events_list2(message)
        elif message.text == 'Изменить дату':
            await bot.send_message(message.chat.id, 'Давайте попробуем еще раз)')
            await start_calendar(message)
        elif message.text in ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00']:
            users[message.chat.id]["booking_time"] = message.text
            await getnumber(message)
        elif message.text == 'Изменить время':
            await calendar.get_events_list2(message)
        elif message.text[0] == '+' or message.text[1] == '9' and len(message.text) == 11:
            users[message.chat.id]["phone_num"] = message.text
            await finish(message)
        elif message.text == 'В начало':
            await start(message)
        elif message.text == "Все верно!":
            random_id_event(message)
            print(message.chat.id)
            event = calendar.create_event_dict(message)
            calendar.create_event(event)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=False)
            second_event = types.KeyboardButton('Записаться еще')
            delete = types.KeyboardButton('Отменить запись')
            markup.add(second_event, delete)
            await bot.send_message(message.chat.id, 'Отлично, вы записаны! Благодарю за запись!\n'
                                              'Если у вас есть дополнительные вопросы, '
                                              'можете написать мне в личные сообщения @andreyblsv',
                             reply_markup=markup)
            time.sleep(1)
            await bot.send_message(message.chat.id, 'Это тестовый бот, по воросам приобретения - пишите: @andreyblsv',
                             reply_markup=markup)
        elif message.text == 'Записаться еще':
            await start(message)
        elif message.text == 'Отменить запись':
            await calendar.get_events_id(message)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            second_event = types.KeyboardButton('Записаться еще')
            delete = types.KeyboardButton('Отменить запись')
            markup.add(second_event, delete)
            await bot.send_message(message.chat.id, 'Больше записей не найдено! Жду вас снова)', reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(back)
            await bot.send_message(message.chat.id,
                             'На этот вопрос я не знаю ответ. Воспользуйтесь, '
                             'пожалуйста, кнопками внизу или командой /start',
                             reply_markup=markup)


@dp.message_handler(content_types=['contact'])
async def getcontact(message):
    users[message.chat.id]["phone_num"] = message.contact.phone_number
    print(users[message.chat.id]["phone_num"])
    await finish(message)


async def start_calendar(message):
    calendarbot, step = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today() + datetime.timedelta(days=1),
                                               max_date=datetime.date.today() + datetime.timedelta(days=51)).build()
    await bot.send_message(message.chat.id, "Выберите день", reply_markup=calendarbot)


@dp.callback_query_handler(WMonthTelegramCalendar.func())
async def calc(c):
    result, key, step = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today() + datetime.timedelta(days=1),
                                               max_date=datetime.date.today() + datetime.timedelta(days=51)).process(
        c.data)
    if not result and key:
        await bot.edit_message_text("Выберите день", c.message.chat.id, c.message.message_id,
                              reply_markup=key)
    elif result:
        await bot.edit_message_text(f"День записи: {result.strftime('%d.%m.%Y')}", c.message.chat.id,
                                    c.message.message_id, reply_markup=key)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        add_date = types.KeyboardButton('Верно!')
        wrong_date = types.KeyboardButton('Изменить дату')
        markup.add(add_date, wrong_date, back)
        await bot.send_message(c.message.chat.id, 'Верно?', reply_markup=markup)
        users[c.message.chat.id]["booking_day"] = result.strftime('%d.%m.%Y')


def random_id_event(message):
    global event_id
    id_event = random.sample(range(10), 3)
    event_id = str(message.chat.id) + ''.join(map(str, id_event))
    print(event_id)


async def getnumber(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    reg_button = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
    markup.add(reg_button, wrong_time, back)
    await bot.send_message(message.chat.id,
                     'Оставьте свой контактный номер для связи, пожалуйста:',
                     reply_markup=markup)


async def finish(message):
    print(get_dict(message))
    print(get_dict(message)["first_name"])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    right_button = types.KeyboardButton("Все верно!")
    markup.add(right_button, wrong_time, wrong_date, back)
    await bot.send_message(message.chat.id, f'{get_dict(message)["first_name"]}, вы записываетесь на '
                                      f'{get_dict(message)["event_summary"]}\n'
                                      f'{get_dict(message)["booking_day"]}\n'
                                      f'в {get_dict(message)["booking_time"]}\n'
                                      f'Ваш контактный номер: {get_dict(message)["phone_num"]}\n\n'
                                      f'Все верно?', reply_markup=markup)


async def on_startup(_):
    await sql_start()


def get_dict(message):
    for k in users.keys():
        if k == message.chat.id:
            return users[k]


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)