from Classes.Match3Objects import Bonuses
from Classes.Events import *

class User:
    def __init__(self, id_2, id_1=None):
        if id_1:
            self.user_id = id_1
        else:
            self.user_id = id_2

        self.first_session = True
        self.install_date = None
        self.publisher = None
        self.source = None
        self.entries = []
        self.last_enter = None
        self.country = None

        self.lives = 5
        self.bonuses = Bonuses(0, 0, 0)
        self.premium_coin = 300
        self.game_coin = 400
        self.previous_game_coin = 400

        self.installed_app_version = None
        self.skipped = False



    def is_skipped(self):
        return self.skipped

    def is_new_session(self, previous_event, current_event):
        if isinstance(current_event, CityEventsInitGameState):
            return True

    def user_status_update(self, current_event, previous_event):
        '''
        обновление статуса игрока
        для корректной работы необходимо включить в запрос события, включающие данные о валюте, покупках, жизнях и тд
        '''


        # при старте матч3 вычитаем выбранные и прибавляем купленные бонусы, обновляем жизни
        if current_event.__class__ is Match3StartGame:
            self.bonuses.plus(current_event.buy_bonuses_count)
            self.bonuses.minus(current_event.start_bonuses)
            if current_event.lives:
                self.lives = current_event.lives

        # в конце игры, если цели выполнены (а они должны быть выполнены по идее) вычитаем полученную за игру пыль
        # и прибавляем пыль после magic time
        elif current_event.__class__ is Match3FinishGame:
            self.previous_game_coin = self.game_coin
            if previous_event.__class__ is Match3CompleteTargets:
                self.game_coin -= int(previous_event.game_currency_count)
                self.game_coin += int(current_event.game_currency_count)

        # прибавляем полученную за игру пыль (на случай, когда не дожидаются FinishGame)
        elif current_event.__class__ is Match3CompleteTargets:
            self.previous_game_coin = self.game_coin
            self.game_coin += current_event.game_currency_count

        # обновляем жизни
        elif current_event.__class__ is Match3FailGame:
            if previous_event is not Match3FailGame:
                self.lost_life_datetime = current_event.datetime
            if current_event.lives:
                self.lives = current_event.lives

        # обновляем валюту и бонусы
        elif current_event.__class__ is CityEventsStartGame:
            self.premium_coin = current_event.premium_coin
            self.previous_game_coin = self.game_coin
            self.game_coin = current_event.game_coin
            self.bonuses = current_event.start_bonuses

        # обновляем валюту
        elif current_event.__class__ is CityEventsInitGameState:
            self.premium_coin = current_event.premium_coin
            self.previous_game_coin = self.game_coin
            self.game_coin = current_event.game_coin

        # обновляем жизни и валюту
        elif current_event.__class__ is CityEventsBuyHealth:
            self.lives = 5
            if current_event.premium_coin is not None:
                self.premium_coin = current_event.premium_coin

        elif current_event.__class__ is CityEventsBuyDecoration:
            if current_event.game_coin is not None:
                self.previous_game_coin = self.game_coin
                self.game_coin = current_event.game_coin

        elif current_event.__class__ is CityEventsBuyPremiumCoin:
            if current_event.premium_coin is not None:
                self.premium_coin = current_event.premium_coin

        elif current_event.__class__ is CityEventsBuyDust:
            if current_event.game_coin is not None and current_event.premium_coin is not None:
                self.premium_coin = current_event.premium_coin
                self.previous_game_coin = self.game_coin
                self.game_coin = current_event.game_coin

        elif current_event.__class__ is CityEventsButtonHealth:
            self.lives = current_event.lives

        elif current_event.__class__ is CityEventsButtonDust:
            self.previous_game_coin = self.game_coin
            self.game_coin = current_event.game_coin

        elif current_event.__class__ is CityEventsUpdateBuilding:
            if current_event.game_coin is not None:
                self.game_coin = current_event.game_coin

        elif isinstance(current_event,CityEventsRestore):
            if current_event.game_coin is not None:
                self.game_coin = current_event.game_coin

    def get_status(self):
        return str("Final status: Premium coin: " + str(self.premium_coin) + " Game coin: " + str(self.game_coin) +
                   " Lives: " + str(self.lives) + " Bonuses: " + self.bonuses.to_string())