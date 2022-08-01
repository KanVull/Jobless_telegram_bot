import math

class Economy:
    def __init__(self):
        self._base_level_cost = 100
        self._level_percent = 1.3
        self._reward_percent = 1.25
        self._balance_rules = {
            'pay': {
                'dice': 3,
            },
            'add': {
                'darts': 9,
                'dice5': 5,
                'dice6': 10,
                'basketball': 5,
                'soccer': 5,
                'bowl': 9,
                'slots': 90,
                'slots777': 600,
                'photo': 3,
                'video': 5,
                'voice': 2,
                'sticker': 1,
            }
        }

    def level_cost(self, level: int) -> int:
        raw_cost = self._base_level_cost * math.pow(self._level_percent, level - 1)
        return math.ceil(raw_cost / 10) * 10

    def get_pay_price(self, type: str, player_level: int) -> int:
        raw_cost = self._balance_rules['pay'][type]
        raw_cost *= math.pow(self._reward_percent, player_level)
        return math.ceil(raw_cost)

    def get_reward(self, type: str, player_level: int) -> int:
        raw_cost = self._balance_rules['add'][type]
        raw_cost *= math.pow(self._reward_percent, player_level)
        return math.ceil(raw_cost)

    def readble_amount(self, amount: int) -> str:
        definition = [
            'k', 'M', 'B', 'T', 'q', 'Q', 's', 'S', 'O', 'N', 
            'D', 'UD', 'DD', 'TD', 'qD', 'QD', 'sD', 'SD', 'OD', 'ND', 
            'V', 'UV', 'DV', 'TV', 'qV', 'QV', 'sV', 'SV', 'OV', 'NV',
            'Tr', 'UTr', 'DTr', 'TTr', 'qTr', 'QTr', 'sTr', 'STr', 'OTr', 'NTr',
            'qg', 'Uqg', 'Dqg', 'Tqg', 'qqg', 'Qqg', 'sqg', 'Sqg', 'Oqg', 'Nqg',
            'Qg', 'UQg', 'DQg', 'TQg', 'qQg', 'QQg', 'sQg', 'SQg', 'OQg', 'NQg',
            'sg', 'Usg', 'Dsg', 'Tsg', 'qsg', 'Qsg', 'ssg', 'Ssg', 'Osg', 'Nsg',
            'Sg', 'USp', 'DSp', 'TSp', 'qSp', 'QSg', 'sSg', 'SSg', 'OSg', 'NSg',
            'Og', 'UOg', 'DOg', 'TOg', 'qOg', 'QOg', 'sOg', 'SOg', 'OOg', 'NOg',
            'Ng', 'UNg', 'DNg', 'TNg', 'qNg', 'QNg', 'sNg', 'SNg', 'ONg', 'NNg',
            'C', 'UC', 'DC', 'TC', 'qC', 'QC', 'sC', 'SC', 'OC', 'NC', 
        ]    
        sAmount = str(amount)
        l = len(sAmount)
        if l <= 3:
            return sAmount
        pw = list(divmod(l, 3))
        if pw[1] == 0:
            pw[1] = 3
            pw[0] -= 1
        sAmount = sAmount[:pw[1] + 3]
        dotPart = sAmount[pw[1]:]
        while dotPart.endswith('0'):
            dotPart = dotPart[:len(dotPart) - 1]
        sAmount = sAmount[:pw[1]]    
        if dotPart != '':
            sAmount = sAmount[:pw[1]] + ',' + dotPart
        return sAmount + definition[pw[0]-1]      




if __name__ == '__main__':
    e = Economy()
    # for i in range(0,100,10): 
        # print(e.readble_amount(e.get_reward('slots', i))) 
    print(e.readble_amount(4100000582734590278345092384752309458852730945873409587230698570697536908746907430968740956734056874906874096874590687458906874089674390674906743906749068479687456907460897469047690872340598237450923847502398457230945872304958723406987234664967439086724689723049687234058927345900))    

