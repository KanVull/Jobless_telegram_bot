import telebot
import random
import os
import configparser
import dropbox

bot = telebot.TeleBot(os.environ.get('token'), parse_mode=False)

DROPBOX_ACCESS_TOKEN = os.environ.get('dropbox_key')
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
dropbox_games_file_name = '/games.cfg'
games_filename = './games.cfg'
config = configparser.ConfigParser()

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
    elif (number+10) % 20 == 0:
        with open('stickers.txt', 'r') as file:
            print(f'[*] reply to photo for {user_name} in sticker mode')
            lines = file.readlines()
            bot.send_sticker(photo.chat.id, random.choice(lines))

@bot.message_handler(regexp=r'^([0-9]{1,})')
def echo(message):
    user_name = message.from_user.first_name
    print(f'[*] reply for number for {user_name}')
    bot.send_message(chat_id=message.chat.id, text=f'{user_name}, ладно')

def game_plus1(chat_id):
    with open(games_filename, 'wb') as f:
        _, result = dbx.files_download(path=dropbox_games_file_name)
        f.write(result.content)
    config.read(games_filename)
    score = int(config['GAMES']['plus1']) + 1
    config['GAMES']['plus1'] = str(score)
    with open(games_filename, 'w') as f:
        config.write(f)
    with open(games_filename, 'rb') as f:    
        meta = dbx.files_upload(f.read(), dropbox_games_file_name, mode=dropbox.files.WriteMode("overwrite"))    
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
            mess = 'скоро начнёшь превышать.\nЭто зачту'
            counting[1] += 1
            game_plus1(message.chat.id)
        elif counting[1] == 2:
            mess = 'слушай, я же тебя просил. Засчитываю последний раз.'
            counting[1] += 1
            game_plus1(message.chat.id)
        else:
            mess = 'чел, (T_T) Жди других'
        bot.send_message(chat_id=message.chat.id, text=f'{user_name}, {mess}')
    else:
        counting = [user_id, 1]
        game_plus1(message.chat.id)
        bot.send_message(chat_id=message.chat.id, text=f'{user_name}, засчитано')


bot.infinity_polling()