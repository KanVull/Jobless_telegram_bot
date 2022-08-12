from typing import List, Tuple
import telebot
import random
import os
import time

import logger
import db_connect
import economy
import filter


###################################################################
##                        Configuration                          ##
###################################################################

TELEBOT_ACCESS_TOKEN = os.environ.get('token')
DATABASE_URL = os.environ.get('DATABASE_URL') 

bot = telebot.TeleBot(TELEBOT_ACCESS_TOKEN, parse_mode=False)
DB = db_connect.DB_work(DATABASE_URL)
e = economy.Economy()
F = filter.Filter()

chat_id = None


###################################################################
##                      Private functions                        ##
###################################################################

def _readble_amount_name(amount):
    sAmount = str(amount)
    if len(sAmount) > 6 :
        return 'преколов'
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
    return 'прекол' + message_ending        

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
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, {message}',
        disable_notification=True
    )
    
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
            bot.send_message(
                chat_id=chat_id, 
                text=message,
                disable_notification=True
            )
        if sticker_state is not None:
            bot.send_sticker(
                chat_id=chat_id, 
                sticker=sticker_state,
                disable_notification=True
            )

def _add_balance(user_id: str, chat_id: str, user_name: str, amount: float) -> None:
    DB.add_balance(user_id, amount)   
    r_a = e.readble_amount(amount)
    balance = DB.get_balance(user_id)
    r_balance = e.readble_amount(balance)
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, + кошелёк: {r_a} {_readble_amount_name(amount)}!\nВ кошельке: {r_balance}',
        disable_notification=True
    )
    logger.log_extrainfo(f"Added {e.readble_amount(r_a)} to balance: {e.readble_amount(balance - amount)} -> {r_balance}")

def _random(percent: List[int]) -> int:
    ran = random.random() * 100
    percent = [0] + percent
    for i in range(1, len(percent)):
        percent[i] += percent[i-1]
    count = 0
    for per in percent:
        if ran < per:
            return count
        count += 1
    return 0       


###################################################################
##                   New user and random stuff                   ##
###################################################################

@bot.message_handler(content_types=["new_chat_members"])
@bot.message_handler(commands=['start'])
def new_member(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    welcome_bonus = 30.0
    if DB.add_user(user_id, user_name, welcome_bonus):
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, Добро пожаловать!\nПриветственный бонус {e.readble_amount(welcome_bonus)} {_readble_amount_name(welcome_bonus)}. \
Введи "Преколы" или команду /prekoli, чтобы посмотреть как их тратить и зарабатывать',
            disable_notification=True
        )
        bot.send_sticker(
            chat_id, 
            sticker='CAACAgIAAxkBAAEWkuti5qorkIqeTaeX0iC_TQQoI6DzqAACXRUAAmyuUEhG7eTQjfA7RykE',
            disable_notification=True
        )
        logger.log_info(f"{user_name} our new user!")
    else:
        user_level_buff = DB.get_level_buff(user_id)
        balance = DB.get_balance(user_id)
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, Добро пожаловать!\nТак как ты уже пользователь батона, то весь твой прогресс будет действовать и здесь\n\
У тебя {e.readble_amount(balance)} {_readble_amount_name(balance)}. Уровень {user_level_buff[0]}.\nТы - {user_level_buff[1]}!\n\
Твой бафф: x{e.readble_amount(user_level_buff[2])}',
            disable_notification=True
        )

