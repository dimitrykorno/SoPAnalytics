# import json
try:
    import ujson as json
except ImportError:
    print("No ujson found. Using json.")
    import json

import re
import traceback
from report_api import Report

from Classes.Events import *
from Classes.Match3Objects import *
from Utilities.Colors import *
from Utilities.Super import *
from Utilities.Targets import *
from Utilities.Tutorials import tutorials
from Utilities.Shop import get_price



def parse_event(event_name, event_json, datetime):
    # заменяем двойные двойные кавычки на одинакрные двойные кавычки (да, тупо...)
    event_json = re.sub(r'""', r'"', event_json)

    try:
        parameters = json.loads(event_json)
    except ValueError:
        Report.Report.not_found.add("Json error:" + event_name + " " + event_json)
        return None
    except Exception as er:
        print(er.args)
        print(event_name, event_json)

        return None

    try:

        if event_name == "Match3Events":
            new_event = parse_match3_event(parameters, datetime)
        elif event_name == "CityEvent":
            new_event = parse_city_event(parameters, datetime)
        elif event_name == "TutorialSteps":
            new_event = parse_tutorial_steps(parameters, datetime)
        elif event_name == "Tutorial":
            new_event = parse_tutorial_complete(parameters, datetime)
        else:
            raise ValueError("Event parse: Unknown event name:", event_name, datetime)

    except Exception as er:

        Report.Report.not_found.add(er.args+" Error: " + event_name + " Json: " + event_json)
        Report.Report.not_found.add(traceback.extract_stack())
        # print(error.args)
        return

    return new_event


