from typing import List, Tuple
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
            'slots': 60,
            'slots777': 300,
        },
        'answers': {
            'photo': 3,
            'video': 5,
            'voice': 2,
            'sticker': 1,
        }
        
    }
}

def _get_chat_user_info(messageObject: telebot.types.Message) -> Tuple[str, str, str]:
    chat_id = messageObject.chat.id
    user_id = str(messageObject.from_user.id)
    user_name = messageObject.from_user.first_name
    return (chat_id, user_id, user_name)

def _gamePlus1_add(user_id: str, chat_id: str, user_name: str) -> None:
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
    logger.log_extrainfo(f'score: {state[1]}')
    
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

def _add_balance(user_id: str, chat_id: str, user_name: str, amount: int) -> None:
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
    logger.log_extrainfo(f"Added {amount} to balance")

def _random(rang: List[int], target: List[int]) -> bool:
    ran = random.randint(rang[0], rang[1])
    return ran in target

@bot.message_handler(regexp='^(баланс)$')
@bot.message_handler(commands=['balance'])
def get_balance(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    amount = DB.get_balance(user_id)
    sAmount = str(amount)
    match sAmount[-1]:
        case '1':
            message_ending = ''
        case '2' | '3' | '4':
            message_ending = 'а'
        case _:
            message_ending = 'ов'        
    if len(sAmount) > 1:
        if sAmount[-2:] in ['11', '12', '13', '14']:
            message_ending = 'ов'
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, у тебя {amount} прикол{message_ending}!',
        disable_notification=True
    )
    logger.log_info(f"{user_name} get_balance: {amount}")


@bot.message_handler(regexp='^(приколы)$')
def balance_info(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    bot.send_message(
        chat_id=chat_id,
        text = f'''
Заработать приколы можно следующими способами:

- Если бот ответит тебе на картинку, тебе на счёт капнет - {balance_rules['add']['answers']['photo']}
- Если бот ответит на видео, тебе придёт - {balance_rules['add']['answers']['video']}
- Если бот ответит на кружок или аудио, на счету появится - {balance_rules['add']['answers']['voice']}
- Если бот ответит на стикер, то ты получишь - {balance_rules['add']['answers']['sticker']}
Также, если ты кидаешь дайс, есть вероятность, что выпадет, что-то хорошее, тогда тебе на счёт придут приколы

Пока что это все возможности баланса.
        ''',
        disable_notification=True
    )
    logger.log_info(f'{user_name} enters Приколы')


@bot.message_handler(regexp='^(dice)$')
@bot.message_handler(regexp='^(дайс)$')
@bot.message_handler(commands=['dice'])
def throw_dice(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    if not DB.pay_balance(user_id, balance_rules['pay']['dice']):
        bot.send_message(
            chat_id, 
            text=f"Недостаточно средств для броска(\nСтоимость: {balance_rules['pay']['dice']}\nВведи \"Приколы\", чтобы узнать как их заработать", 
            disable_notification=True
        )
        logger.log_info(f'{user_name} doesn\'t have enough balance to dice')
        return None

    dices = { '🎯': 'darts', '🎲': 'dice', '🏀': 'basketball', '⚽': 'soccer', '🎳': 'bowl', '🎰': 'slots'}
    dice = random.choice(list(dices.keys()))
    value = bot.send_dice(
        chat_id, 
        dice, 
        disable_notification=True
    )
    value = value.dice
    logger.log_info(f'{user_name} roll the Dice event | {dices[dice]}')
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(2)
    match value.emoji:
        case '🎯':
            if value.value == 6:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEU8adipe5aytwbEZx44NxBptsOdsMuqQACUhQAAjmtyEujIyiczfmW-CQE',
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice']['darts'])
                logger.log_extrainfo('Throw 6 - great')
            elif value.value == 1:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEU8alipe7OabjAdSiFqxeSOY0zE-Y_lQACiAADZaIDLAhqiFNzxo_2JAQ', 
                    disable_notification=True
                )
                logger.log_extrainfo('Missed')
        case '🎲':
            if value.value == 1:
                bot.send_message(
                    chat_id, 
                    text='Ну раз такое дело, пойду проверю, можешь ли ты добавить +1', 
                    disable_notification=True
                )
                logger.log_extrainfo('Making +1 by rolling the dice')
                _gamePlus1_add(str(message.from_user.id), message.chat.id, message.from_user.first_name)
            if value.value in [5, 6]:
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice'][f'dice{value.value}'])

        case '🏀':
            if value.value in [4, 5]:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ',
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice']['basketball'])
                logger.log_extrainfo('Making dunk')
        case '⚽':
            if value.value in [4, 5, 6]:
                stickers = [
                    'CAACAgIAAxkBAAEE-iRipfC9yVqeGn8Yts0Zy_tRBbtUeQACjQADZaIDLN3pznh1PLF1JAQ',
                    'CAACAgIAAxkBAAEE-iZipfDeXE5xad8LNUWgcpM2GWHdiAACgAADZaIDLAABdrRv40DuhyQE',
                    'CAACAgIAAxkBAAEE-ihipfDthzT_3qRWEjrbWeZ5gAtoAgACrQADZaIDLGDZ_6CCKHo7JAQ',
                ]
                bot.send_sticker(
                    chat_id, 
                    sticker=random.choice(stickers),
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice']['soccer'])
                logger.log_extrainfo('GOOOOOAL')
        case '🎳':
            if value.value == 6:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ',
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice']['bowl']) 
                logger.log_extrainfo('Hit the strike') 
            if value.value == 1:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAP8YqX_AAENorYKnbSHVTh2Y0eonKqvAAJ4DwAC_jrxSFUDk4te2W5WJAQ',
                    disable_notification=True
                )
                logger.log_extrainfo('Missed') 
        case '🎰':
            if value.value == 64:
                bot.send_message(
                    chat_id, 
                    text='!!!JACKPOT!!!',
                    disable_notification=True
                )
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEE6AZimgghrbnEEo03sTl0JCnoHL-0NgACdBkAAlXI4Uu6jVZRP85VwCQE',
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice']['slots777'])
                logger.log_extrainfo('Winning jackpot WOW') 
            elif value.value in [43, 22, 1]:
                bot.send_message(
                    chat_id, 
                    text='Не Jackpot, но блин тоже круто',
                    disable_notification=True
                )
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEE_SZipgIAATrAnoBK4mz1-r9iULfgYTMAAhQWAAKAF8lL3tI17cAg9wEkBA',
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, balance_rules['add']['dice']['slots'])
                logger.log_extrainfo('Three in the row') 
            else:
                if _random([0,5], [0]):
                    bot.send_sticker(
                        chat_id, 
                        sticker='CAACAgIAAxkBAAEE6BpimgihzCGdTjyxel5uFJDZfqwI9AACjRMAArwbyUvBk3xJQsTnBSQE',
                        disable_notification=True
                    )
                logger.log_extrainfo('Nothing spetial')                       