@bot.message_handler(regexp=r'^(\+1)$')
@bot.message_handler(commands=['plus'])
def gamePlus1_byCommand(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    _gamePlus1_add(user_id, chat_id, user_name)     

@bot.message_handler(regexp=r'^[0-9]')
def echo(message):
    chat_id, _, user_name = _get_chat_user_info(message)
    logger.log_info(f'reply for number for {user_name}')
    bot.send_message(
        chat_id, 
        text=f'{user_name}, ладно',
        disable_notification=True
    )

@bot.message_handler(regexp='(перд|пёрд|окак|акак|кек|пук|сру|сри|сра|срё|fart|дрист)')
def fart_noice_voice_message(message):
    chat_id, _, user_name = _get_chat_user_info(message)
    fart = DB.random_fart()
    logger.log_info(f'{user_name} farted (o_0)')
    bot.send_voice(
        chat_id, 
        voice=fart,
        disable_notification=True
    )

###################################################################
##                       User information                        ##
###################################################################

@bot.message_handler(regexp='^(баланс)$')
@bot.message_handler(commands=['balance'])
def get_balance(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    amount = DB.get_balance(user_id)
    rAmount = e.readble_amount(amount)
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, у тебя {rAmount} {_readble_amount_name(amount)}!',
        disable_notification=True
    )
    logger.log_info(f"{user_name} get_balance: {rAmount}")

@bot.message_handler(regexp='^(уровень)$')
@bot.message_handler(regexp='^(level)$')
@bot.message_handler(commands=['level'])
def show_level(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    user_level__name = DB.get_level_buff(user_id)
    can_you_buy_a_new_level = DB.level_up_check(user_id)
    if not can_you_buy_a_new_level:
        support_message = 'У тебя максимальный уровень на данный момент'
    else:
        level_cost = e.level_cost(user_level__name[0] + 1)
        support_message = f'Следующий уровень стоит {e.readble_amount(level_cost)} {_readble_amount_name(level_cost)}\n\
Чтобы купить, введи "Купить уровень" или /level_buy'    
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, ты - {user_level__name[1]}!\nУ тебя {user_level__name[0]} уровень\n{support_message}',
        disable_notification=True
    )
    logger.log_info(f"{user_name} show the level: {user_level__name[0]} - {user_level__name[1]}")

@bot.message_handler(regexp='^(бафф)$')
@bot.message_handler(commands=['buff'])
def show_available_buff(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    buff, next_buff = DB.get_buff_info(user_id)
    mess = f'Твой бафф: x{buff}\nУвеличивает всё, кроме стоимости уровня.\n'
    if next_buff is None:
        mess += 'Ты купил последний на данный момент бафф'
    else:
        mess += f'Следующий бафф даст тебе: x{next_buff[1]}\nСтоит: {e.readble_amount(next_buff[0])}\n\
Чтобы купить введи "Купить бафф" или команду /buff_buy'
    bot.send_message(
        chat_id=chat_id, 
        text=mess,
        disable_notification=True
    )    
    logger.log_info(f'{user_name} gets buff info')

@bot.message_handler(regexp='^(преколы)$')
@bot.message_handler(commands=['prekoli'])
def prekoli_info(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    user_level_buff = DB.get_level_buff(user_id)
    x = user_level_buff[2]
    if x == 1:
        buff_info = f'У тебя сейчас неактивны баффы, купи один.'
    else:
        buff_info = f'Твой бафф: x{e.readble_amount(user_level_buff[2])}.'    
    bot.send_message(
        chat_id=chat_id,
        text =\
              
f'''Преколы это внутриботовая валюта.
Свой баланс можно посмотреть командой "Баланс" или /balance.
Её можно тратить на покупку уровня и азартную игру Дайс, где ты можешь выиграть преколов (или проиграть).
Введи команду "Уровень" или /level, чтобы посмотреть информацию о данной системе.
Введи команду "Дайс" или /dice, чтобы поиграть своей удачей!
Введи команду "Бафф" или /buff, чтобы посмотреть улучшение, которое ты можешь купить.

У тебя сейчас {user_level_buff[0]} уровень.
{buff_info}
Получить преколы можно следующими способами:

- Картинка: {e.readble_amount(e.get_reward('photo', user_level_buff[0], x))}
- Видео: {e.readble_amount(e.get_reward('video', user_level_buff[0], x))}
- Голосовое или кружок: {e.readble_amount(e.get_reward('voice', user_level_buff[0], x))}
- Стикер: {e.readble_amount(e.get_reward('sticker', user_level_buff[0], x))}

Дайс стоит: {e.readble_amount(e.get_pay_price('dice', user_level_buff[0], x))}''',\
            
        disable_notification=True
    )
    logger.log_info(f'{user_name} enters Преколы')


###################################################################
##                       Buy opportunities                       ##
###################################################################

@bot.message_handler(regexp='^(купить уровень)$')
@bot.message_handler(commands=['level_buy'])
def buy_level(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    can_you_buy_a_new_level = DB.level_up_check(user_id)
    if not can_you_buy_a_new_level:
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, у тебя максимальный на данный момент уровень\nСкоро добавлю новых уровней',
            disable_notification=True
        )
        bot.send_sticker(
            chat_id, 
            sticker='CAACAgIAAxkBAAEWkmti5pwBcvbEMlO3nNLFpdGmcnOqiAACIAADlUdhIFuwllN9RkoBKQQ',
            disable_notification=True
        )
        logger.log_info(f"{user_name} trying to buy a level when the level is already max")
    else:
        user_level__name = DB.get_level_buff(user_id)
        level_cost = e.level_cost(user_level__name[0] + 1)
        if not DB.pay_balance(user_id, level_cost):
            bot.send_message(
                chat_id, 
                text=f"Недостаточно средств для покупки уровня(\nСтоимость следующего уровня: \
{e.readble_amount(level_cost)}\nТебе не хватает {e.readble_amount(level_cost - DB.get_balance(user_id))}", 
                disable_notification=True
            )
            logger.log_info(f'{user_name} doesn\'t have enough balance to level_up')
            return None
        DB.level_up(user_id)
        user_level__name = DB.get_level_buff(user_id)    
        can_you_buy_a_new_level = DB.level_up_check(user_id)
        if can_you_buy_a_new_level:
            level_cost = e.level_cost(user_level__name[0] + 1)
            support_message = f'Следующий уровень будет стоить {e.readble_amount(level_cost)} {_readble_amount_name(level_cost)}'
        else:
            support_message = f'Это максимальный на данный момент уровень'    
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, поздравляю, теперь у тебя {user_level__name[0]} уровень.\nТы - {user_level__name[1]}\n{support_message}',
            disable_notification=True
        )
        logger.log_info(f"{user_name} rise level to {user_level__name[0]}")
        logger.log_extrainfo(f"Now the level is {user_level__name[1]}")

@bot.message_handler(regexp='^(купить бафф)$')
@bot.message_handler(commands=['buff_buy'])
def buy_buff(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    buff, next_buff = DB.get_buff_info(user_id)
    if next_buff is None:
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, ты купил последний на данный момент бафф',
            disable_notification=True
        )
        bot.send_sticker(
            chat_id, 
            sticker='CAACAgIAAxkBAAEWkmti5pwBcvbEMlO3nNLFpdGmcnOqiAACIAADlUdhIFuwllN9RkoBKQQ',
            disable_notification=True
        )
        logger.log_info(f"{user_name} trying to buy a buff when there is not available buff")
    else:
        if not DB.pay_balance(user_id, next_buff[0]):
            bot.send_message(
                chat_id, 
                text=f"Недостаточно средств для покупки баффа(\nСтоимость баффа: \
{e.readble_amount(next_buff[0])}\nТебе не хватает {e.readble_amount(next_buff[0] - DB.get_balance(user_id))}", 
                disable_notification=True
            )
            logger.log_info(f'{user_name} doesn\'t have enough balance to buff_buy')
            return None
        
        name_of_buff = DB.buff_buy(user_id)
        buff, next_buff = DB.get_buff_info(user_id)
        if next_buff is not None:
            support_message = f'Следующий бафф будет стоить {e.readble_amount(next_buff[0])}\
 {_readble_amount_name(next_buff[0])} и добавит тебе x{e.readble_amount(next_buff[1])} к текущему улучшению.'
        else:
            support_message = f'Ты купил максимальный на данный момент бафф'    
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, ты купил бафф:\n{name_of_buff}\nТеперь у тебя бафф: x{e.readble_amount(buff)}\n{support_message}',
            disable_notification=True
        )
        logger.log_info(f"{user_name} buys a buff {name_of_buff}")
        logger.log_extrainfo(f"Now the buff is x{e.readble_amount(buff)}")

@bot.message_handler(regexp='^(dice)$')
@bot.message_handler(regexp='^(дайс)$')
@bot.message_handler(commands=['dice'])
def buy_dice(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    level, _, buff = DB.get_level_buff(user_id)
    pay_price = e.get_pay_price('dice', level, buff)
    if not DB.pay_balance(user_id, pay_price):
        balance = DB.get_balance(user_id)
        bot.send_message(
            chat_id, 
            text=f'Нет преколов(\nНадо: {e.readble_amount(pay_price)}\nА у тебя: {e.readble_amount(balance)}', 
            disable_notification=True
        )
        logger.log_info(f'{user_name} doesn\'t have enough balance to dice')
        return None

    dices = { 
        '🎯': 'darts', 
        '🎲': 'dice', 
        '🏀': 'basketball', 
        '⚽': 'soccer', 
        '🎳': 'bowl', 
        '🎰': 'slots'
    }
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
                _add_balance(user_id, chat_id, user_name, e.get_reward('darts', level, buff))
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
                    text='Выкинул +1', 
                    disable_notification=True
                )
                logger.log_extrainfo('Making +1 by rolling the dice')
                _gamePlus1_add(user_id, chat_id, user_name)
            if value.value in [5, 6]:
                _add_balance(user_id, chat_id, user_name, e.get_reward(f'dice{value.value}', level, buff))

        case '🏀':
            if value.value in [4, 5]:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ',
                    disable_notification=True
                )
                _add_balance(user_id, chat_id, user_name, e.get_reward('basketball', level, buff))
                logger.log_extrainfo('Making dunk')
        case '⚽':
            if value.value in [3, 4, 5]:
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
                _add_balance(user_id, chat_id, user_name, e.get_reward('soccer', level, buff))
                logger.log_extrainfo('GOOOOOAL')
        case '🎳':
            match value.value:
                case 6:
                    bot.send_sticker(
                        chat_id, 
                        sticker='CAACAgIAAxkBAAEU8btipe_6kxUpjQG7OtXDzR8h9FMYkQACpAADZaIDLGZNvZNIbiHXJAQ',
                        disable_notification=True
                    )
                    _add_balance(user_id, chat_id, user_name, e.get_reward('bowl', level, buff)) 
                    logger.log_extrainfo('Hit the strike') 
                case 1:
                    bot.send_sticker(
                        chat_id, 
                        sticker='CAACAgIAAxkBAAP8YqX_AAENorYKnbSHVTh2Y0eonKqvAAJ4DwAC_jrxSFUDk4te2W5WJAQ',
                        disable_notification=True
                    )
                    logger.log_extrainfo('Missed') 
                case _:
                    pass    
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
                _add_balance(user_id, chat_id, user_name, e.get_reward('slots777', level, buff))
                logger.log_extrainfo('Winning jackpot WOW') 
            elif value.value in [1, 22, 43]:
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
                _add_balance(user_id, chat_id, user_name, e.get_reward('slots', level, buff))
                logger.log_extrainfo('Three in the row') 
            elif value.value in [6, 11, 16, 17, 27, 32, 33, 38, 48, 49, 59]:
                bot.send_sticker(
                    chat_id, 
                    sticker='CAACAgIAAxkBAAEE6BpimgihzCGdTjyxel5uFJDZfqwI9AACjRMAArwbyUvBk3xJQsTnBSQE',
                    disable_notification=True
                )
                logger.log_extrainfo('Only first two of elements')                       


