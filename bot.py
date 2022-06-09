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

@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    chat_id = photo.chat.id
    number = random.randint(0,101)
    user_name = photo.from_user.first_name
    logger.log_info(f'photo gain {number} for {user_name}')
    if number % 20 == 0:
        with open(files['photo_text_answers'], 'r') as file:
            logger.log_info(f'reply to photo for {user_name} in text mode')
            lines = file.readlines()
            bot.send_message(chat_id=chat_id, text=f'{user_name}, {random.choice(lines)}')
    elif (number+10) % 20 == 0:
        with open(files['photo_sticker_answers'], 'r') as file:
            logger.log_info(f'reply to photo for {user_name} in sticker mode')
            lines = file.readlines()
            bot.send_sticker(photo.chat.id, random.choice(lines))

@bot.message_handler(regexp=r'^[0-9]')
def echo(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    logger.log_info(f'reply for number for {user_name}')
    bot.send_message(chat_id=chat_id, text=f'{user_name}, ладно')

def game_plus1(chat_id):
    score = int(config_data['games']['GAMES']['plus1']) + 1
    config_data['games']['GAMES']['plus1'] = str(score)
    config_worker.save_config(config_data['games'], 'games')  
    
    if score % 1000 == 0:
        logger.log_info(f'game +1 gain another 1000')
        bot.send_message(chat_id=chat_id, text=f'!!!{score}!!!\nНу и нечем конечно заняться парням')
    elif score % 50 == 0:
        logger.log_info(f'game +1 gain another 50')
        bot.send_message(chat_id=chat_id, text=f'Командными усильями этот счётчик теперь {score}')

@bot.message_handler(regexp=r'^(\+1)$')
def gamePlus1(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    state = db_cn.update_gameplus1(user_id)
    user_name = message.from_user.first_name
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
        if state[1] % 1000 == 0:
            logger.log_info(f'game +1 gain another 1000')
            bot.send_message(chat_id=chat_id, text=f'!!!{state[1]}!!!\nНу и нечем конечно заняться парням')
    elif state[1] % 50 == 0:
            logger.log_info(f'game +1 gain another 50')
            bot.send_message(chat_id=chat_id, text=f'Командными усильями этот счётчик теперь {state[1]}')

logger.log_info(f'bot start\n')

bot.infinity_polling()