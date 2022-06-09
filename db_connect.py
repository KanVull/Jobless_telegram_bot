from urllib.parse import urlparse
import psycopg2

class DB_gameplus1_work():
    def __init__(self, database_url):
        result = urlparse(database_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        self._connection = psycopg2.connect(
            database = database,
            user = username,
            password = password,
            host = hostname,
            port = port
        )
        self._cur = self._connection.cursor()
        self._cur.execute("select * from gameplus1;")
        self._data = dict(self._cur.fetchall())
        self._data['count'] = int(self._data['count'])
        self._data['player_inrow'] = int(self._data['player_inrow']) if self._data['player_inrow'] != '' else 0


    def _set_value_plus1(self):
        self._data['count'] += 1
        self._cur.execute(f"update gameplus1 set val = '{self._data['count']}' where var = 'count';")
        self._cur.execute(f"update gameplus1 set val = '{self._data['player']}' where var = 'player';")
        self._cur.execute(f"update gameplus1 set val = '{self._data['player_inrow']}' where var = 'player_inrow';")
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
        if player == self._data['player']:
            if self._data['player_inrow'] < 3:
                self._data['player_inrow'] += 1
                self._set_value_plus1()
            else:
                return 4, self._data['count']    
        else:
            self._data['player'] = player
            self._data['player_inrow'] = 1
            self._set_value_plus1()  

        return self._data['player_inrow'], self._data['count']     