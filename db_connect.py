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
        self._cur.execute("select answer from sticker_answers order by random() limit 1;") 
        return self._cur.fetchone()[0]

    def _get_plusoneData(self):
        self._cur.execute("select * from gameplus1;")
        self._data_plusone = dict(self._cur.fetchall())
        self._data_plusone['count'] = int(self._data_plusone['count'])
        self._data_plusone['player_inrow'] = int(self._data_plusone['player_inrow']) if self._data_plusone['player_inrow'] != '' else 0

    def _set_value_plus1(self):
        self._data_plusone['count'] += 1
        self._cur.execute(f"update gameplus1 set val = '{self._data_plusone['count']}' where var = 'count';")
        self._cur.execute(f"update gameplus1 set val = '{self._data_plusone['player']}' where var = 'player';")
        self._cur.execute(f"update gameplus1 set val = '{self._data_plusone['player_inrow']}' where var = 'player_inrow';")
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
        if player == self._data_plusone['player']:
            if self._data_plusone['player_inrow'] < 3:
                self._data_plusone['player_inrow'] += 1
                self._set_value_plus1()
            else:
                return 4, self._data_plusone['count']    
        else:
            self._data_plusone['player'] = player
            self._data_plusone['player_inrow'] = 1
            self._set_value_plus1()  

        return self._data_plusone['player_inrow'], self._data_plusone['count']         