def parse_match3_event(parameters, datetime):
    level_num = list(parameters)[0]
    level_num_corrected = level_num
    if "X" in level_num:
        level_num_corrected = "9" + level_num[2:]
    event_type = list(parameters[level_num])[0]

    try:
        if event_type == "StartGame":

            # костыль, Lives появились в 5.3
            if "Lives" in list(parameters[level_num][event_type]):
                lives = int(parameters[level_num][event_type]["Lives"])
            else:
                lives = None

            return Match3StartGame(
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                lives=lives,
                buy_bonuses_count=get_bought_bonuses(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                start_bonuses=get_bonuses(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif event_type == "FinishGame":

            return Match3FinishGame(
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                game_currency_count=get_currency_count(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif event_type == "CompleteTargets":
            return Match3CompleteTargets(
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                game_currency_count=get_currency_count(parameters[level_num][event_type]),
                buy_steps_count=int(parameters[level_num][event_type]["BuyStepsCount"]),
                ingame_bonuses=int(parameters[level_num][event_type]["InGameBonuses"]["Hammer"]),
                elements_count=get_elements(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif "FailGame" in event_type:

            # костыль, Lives появились в 5.3
            if "Lives" in list(parameters[level_num][event_type]):
                lives = int(parameters[level_num][event_type]["Lives"])
            else:
                lives = None

            return Match3FailGame(
                fail_count=int(event_type[9:]),
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                buy_steps_count=int(parameters[level_num][event_type]["BuyStepsCount"]),
                lives=lives,
                ingame_bonuses=int(parameters[level_num][event_type]["InGameBonuses"]["Hammer"]),
                elements_count=get_elements(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif event_type == "BuyPremiumCoinM3":

            # костыль
            if "premiumCoin" in list(parameters[level_num][event_type]):
                premium_coin = int(parameters[level_num][event_type]["premiumCoin"])
            else:
                premium_coin = None
            if "AppPurchasePrice" in parameters[level_num][event_type]:
                price = round(float(parameters[level_num][event_type]["AppPurchasePrice"]), 2)
            else:
                price = get_price(parameters[level_num][event_type]["AppPurchaseSKU"],money="dollar")
            return Match3BuyPremiumCoin(
                level_num=level_num_corrected,
                quest=parameters[level_num][event_type]["Quest"],
                app_purchase_sku=parameters[level_num][event_type]["AppPurchaseSKU"],
                price=price,
                status=parameters[level_num][event_type]["Status"],
                premium_coin=premium_coin,
                datetime=datetime
            )

        else:
            raise ValueError("Event parse: Unknown Match 3 event type:", event_type)

    except ValueError as error:
        print(error.args)


def get_targets_list(params):
    first_target = Target(
        params["FirstTarget"]["TargetCount"],
        params["FirstTarget"]["Target"],
        params["FirstTarget"]["OverflowTargetCount"]
    )

    if params["SecondTarget"]:
        second_target = Target(
            params["SecondTarget"]["TargetCount"],
            params["SecondTarget"]["Target"],
            params["SecondTarget"]["OverflowTargetCount"]
        )

        return first_target, second_target
    return first_target, None


def get_elements(params):
    # print(params["ElementsCount"])
    supers = {}
    colors = {}
    targets = {}
    others = {}
    for key, value in params["ElementsCount"].items():
        color = Colors.get_color(key)
        if color:
            colors[color] = value
            continue
        sup = Supers.get_super(key)
        if sup:
            supers[sup] = value
            continue
        target = Targets.get_target(key)
        if target:
            targets[target] = value
            continue

        Report.Report.not_found.add("Elements parse: Unknown object: " + key)
        others[key] = value

    return Elements(super_count=supers, targets_count=targets, colors_count=colors, others_count=others)


def get_bought_bonuses(params):
    bought_bonuses = Bonuses()
    if "FirstIntroductory" in params["BuyBonusesCount"]:
        bought_bonuses.first = params["BuyBonusesCount"]["FirstIntroductory"]

    if "SecondIntroductory" in params["BuyBonusesCount"]:
        bought_bonuses.second = params["BuyBonusesCount"]["SecondIntroductory"]

    if "ThirdIntroductory" in params["BuyBonusesCount"]:
        bought_bonuses.third = params["BuyBonusesCount"]["ThirdIntroductory"]

    return bought_bonuses


def get_bonuses(params):
    return Bonuses(
        int(params["StartBonuses"]["First"]),
        int(params["StartBonuses"]["Second"]),
        int(params["StartBonuses"]["Third"])
    )


def get_currency_count(params):
    if params["GameCurrencyCount"] == "not calculate points":
        return 0
    else:
        return int(params["GameCurrencyCount"])


def parse_city_event(parameters, datetime):
    event_type = list(parameters)[0]

    try:
        if event_type == "StartGame":

            level_num = list(parameters[event_type])[0]
            level_num_corrected = level_num
            if "X" in level_num:
                level_num_corrected = "9" + level_num[2:]

            return CityEventsStartGame(
                level_num=level_num_corrected,
                premium_coin=int(parameters[event_type][level_num]["premiumCoin"]),
                game_coin=int(parameters[event_type][level_num]["gameCoin"]),
                start_bonuses=get_bonuses(parameters[event_type][level_num]),
                ingame_bonuses=int(parameters[event_type][level_num]["InGameBonuses"]["Hammer"]),
                datetime=datetime
            )

        elif event_type == "BuyPremiumCoin":
            # костыль
            if "premiumCoin" in list(parameters[event_type]):
                premium_coin = int(parameters[event_type]["premiumCoin"])
            else:
                premium_coin = None
            price = round(float(parameters[event_type]["AppPurchasePrice"]), 2) if "AppPurchasePrice" in \
                                                                                   parameters[
                                                                                       event_type] else None
            return CityEventsBuyPremiumCoin(
                quest=parameters[event_type]["Quest"],
                app_purchase_sku=parameters[event_type]["AppPurchaseSKU"],
                price=price,
                status=parameters[event_type]["Status"],
                premium_coin=premium_coin,
                datetime=datetime
            )

        elif event_type == "BuyDecoration":
            # костыль
            if "gameCoin" in list(parameters[event_type]):
                game_coin = int(parameters[event_type]["gameCoin"])
                # print("Buy decor dust", game_coin)
            else:
                game_coin = None
            return CityEventsBuyDecoration(
                quest=parameters[event_type]["Quest"],
                purchase=parameters[event_type]["Name"],
                status=parameters[event_type]["Status"],
                game_coin=game_coin,
                datetime=datetime
            )

        elif event_type == "BuyHealth":
            # костыль
            if "premiumCoin" in list(parameters[event_type]):
                premium_coin = int(parameters[event_type]["premiumCoin"])
                # print("BuyHealth premium coin",premium_coin)
            else:
                premium_coin = None

            return CityEventsBuyHealth(
                quest=parameters[event_type]["quest_id"],
                premium_coin=premium_coin,
                datetime=datetime
            )

        elif event_type == "BuyDust":
            return CityEventsBuyDust(
                quest=parameters[event_type]["Quest"],
                purchase=parameters[event_type]["Name"],
                status=parameters[event_type]["Status"],
                premium_coin=parameters[event_type]["premiumCoin"],
                game_coin=parameters[event_type]["gameCoin"],
                datetime=datetime
            )

        elif event_type == "UpdateBuilding":
            building = [x for x in list(parameters[event_type]) if x != "premiumCoin"][0]
            # костыль
            premium_coin = int(parameters[event_type]["premiumCoin"]) if "premiumCoin" in list(
                parameters[event_type]) else None
            quest_id = parameters[event_type]["Quest"] if "Quest" in list(
                parameters[event_type]) else None

            return CityEventsUpdateBuilding(
                building=building,
                level=parameters[event_type][building],
                premium_coin=premium_coin,
                datetime=datetime,
                quest_id=quest_id
            )
        elif event_type == "BuyNoDustWindow":
            return CityEventsBuyNoDustWindow(
                game_coin=parameters[event_type]["gameCoin"],
                premium_coin=parameters[event_type]["premiumCoin"],
                quest_id=parameters[event_type]["Quest"],
                status=parameters[event_type]["Status"],
                datetime=datetime
            )

        elif event_type == "Button":
            button_type = list(parameters[event_type])[0]
            quest_id = list(parameters[event_type][button_type])[0]
            if button_type == "Play":
                # просто игра или начало квеста
                play_type = list(parameters[event_type][button_type][quest_id])[0]
                return CityEventsButtonPlay(
                    button=button_type,
                    quest=quest_id,
                    play_type=play_type,
                    action=parameters[event_type][button_type][quest_id][play_type],
                    datetime=datetime
                )
            elif button_type == "Health":
                # print("Health")
                quest = [x for x in list(parameters[event_type][button_type]) if x != "Lives"][0]
                return CityEventsButtonHealth(
                    button=button_type,
                    quest=quest,
                    action=parameters[event_type][button_type][quest],
                    lives=parameters[event_type][button_type]["Lives"],
                    datetime=datetime

                )
            elif button_type == "Dust":
                # print("Dust")
                quest = [x for x in list(parameters[event_type][button_type]) if x != "gameCoin"][0]
                return CityEventsButtonDust(
                    button=button_type,
                    quest=quest,
                    action=parameters[event_type][button_type][quest],
                    game_coin=parameters[event_type][button_type]["gameCoin"],
                    datetime=datetime

                )
            else:
                return CityEventsButton(
                    button=button_type,
                    quest=quest_id,
                    action=parameters[event_type][button_type][quest_id],
                    datetime=datetime
                )
        elif event_type == "InitGameState":
            return CityEventsInitGameState(
                premium_coin=int(parameters[event_type]["premiumCoin"]),
                game_coin=int(parameters[event_type]["gameCoin"]),
                datetime=datetime
            )
        elif event_type == "Quest":
            quest_id = list(parameters[event_type])[0]
            # косяки
            if quest_id in ("Take", "Сomplete"):
                return
            if parameters[event_type][quest_id] == "Сomplete":
                action = "Complete"
            else:
                action = parameters[event_type][quest_id]
            return CityEventsQuest(
                quest_id=quest_id,
                action=action,
                datetime=datetime
            )
        elif event_type == "Restore":
            if isinstance(parameters[event_type], str):
                return None
            game_coin = int(parameters[event_type]["gameCoin"]) if "gameCoin" in list(
                parameters[event_type]) else None
            quest_id = parameters[event_type]["Quest"] if "Quest" in list(
                parameters[event_type]) else None
            obj = parameters[event_type]["Object"] if "Object" in list(
                parameters[event_type]) else parameters[event_type]
            return CityEventsRestore(
                object_name=obj,
                datetime=datetime,
                game_coin=game_coin,
                quest_id=quest_id
            )
        elif event_type == "Remove":
            # if "premiumCoin" not in parameters[event_type]:
            #    return None
            return CityEventsRemove(
                object_name=parameters[event_type],
                datetime=datetime,
                premium_coin=int(parameters[event_type]["premiumCoin"]),
                quest_id=parameters[event_type]["Quest"]
            )
        elif event_type == "MillDust":
            return CityEventsMillDust(
                garden_id=parameters[event_type]["Garden"],
                datetime=datetime,
                game_coin=int(parameters[event_type]["gameCoin"]),
                quest_id=parameters[event_type]["Quest"]
            )
        else:
            raise ValueError("Event parse: Unknown City event type:", event_type)

    except ValueError as error:
        print(error.args)


def parse_tutorial_steps(parameters, datetime):
    level_num = list(parameters)[0]
    return TutorialSteps(
        level_num=level_num,
        step_number=parameters[level_num],
        datetime=datetime
    )


def parse_tutorial_complete(parameters, datetime):
    tutorial_code = list(parameters)[0]
    if tutorial_code not in tutorials:
        print("Event parse: Unknown tutorial:", tutorial_code)
    return Tutorial(
        tutorial_code=tutorial_code,
        status=parameters[tutorial_code],
        datetime=datetime
    )
