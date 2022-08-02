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
                'darts': 14,
                'dice5': 5,
                'dice6': 10,
                'basketball': 9,
                'soccer': 5,
                'bowl': 14,
                'slots': 60,
                'slots777': 300,
                'photo': 3,
                'video': 5,
                'voice': 2,
                'sticker': 1,
            }
        }

    def _get_cost(self, raw_cost, player_level, buff):
        raw_cost *= math.ceil(math.pow(self._reward_percent, player_level))
        raw_cost *= buff
        return math.ceil(raw_cost)

    def level_cost(self, level: int) -> int:
        raw_cost = self._base_level_cost * math.pow(self._level_percent, level - 1)
        return math.ceil(raw_cost / 10) * 10

    def get_pay_price(self, type: str, player_level: int, buff: float) -> int:
        raw_cost = self._balance_rules['pay'][type]
        return self._get_cost(raw_cost, player_level, buff)

    def get_reward(self, type: str, player_level: int, buff: float) -> int:
        raw_cost = self._balance_rules['add'][type]
        return self._get_cost(raw_cost, player_level, buff)

    def readble_amount(self, amount: float) -> str:
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
        if '.' in sAmount:
            afterdot = sAmount.split('.')[-1]
            if len(afterdot) >= 2:
                sAmount = sAmount[:sAmount.index('.') + 3]
            else:    
                while len(afterdot) < 2:
                    afterdot += '0'
                    sAmount += '0'    
        else:
            sAmount += '.00'

        l = len(sAmount)
        if l <= 6:
            if '.' in sAmount:
                while sAmount.endswith('0'):
                    sAmount = sAmount[:-1]
            if sAmount.endswith('.'):
                sAmount = sAmount[:-1]        
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
        if sAmount.endswith('.'):
            sAmount = sAmount[:-1]    
        return sAmount + definition[pw[0]-2]      


if __name__ == '__main__':
    e = Economy()
    # for i in range(0,100,10): 
        # print(e.readble_amount(e.get_reward('slots', i))) 
    # print(e.readble_amount(e.get_reward('video', 6, 10))) 
    # for i in range(1,70):
    #     level_cost = e.level_cost(i)
    #     level_cost_diff = math.pow(e._level_percent, i - 1)
    #     reward_cost_diff = math.pow(e._reward_percent, i - 1)
    #     if i >= 3:
    #         reward_cost_diff *= 1.1
    #     if i >= 13:
    #         reward_cost_diff *= 1.6
    #     if i >= 28:
    #         reward_cost_diff *= 1.7 
    #     if i >= 43:
    #         reward_cost_diff *= 1.8  
    #     if i >= 59:
    #         reward_cost_diff *= 2

    #     print(f"{i} -> {level_cost} : {level_cost_diff:.02f}\t|\t{reward_cost_diff:.02f}\t|\t{1.0*level_cost_diff/reward_cost_diff:.02f}")  
    print(e.readble_amount(1.43453453))
