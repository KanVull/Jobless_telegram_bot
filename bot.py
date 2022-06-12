import telebot
import random
import os
import time

import logger
import db_connect

TELEBOT_ACCESS_TOKEN = os.environ.get('token')
DATABASE_URL = os.environ.get('DATABASE_URL') 

bot = telebot.TeleBot(TELEBOT_ACCESS_TOKEN, parse_mode=False)
DB = db_connect.DB_work(DATABASE_URL)

chat_id = None


def _gamePlus1_add(user_id, chat_id, user_name):
    state = DB.update_gameplus1(user_id)
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
            sticker_state = DB.random_sticker_answer()
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


@bot.message_handler(regexp='^(dice)$')
@bot.message_handler(regexp='^(дайс)$')
@bot.message_handler(commands=['dice'])
def throw_dice(message):
    dices = { '🎯': 'darts', '🎲': 'dice', '🏀': 'basketball', '⚽': 'soccer', '🎳': 'bowl', '🎰': 'slots'}
    dice = random.choice(list(dices.keys()))
    value = bot.send_dice(message.chat.id, dice)
    value = value.dice
    logger.log_info(f'{message.from_user.first_name} roll the Dice event | {dices[dice]}')
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(2)
    match value.emoji:
        case '🎯':
            if value.value == 6:
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEU8adipe5aytwbEZx44NxBptsOdsMuqQACUhQAAjmtyEujIyiczfmW-CQE')
                logger.log_extrainfo('\tThrow 6 - great')
            elif value.value == 1:
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEU8alipe7OabjAdSiFqxeSOY0zE-Y_lQACiAADZaIDLAhqiFNzxo_2JAQ')
                logger.log_extrainfo('\tMissed')
        case '🎲':
            if value.value == 1:
                bot.send_message(message.chat.id, text='Ну раз такое дело, пойду проверю, можешь ли ты добавить +1')
                logger.log_extrainfo('\tMaking +1 by rolling the dice')
                _gamePlus1_add(str(message.from_user.id), message.chat.id, message.from_user.first_name)
        case '🏀':
            if value.value in [4, 5]:
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ')
                logger.log_extrainfo('\tMaking dunk')
        case '⚽':
            if value.value in [4, 5]:
                stickers = [
                    'CAACAgIAAxkBAAEE-iRipfC9yVqeGn8Yts0Zy_tRBbtUeQACjQADZaIDLN3pznh1PLF1JAQ',
                    'CAACAgIAAxkBAAEE-iZipfDeXE5xad8LNUWgcpM2GWHdiAACgAADZaIDLAABdrRv40DuhyQE',
                    'CAACAgIAAxkBAAEE-ihipfDthzT_3qRWEjrbWeZ5gAtoAgACrQADZaIDLGDZ_6CCKHo7JAQ',
                ]
                bot.send_sticker(message.chat.id, sticker=random.choice(stickers))
                logger.log_extrainfo('\tGOOOOOAL')
        case '🎳':
            if value.value == 6:
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ') 
                logger.log_extrainfo('\tHit the strike') 
            if value.value == 1:
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAP8YqX_AAENorYKnbSHVTh2Y0eonKqvAAJ4DwAC_jrxSFUDk4te2W5WJAQ')
                logger.log_extrainfo('\tMissed') 
        case '🎰':
            if value.value == 64:
                bot.send_message(message.chat.id, text='!!!JACKPOT!!!')
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEE6AZimgghrbnEEo03sTl0JCnoHL-0NgACdBkAAlXI4Uu6jVZRP85VwCQE')
                logger.log_extrainfo('\tWinning jackpot WOW') 
            elif value.value in [43, 22, 1]:
                bot.send_message(message.chat.id, text='Не Jackpot, но блин тоже круто')
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEE_SZipgIAATrAnoBK4mz1-r9iULfgYTMAAhQWAAKAF8lL3tI17cAg9wEkBA')
                logger.log_extrainfo('\tThree in the row')  
            else:
                bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAEE6BpimgihzCGdTjyxel5uFJDZfqwI9AACjRMAArwbyUvBk3xJQsTnBSQE')
                logger.log_extrainfo('\tNothing spetial')                       


@bot.message_handler(regexp=r'^(\+1)$')
@bot.message_handler(commands=['plus'])
def gamePlus1_byCommand(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    _gamePlus1_add(user_id, chat_id, user_name)     


@bot.message_handler(regexp=r'^[0-9]')
def echo(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    logger.log_info(f'reply for number for {user_name}')
    bot.send_message(chat_id=chat_id, text=f'{user_name}, ладно')


@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    chat_id = photo.chat.id
    user_name = photo.from_user.first_name
    number = random.randint(0,10)
    logger.log_info(f'photo gain {number} for {user_name}')
    if number == 4:
        logger.log_extrainfo(f'reply to photo for {user_name} in text mode')
        message = DB.random_text_answer()
        bot.send_message(chat_id=chat_id, text=f'{user_name}, {message}')
    elif number in [8,9]:
        logger.log_extrainfo(f'reply to photo for {user_name} in sticker mode')
        sticker = DB.random_sticker_answer()
        bot.send_sticker(chat_id=chat_id, sticker=sticker)


@bot.message_handler(content_types=['video_note'])
def send_circle_reaction(video_note):
    chat_id = video_note.chat.id
    user_name = video_note.from_user.first_name
    number = random.randint(0,10)
    logger.log_info(f'video_note gain {number} for {user_name}')
    if number in [0,3,5,7]:
        logger.log_extrainfo(f'reply to video_note for {user_name} in text mode')
        sticker = DB.random_sticker_answer()
        bot.send_sticker(chat_id=chat_id, sticker=sticker)

        
logger.log_info(f'bot start\n')

bot.infinity_polling()