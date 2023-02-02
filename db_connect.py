from typing import Any, Optional, Tuple
from mysql import connector

class DB_work():
    def __init__(self, database):
        self.db_info = database
        self.cnx = connector.connect(
            database=database['name'],
            user    =database['user'],
            password=database['password'],
            host    =database['host'],
        )
        
    def get_answer(self, function_name):
        with self.cnx.cursor() as cur:
            cur.execute(f'select `{self.db_info["name"]}`.`{function_name}`() as answer;')
            answer = cur.fetchone()[0]
        return answer

    def random_text_answer(self):
        return self.get_answer("random_text_answer")

    def random_sticker_answer(self):
        return self.get_answer("random_sticker_answer")

    def random_fart(self):
        with self.cnx.cursor() as cur:
            cur.execute("select data from sound where type = 'fart' order by rand() limit 1;") 
            fart = cur.fetchone()[0]  
        return fart  

    def _get_plusoneData(self):
        keys = ['player', 'count', 'player_inrow']

        with self.cnx.cursor() as cur:
            cur.execute(f"select {', '.join(keys)} from gameplus1;")
            rows = cur.fetchall()

        if not rows:
            return {}

        data_plusone = dict(zip(keys, rows[0]))
        data_plusone['count'] = int(data_plusone['count'])
        data_plusone['player_inrow'] = int(data_plusone['player_inrow']) if data_plusone['player_inrow'] != '' else 0
        return data_plusone

    def _set_value_plus1(self, newdata):
        player = newdata['player']
        count = newdata['count']
        inrow = newdata['player_inrow']
        with self.cnx.cursor() as cur:
            cur.execute(f"call `update_gameplus`('{player}', {count}, {inrow});")
            self.cnx.commit()

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
        with self.cnx.cursor() as cur:
            cur.execute(f"call `{self.db_info['name']}`.`add_balance`('{id}', {amount});")
            self.cnx.commit()   

    def get_balance(self, id: str) -> float:
        with self.cnx.cursor() as cur:
            cur.execute(f"select `{self.db_info['name']}`.`get_balance`('{id}');")
            answer = cur.fetchone()[0]    
            self.cnx.commit() 

        return float(answer)

    def pay_balance(self, id: str, amount: float) -> bool:
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT `{self.db_info['name']}`.`pay`('{id}', {amount});")
            answer = cur.fetchone()[0]   
            if answer:
                self.cnx.commit() 

        return answer    

    def get_level_buff(self, id: str) -> Tuple[int, str, float]:
        with self.cnx.cursor() as cur:
            cur.execute(f"call `{self.db_info['name']}`.`get_user_info`('{id}', @level, @level_name, @x);")
            cur.execute(f"SELECT @level, @level_name, @x;")
            level, level_name, buff = cur.fetchone()[0:3]   

        return (level, level_name, buff)   

    def get_buff_info(self, id: str) -> Any:
        with self.cnx.cursor() as cur:
            cur.execute(f"select x, buff_id from `buff` where id = '{id}';")
            buff, buff_id = cur.fetchone()[0:2]
            buff = float(buff)
            
            query = f"select cost, x from buff_info where id = {buff_id + 1}"
            cur.execute(f"select exists({query})")
            next_buff_exists = cur.fetchone()[0]

            if next_buff_exists:
                cur.execute(query)
                next_cost, next_buff = map(float, cur.fetchone()[0:2])
            else:
                next_cost, next_buff = None, None
            
        return buff, [next_cost, next_buff] if next_cost else None      

    def buff_buy(self, id: str) -> str:
        with self.cnx.cursor() as cur:
            cur.execute(f"select * from add_buff('{id}')")
            name_of_buff = cur.fetchone()[0]   
            self.cnx.commit()
        return name_of_buff

    def level_up_check(self, id: str) -> bool:
        level = self.get_level_buff(id)[0]
        with self.cnx.cursor() as cur:
            cur.execute(f"select exists(select name from levels where level={level+1})")
            next_level_check = cur.fetchone()[0] 
        return  next_level_check  
    
    def level_up(self, id: str) -> None:
        level = self.get_level_buff(id)[0]
        with self.cnx.cursor() as cur:
            cur.execute(f"update person set level = {level+1} where id = '{id}'")
        self.cnx.commit()

    def add_user(self, user_id: str, user_name: str, bonus=0.0) -> None:
        with self.cnx.cursor() as cur:
            cur.execute(f"select `{self.db_info['name']}`.`new_person`('{user_id}', '{user_name}', {bonus});")
            answer = cur.fetchone()[0]    
            if answer: 
                self.cnx.commit() 

        return answer
