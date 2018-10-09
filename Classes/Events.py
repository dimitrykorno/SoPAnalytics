from Utilities.Tutorials import get_tutorial_name

indent = 20


class Event:
    medium_time = []

    def __init__(self, datetime):
        self.datetime = datetime
        pass

    def print(self):
        print(self.__dict__)

    def to_string(self):
        return str(self.__class__.__name__) + ": "

    def to_short_string(self):
        return self.to_string()


class Match3Event(Event):
    def __init__(self, level_num, session_id, datetime):
        super().__init__(datetime)
        self.level_num = level_num
        self.session_id = session_id

    def to_string(self):
        info = super().to_string()
        info += str(self.level_num) + ": \n" + " " * indent
        return info

    def to_short_string(self):
        info = super().to_string()
        info += "Level: " + str(self.level_num)
        return info


class Match3StartGame(Match3Event):
    def __init__(self, level_num, session_id, turn_count, lives, buy_bonuses_count, targets_list, start_bonuses,
                 datetime):
        super().__init__(level_num, session_id, datetime)
        self.turn_count = turn_count
        self.lives = lives
        self.buy_bonuses_count = buy_bonuses_count
        self.targets_list = targets_list
        self.start_bonuses = start_bonuses

    def to_string(self):
        info = super().to_string()
        info += "Turns: " + str(
            self.turn_count) + ", Lives: " + str(
            self.lives) + ", Bonuses: " + self.start_bonuses.to_string() + "\n" + " " * indent
        info += "Targets: \n" + " " * indent
        for target in self.targets_list:
            if target:
                info += target.to_string() + "\n" + " " * indent

        info += "Bought bonuses: " + self.buy_bonuses_count.to_string()
        return info


class Match3FinishGame(Match3Event):
    def __init__(self, level_num, session_id, turn_count, game_currency_count, targets_list, datetime):
        super().__init__(level_num, session_id, datetime)
        self.turn_count = turn_count
        self.game_currency_count = game_currency_count
        self.targets_list = targets_list

    def to_string(self):
        info = super().to_string()
        info += "Turns: " + str(self.turn_count) + ", Game currency: " + str(self.game_currency_count) + \
                "\n" + " " * indent
        info += "Targets: "
        for target in self.targets_list:
            if target:
                info += "\n" + " " * indent + target.to_string()

        return info


class Match3CompleteTargets(Match3Event):
    def __init__(self, level_num, session_id, turn_count, game_currency_count, buy_steps_count, ingame_bonuses,
                 elements_count, targets_list, datetime):
        super().__init__(level_num, session_id, datetime)
        self.turn_count = turn_count
        self.game_currency_count = game_currency_count
        self.buy_steps_count = buy_steps_count
        self.targets_list = targets_list
        self.ingame_bonuses = ingame_bonuses
        self.elements_count = elements_count

    def to_string(self):
        info = super().to_string()
        info += "Turns: " + str(self.turn_count) + ", Game currency: " + str(self.game_currency_count) + \
                "\n" + " " * indent
        info += "Targets: \n" + " " * indent
        for target in self.targets_list:
            if target:
                info += target.to_string() + "\n" + " " * indent

        info += "Bought steps: " + str(self.buy_steps_count) + ", Ingame bonuses: " + str(
            self.ingame_bonuses) + \
                "\n" + " " * indent + "Elements: " + self.elements_count.to_string()
        return info


class Match3FailGame(Match3Event):
    def __init__(self, fail_count, level_num, session_id, turn_count, buy_steps_count, lives, ingame_bonuses,
                 elements_count, targets_list, datetime):
        super().__init__(level_num, session_id, datetime)
        self.fail_count = fail_count
        self.turn_count = turn_count
        self.buy_steps_count = buy_steps_count
        self.lives = lives
        self.targets_list = targets_list
        self.ingame_bonuses = ingame_bonuses
        self.elements_count = elements_count

    def to_string(self):
        info = super().to_string()
        info += "Fail count: " + str(self.fail_count) + ", Turns: " + str(self.turn_count) + \
                "\n" + " " * indent + "Lives: " + str(self.lives) + ", Targets: \n" + " " * indent
        for target in self.targets_list:
            if target:
                info += target.to_string() + "\n" + " " * indent
        info += "Bought steps: " + str(self.buy_steps_count) + ", Ingame bonuses: " + str(self.ingame_bonuses) + \
                "\n" + " " * indent + "Elements: " + self.elements_count.to_string()
        return info

    def to_short_string(self):
        info = super().to_short_string()
        info += ", Lives: " + str(self.lives)
        return info


