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

balance_rules = {
    'pay': {
        'dice': 3,
    },
    'add': {
        'dice': {
            'darts': 9,
            'dice5': 5,
            'dice6': 6,
            'basketball': 5,
            'soccer': 4,
            'bowl': 9,
            'slots': 48,
            'slots777': 300,
        },
        'answers': {
            'photo': 2,
            'video_note': 1
        }
        
    }
}

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
    logger.log_extrainfo(f'\t\tscore: {state[1]}')
    
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
            logger.log_extrainfo(logger_message)
            bot.send_message(chat_id=chat_id, text=message)
        if sticker_state is not None:
            bot.send_sticker(chat_id=chat_id, sticker=sticker_state)

def _add_balance(user_id, chat_id, user_name, amount):
    DB.add_balance(user_id, amount)
    match str(amount)[-1]:
        case '1':
            message_ending = ''
        case '2' | '3' | '4':
            message_ending = 'а'
        case _:
            message_ending = 'ов' 
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, тебе на счёт капнуло {amount} прикол{message_ending}!',
        disable_notification=True
    )
    logger.log_extrainfo(f"\tAdded {amount} to balance")


@bot.message_handler(regexp='^(баланс)$')
@bot.message_handler(commands=['balance'])
def get_balance(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    amount = DB.get_balance(user_id)
    match str(amount)[-1]:
        case '1':
            message_ending = ''
        case '2' | '3' | '4':
            message_ending = 'а'
        case _:
            message_ending = 'ов'        
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, у тебя {amount} прикол{message_ending}!',
        disable_notification=True
    )
    logger.log_info(f"{user_name} get_balance: {amount}")

@bot.message_handler(regexp='^(приколы)$')
def balance_info(message):
    bot.send_message(
        chat_id=message.chat.id,
        text = f'''
            Заработать приколы можно следующими способами:\n 
            - Если бот ответит тебе на картинку, тебе на счёт капнет - {balance_rules['add']['answers']['photo']}\n
            - Если бот ответит на кружок, на счету появится - {balance_rules['add']['answers']['video_note']}\n
            Также, если ты кидаешь дайс, есть вероятность, что выпадет, что-то хорошее, тогда тебе на счёт придут приколы\n\n
            Пока что это все возможности баланса.
        ''',
        disable_notification=True
    )
    logger.log_info(f'{message.from_user.first_name} enters Приколы')