###################################################################
##                      Reward opportunities                     ##
###################################################################


@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    chat_id, user_id, user_name = _get_chat_user_info(photo)
    if not F.check_type(user_id, 'photo'):
        logger.log_info(f'photo block timeout for {user_name}')
        return None
    state = _random([15,20])
    logger.log_info(f'photo gain state: {state} for {user_name}')
    match state:
        case 1:
            logger.log_extrainfo(f'reply to photo for {user_name} in text mode')
            message = DB.random_text_answer()
            bot.send_message(
                chat_id=chat_id, 
                text=f'{user_name}, {message}',
                disable_notification=True
            )
        case 2:
            logger.log_extrainfo(f'reply to photo for {user_name} in sticker mode')
            sticker = DB.random_sticker_answer()
            bot.send_sticker(
                chat_id=chat_id, 
                sticker=sticker,
                disable_notification=True
            )
        case _:
            pass    
    if state:
        level, _, buff = DB.get_level_buff(user_id)
        _add_balance(user_id, chat_id, user_name, e.get_reward('photo', level, buff))   

@bot.message_handler(content_types=['video'])
def video_message(video):
    chat_id, user_id, user_name = _get_chat_user_info(video)
    if not F.check_type(user_id, 'video'):
        logger.log_info(f'video block timeout for {user_name}')
        return None
    state = _random([40]) 
    logger.log_info(f'video gain state {state} for {user_name}')
    if state:
        sticker = DB.random_sticker_answer()
        bot.send_sticker(
            chat_id=chat_id, 
            sticker=sticker,
            disable_notification=True
        )
        level, _, buff = DB.get_level_buff(user_id)
        _add_balance(user_id, chat_id, user_name, e.get_reward('video', level, buff))   