class PurchaseEvent(Event):
    def __init__(self, quest, purchase, status, price, datetime):
        super().__init__(datetime)
        self.quest = quest
        self.purchase = purchase
        self.status = status
        self.price = price

    def to_string(self):
        info = super().to_string()
        info += "Quest: " + str(self.quest) + ", Purchase: " + str(self.purchase) + ", Status: " + str(self.status)
        return info


class Match3BuyPremiumCoin(PurchaseEvent):
    def __init__(self, level_num, quest, app_purchase_sku, price, status, premium_coin, datetime):
        super().__init__(quest, app_purchase_sku, status, price, datetime)
        self.level_num = level_num
        self.premium_coin = premium_coin

    def to_string(self):
        info = super().to_string()
        info += ", Level: " + str(self.level_num) + ", PremiumCoin: " + str(self.premium_coin)
        return info


class CityEventsBuyPremiumCoin(PurchaseEvent):
    def __init__(self, quest, app_purchase_sku, price, status, premium_coin, datetime):
        super().__init__(quest, app_purchase_sku, status, price, datetime)
        self.premium_coin = premium_coin

    def to_string(self):
        info = super().to_string() + ", PremiumCoin: " + str(self.premium_coin)
        return info


class CityEventsBuyDecoration(PurchaseEvent):
    def __init__(self, quest, purchase, status, game_coin, datetime):
        super().__init__(quest, purchase, status, None, datetime)
        self.game_coin = game_coin

    def to_string(self):
        info = super().to_string() + ", GameCoin: " + str(self.game_coin)
        return info


class CityEventsStartGame(Event):
    def __init__(self, level_num, premium_coin, game_coin, start_bonuses, ingame_bonuses, datetime):
        super().__init__(datetime)
        self.level_num = level_num
        self.premium_coin = premium_coin
        self.game_coin = game_coin
        self.start_bonuses = start_bonuses
        self.ingame_bonuses = ingame_bonuses

    def to_string(self):
        info = super().to_string()
        info += "Level: " + str(
            self.level_num) + "\n" + " " * indent + "Bonuses: " + self.start_bonuses.to_string() + ", Ingame Bonuses: " + str(
            self.ingame_bonuses) + "\n" + " " * indent + "Premium coin: " + str(
            self.premium_coin) + ", Game coin: " + str(self.game_coin)
        return info

    def to_short_string(self):
        info = super().to_string()
        info += "Level: " + str(self.level_num)
        return info


class CityEventsBuyHealth(Event):
    def __init__(self, quest, premium_coin, datetime):
        super().__init__(datetime)
        self.quest = quest
        self.premium_coin = premium_coin

    def to_string(self):
        info = super().to_string()
        info += "Quest: " + str(self.quest) + ", PremiumCoin: " + str(self.premium_coin)
        return info


class CityEventsBuyDust(PurchaseEvent):
    def __init__(self, quest, purchase, status, premium_coin, game_coin, datetime):
        super().__init__(quest, purchase, status, None, datetime)
        self.premium_coin = premium_coin
        self.game_coin = game_coin

    def to_string(self):
        info = super().to_string()
        info += ", PremiumCoin: " + str(self.premium_coin) + ", GameCoin: " + str(self.game_coin)
        return info


class CityEventsUpdateBuilding(Event):
    def __init__(self, building, level, game_coin, datetime, quest_id=""):
        super().__init__(datetime)
        self.quest = quest_id
        self.building = building
        self.level = level
        self.game_coin = game_coin

    def to_string(self):
        info = super().to_string()
        info += "Building: " + str(self.building) + ", Level: " + str(self.level)
        return info


class CityEventsInitGameState(Event):
    def __init__(self, premium_coin, game_coin, datetime):
        super().__init__(datetime)
        self.premium_coin = premium_coin
        self.game_coin = game_coin

    def to_string(self):
        info = super().to_string()
        info += "Premium coin: " + str(self.premium_coin) + ", Game coin: " + str(self.game_coin)
        return info


