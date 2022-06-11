import telebot
import random
import os

import config_worker
import logger
import db_connect

TELEBOT_ACCESS_TOKEN = os.environ.get('token')
DATABASE_URL = os.environ.get('DATABASE_URL') 

bot = telebot.TeleBot(TELEBOT_ACCESS_TOKEN, parse_mode=False)
db_cn = db_connect.DB_gameplus1_work(DATABASE_URL)
config_data = config_worker.check_enviroment()

chat_id = None
config = None
games = None
files = {
    'photo_text_answers': './nicelist.txt',
    'photo_sticker_answers': './stickers.txt'
}

def mem_of_a_day(time):
    pass

def dice():
    bot.send_dice()

@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    chat_id = photo.chat.id
    number = random.randint(0,100)
    user_name = photo.from_user.first_name
    logger.log_info(f'photo gain {number} for {user_name}')
    if number % 20 == 0:
        with open(files['photo_text_answers'], 'r') as file:
            logger.log_info(f'reply to photo for {user_name} in text mode')
            lines = file.readlines()
            message = random.choice(lines).replace('\n', '')
            bot.send_message(chat_id=chat_id, text=f'{user_name}, {message}')
    elif (number+10) % 20 == 0:
        with open(files['photo_sticker_answers'], 'r') as file:
            logger.log_info(f'reply to photo for {user_name} in sticker mode')
            lines = file.readlines()
            sticker = random.choice(lines).replace('\n', '')
            bot.send_sticker(chat_id=chat_id, sticker=sticker)

@bot.message_handler(regexp=r'^[0-9]')
def echo(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    logger.log_info(f'reply for number for {user_name}')
    bot.send_message(chat_id=chat_id, text=f'{user_name}, ладно')

def _gamePlus1_add(user_id, chat_id, user_name):
    state = db_cn.update_gameplus1(user_id)
    match state[0]:
        case 1:
            message = 'засчитано'
        case 2:
            message = 'скоро начнёшь превышать.\nЭто зачту'
        case 3:
            message = 'слушай, я же тебя просил. Засчитываю последний раз.'
        case _:
            message = 'чел, (T_T) Жди других'            
    bot.send_message(chat_id=chat_id, text=f'{user_name}, {message}')
    
    logger.log_info(f'game +1 making for {user_name}')
    logger.log_info(f'\t\tscore: {state[1]}')
    
    if state[0] < 4:
        sticker_state = None
        logger_message = None
        if state[1] in [228, 256, 322, 420, 512, 666, 777, 1001, 1024, 1337, 1488, 2048]:
            logger_message = f'game +1 gain specific {state[1]} score'
            message = f'{state[1]} насчитали\nЩиииииииииии'
            with open(files['photo_sticker_answers'], 'r') as file:
                logger.log_info(f'gaining sticker for {state[1]} score')
                lines = file.readlines()
                sticker_state = random.choice(lines).replace('\n', '')
        elif state[1] % 1000 == 0:
            logger_message = f'game +1 gain another 1000'
            message = f'!!!{state[1]}!!!\nНу и нечем конечно заняться парням'
        elif state[1] % 50 == 0:
            logger_message = f'game +1 gain another 50'
            message = f'Командными усильями этот счётчик теперь {state[1]}'

        if logger_message is not None:
            logger.log_info(logger_message)
            bot.send_message(chat_id=chat_id, text=message)
        if sticker_state is not None:
            bot.send_sticker(chat_id=chat_id, sticker=sticker_state)

@bot.message_handler(regexp=r'^(\+1)$')
@bot.message_handler(commands=['plus'])
def gamePlus1_byCommand(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    _gamePlus1_add(user_id, chat_id, user_name)     

logger.log_info(f'bot start\n')

bot.infinity_polling()