def send_video_note_voice_reaction(quick_voice_message, duration):
    chat_id, user_id, user_name = _get_chat_user_info(quick_voice_message)
    if duration < 8:
        if not F.check_type(user_id, 'quick_voice'):
            logger.log_info(f'quick_voice_message block timeout for {user_name}')
            return None
    state = _random([40])
    logger.log_info(f'quick_voice_message gain state {state} for {user_name}')
    if state:
        sticker = DB.random_sticker_answer()
        bot.send_sticker(
            chat_id=chat_id, 
            sticker=sticker,
            disable_notification=True
        )
        level, _, buff= DB.get_level_buff(user_id)
        _add_balance(user_id, chat_id, user_name, e.get_reward('voice', level, buff)) 

@bot.message_handler(content_types=['video_note'])
def video_note_answer(quick_voice_message):
    send_video_note_voice_reaction(quick_voice_message, quick_voice_message.video_note.duration)

@bot.message_handler(content_types=['voice'])
def video_note_answer(quick_voice_message):
    send_video_note_voice_reaction(quick_voice_message, quick_voice_message.voice.duration)    

@bot.message_handler(content_types=['sticker'])
def sticker_answer(sticker):
    chat_id, user_id, user_name = _get_chat_user_info(sticker)
    if not F.check_type(user_id, 'sticker'):
        logger.log_info(f'sticker block timeout for {user_name}')
        return None
    state = _random([25])
    logger.log_info(f'sticker gain state {state} for {user_name}')
    if state:
        level, _, buff = DB.get_level_buff(user_id)
        _add_balance(user_id, chat_id, user_name, e.get_reward('sticker', level, buff)) 


###################################################################
##                          Bot start                            ##
###################################################################

logger.log_info(f'bot start\n')

bot.infinity_polling()