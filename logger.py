import datetime
def current_data():
    now = datetime.datetime.now()
    return now.strftime('%y:%m:%d %H:%M:%S')

def log_info(message: str) -> None:
    print(f'[*] {current_data()} | {message}')