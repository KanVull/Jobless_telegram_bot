from typing import Any, Optional, Tuple
from urllib.parse import urlparse
import psycopg2

class DB_work():
    def __init__(self, database_url):
        result = urlparse(database_url)
        self._connection = psycopg2.connect(
            database = result.path[1:],
            user     = result.username,
            password = result.password,
            host     = result.hostname,
            port     = result.port
        )
        self._cur = self._connection.cursor()
        
    def random_text_answer(self):
        self._cur.execute('select answer from text_answers order by random() limit 1;')
        return self._cur.fetchone()[0]

    def random_sticker_answer(self):
        self._cur.execute("select id from sticker_answers order by random() limit 1;") 
        return self._cur.fetchone()[0]

    def _get_plusoneData(self):
        self._cur.execute("select * from gameplus1;")
        data_plusone = dict(self._cur.fetchall())
        data_plusone['count'] = int(data_plusone['count'])
        data_plusone['player_inrow'] = int(data_plusone['player_inrow']) if data_plusone['player_inrow'] != '' else 0
        return data_plusone

    def _set_value_plus1(self, newdata):
        self._cur.execute(f"update gameplus1 set val = '{newdata['count']}' where var = 'count';")
        self._cur.execute(f"update gameplus1 set val = '{newdata['player']}' where var = 'player';")
        self._cur.execute(f"update gameplus1 set val = '{newdata['player_inrow']}' where var = 'player_inrow';")
        self._connection.commit()

    def update_gameplus1(self, player: str) -> tuple:
        '''
        returns state of addition at 0 element:
            1 - player plays first time in row
            2 - player plays second time in row 
                -> first warning
            3 - player plays third time in row 
                -> second and last warning
            4 - player plays fourht or more time in row 
                -> not updated counter - restriction
        and 1 element:
            current count        
        '''
        data_plusone = self._get_plusoneData()
        if player == data_plusone['player']:
            if data_plusone['player_inrow'] < 3:
                data_plusone['count'] += 1
                data_plusone['player_inrow'] += 1
                self._set_value_plus1(data_plusone)
            else:
                return 4, data_plusone['count']    
        else:
            data_plusone['count'] += 1
            data_plusone['player'] = player
            data_plusone['player_inrow'] = 1
            self._set_value_plus1(data_plusone)  

        return data_plusone['player_inrow'], data_plusone['count']      

    def add_balance(self, id: str, amount: float) -> None:
        '''
        Call procedure to add amount of balance to id
        or create balance row wiht given id
        '''
        self._cur.execute(f"call add_balance('{id}', {amount});")
        self._connection.commit()   

    def get_balance(self, id: str) -> float:
        '''
        Check for existing id and get balance amount if found
        or create new row with id and 0 val balance
        '''
        self._cur.execute(f"select * from get_balance('{id}');")
        answer = self._cur.fetchone()[0]    
        self._connection.commit() 

        return answer

    def pay_balance(self, id: str, amount: float) -> bool:
        '''
        returns 
        True if payment was success
        False if ...

        Also creates a person_id if is not exist in balance table
        '''
        self._cur.execute(f"select * from pay('{id}', {amount});")
        answer = self._cur.fetchone()[0]   
        self._connection.commit() 

        return answer    

    def get_level_buff(self, id: str) -> Tuple[int, str, float]:
        self._cur.execute(f"select * from get_level('{id}');")
        level_name = self._cur.fetchone()[0]
        self._cur.execute(f"select level from person where id = '{id}';")
        level = self._cur.fetchone()[0]
        self._cur.execute(f"select x from buff where id = '{id}';")
        buff = self._cur.fetchone()[0]
        return (level, level_name, buff)   

    def get_buff_info(self, id: str) -> Any:
        self._cur.execute(f"select x, buff_id from buff where id = '{id}';")
        buff, buff_id = self._cur.fetchone()[0:2]
        self._cur.execute(f"select exists(select id from buff_info where id={buff_id+1})")
        next_buff = self._cur.fetchone()[0]
        if next_buff:
            self._cur.execute(f"select cost, x from buff_info where id = {buff_id+1}")
            next_buff = self._cur.fetchone()[0:2]
        else:
            next_buff = None
        return buff, next_buff        

    def buff_buy(self, id: str) -> str:
        self._cur.execute(f"select * from add_buff('{id}')")
        name_of_buff = self._cur.fetchone()[0]   
        self._connection.commit()
        return name_of_buff

    def level_up_check(self, id: str) -> bool:
        level = self.get_level_buff(id)[0]
        self._cur.execute(f"select exists(select name from levels where level={level+1})")
        return self._cur.fetchone()[0]    
    
    def level_up(self, id: str) -> None:
        level = self.get_level_buff(id)[0]
        self._cur.execute(f"update person set level = {level+1} where id = '{id}'")
        self._connection.commit()

    def add_user(self, user_id: str, user_name: str, hello_bonus=0.0) -> None:
        self._cur.execute(f"call add_user('{user_id}', '{user_name}', {hello_bonus})")
        self._connection.commit()
