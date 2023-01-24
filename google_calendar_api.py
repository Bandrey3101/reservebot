from aiogram import types, Bot
import googleapiclient
from googleapiclient.discovery import build
from google.oauth2 import service_account
import time
from config import calendar_id, token
import datetime
from dictor import users

SERVICE_ACCOUNT_FILE = 'apikey.json'
calendarId = calendar_id
SCOPES = ['https://www.googleapis.com/auth/calendar']
bot = Bot(token=token)


event_id = ''
back = types.KeyboardButton('В начало')
wrong_time = types.KeyboardButton('Изменить время')
wrong_date = types.KeyboardButton('Изменить дату')


def get_dict(message):
    for k in users.keys():
        if k == message.chat.id:
            return users[k]


class GoogleCalendar(object):
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    def create_event_dict(self, message):
        descript = [get_dict(message)["first_name"], get_dict(message)["phone_num"]]
        descriptor = ' | '.join(descript)
        book1 = [get_dict(message)["booking_day"], get_dict(message)["booking_time"]]
        book2 = ' '.join(book1)
        start_time = datetime.datetime.strptime(book2, '%d.%m.%Y %H:%M')
        end_time = start_time + datetime.timedelta(hours=2)
        end_ti = end_time.strftime('%Y-%m-%dT%H:%M:%S+05:00')
        start_ti2 = start_time.strftime('%Y-%m-%dT%H:%M:%S+05:00')

        event = {
            'summary': get_dict(message)["event_summary"],
            'description': descriptor,

            'start': {
                'dateTime': start_ti2,
                # 'timeZone': 'Asia/Yekaterinburg',
            },
            'end': {
                'dateTime': end_ti,
                # 'timeZone': 'Asia/Yekaterinburg',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
            'id': event_id,
        }
        return event

    def create_event(self, event):
        e = self.service.events().insert(calendarId=calendarId, body=event).execute()
        return e

    async def get_events_id(self, message):
        start_time = datetime.datetime.today()
        end_time = start_time + datetime.timedelta(days=51)
        start_ti2 = start_time.strftime('%Y-%m-%dT%H:%M:%S+05:00')
        end_ti2 = end_time.strftime('%Y-%m-%dT%H:%M:%S+05:00')
        events_res = self.service.events().list(calendarId=calendarId, timeMin=start_ti2, timeMax=end_ti2,
                                                singleEvents=True,
                                                orderBy='startTime').execute()
        events = events_res.get('items', [])
        print(events)

        for event in events:
            if str(message.chat.id) in event['id']:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start)
                eve = event['id']
                print('Пытаюсь удалить')
                self.service.events().delete(calendarId=calendarId,
                                             eventId=eve).execute()
                print('событие удалено')
                await bot.send_message(message.chat.id, f'Ваша запись {start} отменена')

    async def get_events_list2(self, message):
        first_time = '8:00'
        book1 = [get_dict(message)["booking_day"], first_time]
        print(book1)
        book2 = ' '.join(book1)
        print(book2)
        start_day = datetime.datetime.strptime(book2, '%d.%m.%Y %H:%M')
        end_day = start_day + datetime.timedelta(hours=12)
        end_d = end_day.strftime('%Y-%m-%dT%H:%M:%S+05:00')
        start_d = start_day.strftime('%Y-%m-%dT%H:%M:%S+05:00')
        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=start_d, timeMax=end_d,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        btns = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00']
        for event in events:
            for btn in btns[:]:
                if btn in event['start']['dateTime']:
                    btns.remove(btn)
        print(btns)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
        for btn in btns:
            btn = types.KeyboardButton(btn)
            print(btn)
            markup.add(btn)

        markup.add(wrong_date, back)
        await bot.send_message(message.chat.id, f'Доступное время на {get_dict(message)["booking_day"]}:',
                               reply_markup=markup)
        if len(btns) == 0:
            time.sleep(1)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            markup.add(wrong_date, back)
            await bot.send_message(message.chat.id, f'К сожалению {get_dict(message)["booking_day"]} все уже занято',
                                   reply_markup=markup)


calendar = GoogleCalendar()
