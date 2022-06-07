import telebot
import configparser

config_file = configparser.ConfigParser()
config_file.read('config.cfg')
bot = telebot.TeleBot(config_file['BOT_SETTINGS']['Token'], parse_mode=False)

config_schedule = configparser.ConfigParser()
config_schedule.read('config_schedule.cfg')

def Pasha():
    bot.send_message(chat_id=photo.chat.id, text=f'{user_name}, отлично фото. Это ты в детстве?')

def Matvey():
    bot.send_message(chat_id=message.chat.id, text=f'{user_name}, ладно')

def Roma():


while True:
