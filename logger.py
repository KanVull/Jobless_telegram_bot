import datetime


def current_data():
    now = datetime.datetime.now()
    time_change = datetime.timedelta(hours=3)
    new_time = now + time_change
    return new_time.strftime('%d.%m.%y %H:%M:%S')

def log_info(message: str) -> None:
    print(f'[*] {current_data()} | {message}')
    
def log_extrainfo(message: str) -> None:
    print(f'[.] {current_data()} | \t{message}')    

def empty_log() -> None:
    print()     