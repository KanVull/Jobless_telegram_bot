from typing import List, Tuple
import translators as ts
import telebot
import openai
import random
import time
import configparser

import logger
import db_connect
import economy
import filter


###################################################################
##                        Configuration                          ##
###################################################################

def readConfig(config_path='../Jobless_bot_config/config.cfg'):
    '''
    returns config file
    '''
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
    except Exception:
        print(f'Check your {config_path} config file!')
        return None
    else:
        return config    

CONFIG = readConfig()
TELEBOT_ACCESS_TOKEN = CONFIG['BOT']['Token']
DATABASE = {
    'name':     CONFIG['DB']['Name'],
    'password': CONFIG['DB']['Password'],
    'user':     CONFIG['DB']['User'],
    'host':     CONFIG['DB']['Host'],
    'port':     CONFIG['DB']['Port']
}
OPENAI_TOKEN = CONFIG['OPENAI']['Token']

bot = telebot.TeleBot(TELEBOT_ACCESS_TOKEN, parse_mode=False)
openai.api_key = OPENAI_TOKEN
DB = db_connect.DB_work(DATABASE)
e = economy.Economy()
F = filter.Filter()

chat_id = None


###################################################################
##                      Private functions                        ##
###################################################################

def _readable_amount_name(amount):
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
    '''
    returns chat_id, user_id, user_name
    '''
    chat_id = messageObject.chat.id
    user_id = str(messageObject.from_user.id)
    user_name = messageObject.from_user.first_name
    return (chat_id, user_id, user_name)

def _gamePlus1_add(user_id: str, chat_id: str, user_name: str) -> None:
    state = DB.update_gameplus1(user_id)
    messages = {
        1: 'засчитано',
        2: 'скоро начнёшь превышать.\nЭто зачту',
        3: 'слушай, я же тебя просил. Засчитываю последний раз.'
    }
    message = messages.get(state[0], 'чел, (T_T) Жди других')        
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
    r_a = e.readable_amount(amount)
    balance = DB.get_balance(user_id)
    r_balance = e.readable_amount(balance)
    bot.send_message(
        chat_id=chat_id, 
        text=f'{user_name}, +{r_a} {_readable_amount_name(amount)}!\nВ кошельке: {r_balance}',
        disable_notification=True
    )
    logger.log_extrainfo(f"Added {e.readable_amount(r_a)} to balance: {e.readable_amount(balance - amount)} -> {r_balance}")

def _random(percent: List[int]) -> int:
    # Check if the input is valid
    if not all(0 <= p <= 100 for p in percent):
        raise ValueError("Percentages must be between 0 and 100.")

    # Generate a random number between 0 and 100
    ran = random.random() * 100

    # Create a cumulative percentage list
    cumulative_percent = [0]
    for p in percent:
        cumulative_percent.append(cumulative_percent[-1] + p)
    cumulative_percent.pop(0)

    # Find the corresponding index
    for i, cp in enumerate(cumulative_percent):
        if ran < cp:
            return i + 1
    return 0    

def _generate_answer(question: str) -> str:
    model_engine = "text-davinci-003"
    prompt = (f"{question}")
    try:
        completions = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )

        message = completions.choices[0].text
    except Exception:
        message = None    
    return message

def _remove_prefix(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):]
    return text

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
            text=f'{user_name}, Добро пожаловать!\nПриветственный бонус {e.readable_amount(welcome_bonus)} {_readable_amount_name(welcome_bonus)}. \
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
У тебя {e.readable_amount(balance)} {_readable_amount_name(balance)}. Уровень {user_level_buff[0]}.\nТы - {user_level_buff[1]}!\n\
Твой бафф: x{e.readable_amount(user_level_buff[2])}',
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

