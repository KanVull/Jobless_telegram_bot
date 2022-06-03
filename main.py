import telebot
import configparser
import random

config_file = configparser.ConfigParser()
config_file.read('config.cfg')
bot = telebot.TeleBot(config_file['BOT_SETTINGS']['Token'], parse_mode=False)
counting = None
print('[*] bot start\n')

@bot.message_handler(content_types=['photo'])
def photo_message(photo):
    number = random.randint(0,101)
    user_name = photo.from_user.first_name
    print(f'[*] photo gain {number} for {user_name}')
    if number % 20 == 0:
        with open('nicelist.txt', 'r') as file:
            print(f'[*] reply to photo for {user_name} in text mode')
            lines = file.readlines()
            bot.send_message(chat_id=photo.chat.id, text=f'{user_name}, {random.choice(lines)}')
    elif number+10 % 20 == 0:
        with open('stickers.txt', 'r') as file:
            print(f'[*] reply to photo for {user_name} in sticker mode')
            lines = file.readlines()
            bot.send_sticker(chat_id=photo.chat.id, file_id=random.choice(lines).replace('\n', ''))    

@bot.message_handler(regexp=r'^([0-9]{1,})')
def echo(message):
    user_name = message.from_user.first_name
    print(f'[*] reply for number for {user_name}')
    bot.send_message(chat_id=message.chat.id, text=f'{user_name}, ладно')

def game_plus1(chat_id):
    score = int(config_file['GAMES']['Counting']) + 1
    config_file['GAMES']['Counting'] = str(int(config_file['GAMES']['Counting']) + 1) 
    with open('config.cfg', 'w') as configfile:
        config_file.write(configfile)
    if score % 1000 == 0:
        print(f'[*] game +1 gain another 1000')
        bot.send_message(chat_id=chat_id, text=f'!!!{score}!!!\nНу и нечем конечно заняться парням') 
    elif score % 50 == 0:
        print(f'[*] game +1 gain another 50')
        bot.send_message(chat_id=chat_id, text=f'Командными усильями этот счётчик теперь {score}')     

@bot.message_handler(regexp=r'^(\+1)$')
def gamePlus1(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    print(f'[*] game +1 making for {user_name}')
    global counting
    if counting is None:
        counting = [user_id, 1]
        game_plus1(message.chat.id)
        bot.send_message(chat_id=message.chat.id, text=f'{user_name}, засчитано')
    elif counting[0] == user_id:
        if counting[1] == 1:
            mess = 'скоро начнёшь превышать, дай другим тоже поиграть.\nладно, это зачту'
            counting[1] += 1
            game_plus1(message.chat.id)
        elif counting[1] == 2:  
            mess = 'слушай, я же тебя просил. Не испытывай терпение. Засчитываю последний раз. Дай другим тоже прибавлять'     
            counting[1] += 1
            game_plus1(message.chat.id)
        else:
            mess = 'чел, ты в муте. Жди других (T_T)'
        bot.send_message(chat_id=message.chat.id, text=f'{user_name}, {mess}')        
    else:
        counting = [user_id, 1]
        game_plus1(message.chat.id)
        bot.send_message(chat_id=message.chat.id, text=f'{user_name}, засчитано')   


bot.infinity_polling()