@bot.message_handler(regexp='^(dice)$')
@bot.message_handler(regexp='^(дайс)$')
@bot.message_handler(commands=['dice'])
def throw_dice(message):
    if not DB.pay_balance(message.from_user.id, balance_rules['pay']['dice']):
        bot.send_message(
            message.chat.id, 
            text=f"Недостаточно средств для броска(\n Стоимость: {balance_rules['pay']['dice']}\nВведи \"Приколы\", чтобы узнать как их заработать", 
            disable_notification=True
        )
        logger.log_info(f'{message.from_user.first_name} doesn\'t have enough balance to dice')
        return None

    dices = { '🎯': 'darts', '🎲': 'dice', '🏀': 'basketball', '⚽': 'soccer', '🎳': 'bowl', '🎰': 'slots'}
    dice = random.choice(list(dices.keys()))
    value = bot.send_dice(
        message.chat.id, 
        dice, 
        disable_notification=True
    )
    value = value.dice
    logger.log_info(f'{message.from_user.first_name} roll the Dice event | {dices[dice]}')
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(2)
    match value.emoji:
        case '🎯':
            if value.value == 6:
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAEU8adipe5aytwbEZx44NxBptsOdsMuqQACUhQAAjmtyEujIyiczfmW-CQE',
                    disable_notification=True
                )
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice']['darts'])
                logger.log_extrainfo('\tThrow 6 - great')
            elif value.value == 1:
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAEU8alipe7OabjAdSiFqxeSOY0zE-Y_lQACiAADZaIDLAhqiFNzxo_2JAQ', 
                    disable_notification=True
                )
                logger.log_extrainfo('\tMissed')
        case '🎲':
            if value.value == 1:
                bot.send_message(
                    message.chat.id, 
                    text='Ну раз такое дело, пойду проверю, можешь ли ты добавить +1', 
                    disable_notification=True
                )
                logger.log_extrainfo('\tMaking +1 by rolling the dice')
                _gamePlus1_add(str(message.from_user.id), message.chat.id, message.from_user.first_name)
            if value.value in [5, 6]:
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice'][f'dice{value.value}'])

        case '🏀':
            if value.value in [4, 5]:
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ',
                    disable_notification=True
                )
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice']['basketball'])
                logger.log_extrainfo('\tMaking dunk')
        case '⚽':
            if value.value in [4, 5, 6]:
                stickers = [
                    'CAACAgIAAxkBAAEE-iRipfC9yVqeGn8Yts0Zy_tRBbtUeQACjQADZaIDLN3pznh1PLF1JAQ',
                    'CAACAgIAAxkBAAEE-iZipfDeXE5xad8LNUWgcpM2GWHdiAACgAADZaIDLAABdrRv40DuhyQE',
                    'CAACAgIAAxkBAAEE-ihipfDthzT_3qRWEjrbWeZ5gAtoAgACrQADZaIDLGDZ_6CCKHo7JAQ',
                ]
                bot.send_sticker(
                    message.chat.id, 
                    sticker=random.choice(stickers),
                    disable_notification=True
                )
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice']['soccer'])
                logger.log_extrainfo('\tGOOOOOAL')
        case '🎳':
            if value.value == 6:
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ',
                    disable_notification=True
                )
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice']['bowl']) 
                logger.log_extrainfo('\tHit the strike') 
            if value.value == 1:
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAP8YqX_AAENorYKnbSHVTh2Y0eonKqvAAJ4DwAC_jrxSFUDk4te2W5WJAQ',
                    disable_notification=True
                )
                logger.log_extrainfo('\tMissed') 
        case '🎰':
            if value.value == 64:
                bot.send_message(
                    message.chat.id, 
                    text='!!!JACKPOT!!!',
                    disable_notification=True
                )
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAEE6AZimgghrbnEEo03sTl0JCnoHL-0NgACdBkAAlXI4Uu6jVZRP85VwCQE',
                    disable_notification=True
                )
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice']['slots777'])
                logger.log_extrainfo('\tWinning jackpot WOW') 
            elif value.value in [43, 22, 1]:
                bot.send_message(
                    message.chat.id, 
                    text='Не Jackpot, но блин тоже круто',
                    disable_notification=True
                )
                bot.send_sticker(
                    message.chat.id, 
                    sticker='CAACAgIAAxkBAAEE_SZipgIAATrAnoBK4mz1-r9iULfgYTMAAhQWAAKAF8lL3tI17cAg9wEkBA',
                    disable_notification=True
                )
                _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['dice']['slots'])
                logger.log_extrainfo('\tThree in the row') 
            else:
                if random.randint(0,5) == 0:
                    bot.send_sticker(
                        message.chat.id, 
                        sticker='CAACAgIAAxkBAAEE6BpimgihzCGdTjyxel5uFJDZfqwI9AACjRMAArwbyUvBk3xJQsTnBSQE',
                        disable_notification=True
                    )
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
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, {message}',
            disable_notification=True
        )
    elif number == 8:
        logger.log_extrainfo(f'reply to photo for {user_name} in sticker mode')
        sticker = DB.random_sticker_answer()
        bot.send_sticker(
            chat_id=chat_id, 
            sticker=sticker,
            disable_notification=True
        )
    if number in [4,8]:
        _add_balance(message.from_user.id, message.chat.id, message.from_user.first_name, balance_rules['add']['answers']['photo'])   


@bot.message_handler(content_types=['video_note'])
def send_video_note_reaction(video_note):
    chat_id = video_note.chat.id
    user_name = video_note.from_user.first_name
    number = random.randint(0,10)
    logger.log_info(f'video_note gain {number} for {user_name}')
    if number in [0,3,5,7]:
        logger.log_extrainfo(f'reply to video_note for {user_name} in text mode')
        sticker = DB.random_sticker_answer()
        bot.send_sticker(
            chat_id=chat_id, 
            sticker=sticker,
            disable_notification=True
        )
        _add_balance(video_note.from_user.id, chat_id, user_name, balance_rules['add']['answers']['video_note']) 

        
logger.log_info(f'bot start\n')

bot.infinity_polling()