class CityEventsQuest(Event):
    def __init__(self, action, quest_id, datetime):
        super().__init__(datetime)
        self.action = action
        self.quest = quest_id

    def to_string(self):
        info = super().to_string()
        info += "Quest: " + str(self.action) + " " + str(self.quest)
        return info

    def to_short_string(self):
        return self.to_string()

    @staticmethod
    def compare_quests(q1, q2):
        if not isinstance(q1, CityEventsQuest) or not isinstance(q2, CityEventsQuest):
            print("Quest Comparision Error: q1 or q2 is not a quest")
        if "fin" in q1:
            if "fin" not in q2:
                return 1
        elif "fin" in q2:
            if "fin" not in q1:
                return -1
        q1_loc = q1[3:4]
        q2_loc = q2[3:4]
        print(q1_loc)
        if q1_loc > q2_loc:
            return 1
        elif q2_loc > q1_loc:
            return -1
        else:
            q1_q = q1[6:7]
            q2_q = q2[6:7]
            print(q1_q)
            if q1_q > q2_q:
                return 1
            elif q2_q > q1_q:
                return -1
            else:
                if q1.action == "Take" and q2.action == "Complete":
                    return 1
                elif q1.action == "Complete" and q2.action == "Take":
                    return -1
                else:
                    return 0


class CityEventsButton(Event):
    '''
    Общий класс для однотипных кнопок: Store, Decoration, Leaderboard, Puzzle
    '''

    def __init__(self, button, quest, action, datetime):
        super().__init__(datetime)
        self.button = button
        self.quest = quest
        self.action = action

    def to_string(self):
        info = super().to_string()
        info += "Button: " + str(self.button) + ", Quest: " + str(self.quest) + ", Action: " + str(self.action)
        return info


class CityEventsButtonPlay(CityEventsButton):
    def __init__(self, button, quest, play_type, action, datetime):
        super().__init__(button, quest, action, datetime)
        self.play_type = play_type

    def to_string(self):
        info = str(self.__class__.__name__) + ": Button: " + str(self.button) + ", Quest: " + str(
            self.quest) + ", Play type: " + str(
            self.play_type) + ", Action: " + str(self.action)
        return info


class CityEventsButtonHealth(CityEventsButton):
    def __init__(self, button, quest, action, lives, datetime):
        super().__init__(button, quest, action, datetime)
        self.lives = lives

    def to_string(self):
        info = str(self.__class__.__name__) + ": Button: " + str(self.button) + ", Quest: " + str(
            self.quest) + ", Lives: " + str(self.lives)
        return info


class CityEventsButtonDust(CityEventsButton):
    def __init__(self, button, quest, action, game_coin, datetime):
        super().__init__(button, quest, action, datetime)
        self.game_coin = game_coin

    def to_string(self):
        info = str(self.__class__.__name__) + ": Button: " + str(self.button) + ", Quest: " + str(
            self.quest) + ", GameCoin: " + str(self.game_coin)
        return info


class CityEventsRestore(Event):
    def __init__(self, object_name, datetime, quest_id="", game_coin=""):
        super().__init__(datetime)
        self.quest = quest_id
        self.object_name = object_name
        self.game_coin = game_coin

    def to_string(self):
        info = super().to_string()
        info += "Restore: Quest: " + str(self.quest) + ", Object: " + str(self.object_name)
        return info


class CityEventsRemove(Event):
    def __init__(self, object_name, datetime, quest_id, premium_coin):
        super().__init__(datetime)
        self.quest = quest_id
        self.object_name = object_name
        self.premium_coin = premium_coin

    def to_string(self):
        info = super().to_string()
        info += "Remove: Quest: " + str(self.quest) + ", Object: " + str(self.object_name)
        return info


class CityEventsMillDust(Event):
    def __init__(self, garden_id, datetime, quest_id, game_coin):
        super().__init__(datetime)
        self.quest = quest_id
        self.garden = garden_id
        self.game_coin = game_coin

    def to_string(self):
        info = super().to_string()
        info += "Get dust: Quest: " + str(self.quest) + ", From: " + str(self.garden) + ", Coins: " + str(
            self.game_coin)
        return info


class TutorialSteps(Event):
    def __init__(self, level_num, step_number, datetime):
        super().__init__(datetime)
        self.level_num = level_num
        self.step_number = step_number

    def to_string(self):
        info = super().to_string()
        info += "TutorialSteps: Level: " + str(self.level_num) + ", Step: " + str(self.step_number)
        return info


class Tutorial(Event):
    def __init__(self, tutorial_code, status, datetime):
        super().__init__(datetime)
        self.tutorial_code = tutorial_code
        if status == "00":
            self.status = "Start"
        elif status == "01":
            self.status = "Finish"
        else:
            self.status = "In progress " + status

    def to_string(self):
        info = super().to_string()
        info += "Tutor name: " + get_tutorial_name(self.tutorial_code) + ", Status: " + self.status
        return info
