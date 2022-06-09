import configparser
import os

files = {
    'config': './config.ini',
    'games': './games.ini',
}

def save_config(config, name):
    with open(files[name], 'w') as config_file:
        config.write(config_file)   
         
def create_config(config):
    save_config(config, 'config')
    return config

def check_config(config):
    
    return config

def create_games(games):
    games['GAMES'] = {
        'plus1': '0'
    }
    save_config(games, 'games')
    return games

def check_games(games):
    if 'GAMES' in games:
        if not 'plus1' in games['GAMES']:
            games['GAMES']['plus1'] = '0'
    else:
        games['GAMES'] = {
            'plus1': '0'
        }


    return games

def check_enviroment() -> dict:
    config = configparser.ConfigParser()
    games = configparser.ConfigParser()

    if not os.path.exists(files['config']):
        config = create_config(config)    
    else:
        config.read(files['config'])
        config = check_config(config)

    if not os.path.exists(files['games']):
        games = create_games(games)
    else:
        games.read(files['games'])
        games = check_games(games)

    return {
        'config': config,
        'games': games
    }