@bot.message_handler(regexp=r'^(\+1)$')
@bot.message_handler(commands=['plus'])
def gamePlus1_byCommand(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    _gamePlus1_add(user_id, chat_id, user_name)     


@bot.message_handler(regexp=r'^[0-9]')
def echo(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    logger.log_info(f'reply for number for {user_name}')
    bot.send_message(
        chat_id, 
        text=f'{user_name}, ладно',
        disable_notification=True
    )


@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    chat_id, user_id, user_name = _get_chat_user_info(photo)
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
        _add_balance(user_id, chat_id, user_name, balance_rules['add']['answers']['photo'])   


@bot.message_handler(content_types=['video_note', 'voice'])
def send_video_note_reaction(quick_voice_message):
    chat_id, user_id, user_name = _get_chat_user_info(quick_voice_message)
    logger.log_info(f'quick_voice_message gain number for {user_name}')
    if _random([0,10], [0,3,5,7]):
        logger.log_extrainfo(f'reply to quick_voice_message for {user_name} in text mode')
        sticker = DB.random_sticker_answer()
        bot.send_sticker(
            chat_id=chat_id, 
            sticker=sticker,
            disable_notification=True
        )
        _add_balance(user_id, chat_id, user_name, balance_rules['add']['answers']['voice']) 


@bot.message_handler(content_types=['sticker'])
def sticker_answer(sticker):
    chat_id, user_id, user_name = _get_chat_user_info(sticker)
    logger.log_info(f'sticker gain number for {user_name}')
    if _random([0,15], [7]):
        logger.log_extrainfo(f'reply to sticker for {user_name}')
        _add_balance(user_id, chat_id, user_name, balance_rules['add']['answers']['sticker']) 
  


logger.log_info(f'bot start\n')

bot.infinity_polling()