@bot.message_handler(regexp='^(Baton,|baton,|bot,|Bot,|Батон,|батон,|бот,|Бот,)')
def openChat_answer(message):
    user_name = _get_chat_user_info(message)[2]
    logger.log_info(f'{user_name} asked ChatGPT')

    text = _remove_prefix(message.text, ['Батон,', 'батон,', 'бот,', 'Бот,','Baton,','baton,','bot,','Bot,'])
    text = ts.translate_text(text.strip())
    answer = _generate_answer(text)
    response = answer or f'{user_name}, я сейчас сплю, напиши, когда проснусь\n(-_-)Zzzz'
    bot.reply_to(
        message,
        text=response,
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
def show_balance(message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    amount = DB.get_balance(user_id)
    rAmount = e.readable_amount(amount)
    bot.reply_to(
        message, 
        text=f'{user_name}, у тебя {rAmount} {_readable_amount_name(amount)}!',
        disable_notification=True
    )
    logger.log_info(f"{user_name} get_balance: {rAmount}")

@bot.message_handler(regexp='^(уровень)$')
@bot.message_handler(regexp='^(level)$')
@bot.message_handler(commands=['level'])
def show_level(message):
    _, user_id, user_name = _get_chat_user_info(message)
    user_level__name = DB.get_level_buff(user_id)
    can_you_buy_a_new_level = DB.level_up_check(user_id)
    if not can_you_buy_a_new_level:
        support_message = 'У тебя максимальный уровень на данный момент'
    else:
        level_cost = e.level_cost(user_level__name[0] + 1)
        support_message = f'Следующий уровень стоит {e.readable_amount(level_cost)} {_readable_amount_name(level_cost)}\n\
Чтобы купить, введи "Купить уровень" или /level_buy'    
    bot.reply_to(
        message, 
        text=f'{user_name}, ты - {user_level__name[1]}!\nУ тебя {user_level__name[0]} уровень\n{support_message}',
        disable_notification=True
    )
    logger.log_info(f"{user_name} show the level: {user_level__name[0]} - {user_level__name[1]}")

@bot.message_handler(regexp='^(бафф)$')
@bot.message_handler(commands=['buff'])
def show_available_buff(message):
    _, user_id, user_name = _get_chat_user_info(message)
    buff, next_buff = DB.get_buff_info(user_id)
    mess = f'Твой бафф: x{buff}\nУвеличивает всё, кроме стоимости уровня.\n'
    if next_buff is None:
        mess += 'Ты купил последний на данный момент бафф'
    else:
        mess += f'Следующий бафф даст тебе: x{next_buff[1]}\nСтоит: {e.readable_amount(next_buff[0])}\n\
Чтобы купить введи "Купить бафф" или команду /buff_buy'
    bot.reply_to(
        message, 
        text=mess,
        disable_notification=True
    )    
    logger.log_info(f'{user_name} gets buff info')

@bot.message_handler(regexp='^(преколы)$')
@bot.message_handler(commands=['prekoli'])
def show_prekoli_info(message):
    _, user_id, user_name = _get_chat_user_info(message)
    user_level_buff = DB.get_level_buff(user_id)
    x = user_level_buff[2]
    if x == 1:
        buff_info = f'У тебя сейчас неактивны баффы, купи один.'
    else:
        buff_info = f'Твой бафф: x{e.readable_amount(user_level_buff[2])}.'    
    bot.reply_to(
        message,
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

- Картинка: {e.readable_amount(e.get_reward('photo', user_level_buff[0], x))}
- Видео: {e.readable_amount(e.get_reward('video', user_level_buff[0], x))}
- Голосовое или кружок: {e.readable_amount(e.get_reward('voice', user_level_buff[0], x))}
- Стикер: {e.readable_amount(e.get_reward('sticker', user_level_buff[0], x))}

Дайс стоит: {e.readable_amount(e.get_pay_price('dice', user_level_buff[0], x))}''',\
            
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
{e.readable_amount(level_cost)}\nТебе не хватает {e.readable_amount(level_cost - DB.get_balance(user_id))}", 
                disable_notification=True
            )
            logger.log_info(f'{user_name} doesn\'t have enough balance to level_up')
            return None
        DB.level_up(user_id)
        user_level__name = DB.get_level_buff(user_id)    
        can_you_buy_a_new_level = DB.level_up_check(user_id)
        if can_you_buy_a_new_level:
            level_cost = e.level_cost(user_level__name[0] + 1)
            support_message = f'Следующий уровень будет стоить {e.readable_amount(level_cost)} {_readable_amount_name(level_cost)}'
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
{e.readable_amount(next_buff[0])}\nТебе не хватает {e.readable_amount(next_buff[0] - DB.get_balance(user_id))}", 
                disable_notification=True
            )
            logger.log_info(f'{user_name} doesn\'t have enough balance to buff_buy')
            return None
        
        name_of_buff = DB.buff_buy(user_id)
        buff, next_buff = DB.get_buff_info(user_id)
        if next_buff is not None:
            support_message = f'Следующий бафф будет стоить {e.readable_amount(next_buff[0])}\
 {(next_buff[0])} и добавит тебе x{e.readable_amount(next_buff[1])} к текущему улучшению.'
        else:
            support_message = f'Ты купил максимальный на данный момент бафф'    
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, ты купил бафф:\n{name_of_buff}\nТеперь у тебя бафф: x{e.readable_amount(buff)}\n{support_message}',
            disable_notification=True
        )
        logger.log_info(f"{user_name} buys a buff {name_of_buff}")
        logger.log_extrainfo(f"Now the buff is x{e.readable_amount(buff)}")

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
            text=f'Нет преколов(\nНадо: {e.readable_amount(pay_price)}\nА у тебя: {e.readable_amount(balance)}', 
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


def handle_content_message(content: str, message):
    chat_id, user_id, user_name = _get_chat_user_info(message)
    if not F.check_type(user_id, content):
        logger.log_info(f'{content} block timeout for {user_name}')
        return None
    if content == 'photo':
        state = _random([15, 20])
    elif content in ['video', 'voice', 'video_note']:
        state = _random([40])
    elif content == 'sticker':
        state = _random([25])
    else:
        return None
    logger.log_info(f'{content} gain state {state} for {user_name}')
    if state == 2 and content == 'photo':
        logger.log_extrainfo(f'reply to {content} for {user_name} in text mode')
        message = DB.random_text_answer()
        bot.send_message(
            chat_id=chat_id, 
            text=f'{user_name}, {message}',
            disable_notification=True
        )
    elif state:
        sticker = DB.random_sticker_answer()
        bot.send_sticker(
            chat_id=chat_id, 
            sticker=sticker,
            disable_notification=True
        )
        level, _, buff = DB.get_level_buff(user_id)
        _add_balance(user_id, chat_id, user_name, e.get_reward(content, level, buff))

@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    handle_content_message('photo', photo)

@bot.message_handler(content_types=['video'])
def video_message(video):
    handle_content_message('video', video)

@bot.message_handler(content_types=['voice'])
def voice_message(voice):
    handle_content_message('voice', voice)

@bot.message_handler(content_types=['video_note'])
def video_note_message(video_note):
    handle_content_message('video_note', video_note)

@bot.message_handler(content_types=['sticker'])
def sticker_message(sticker):
    handle_content_message('sticker', sticker)


###################################################################
##                          Bot start                            ##
###################################################################

logger.log_info(f'bot start\n')

bot.infinity_polling()