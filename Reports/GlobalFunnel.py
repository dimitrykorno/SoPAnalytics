import pandas as pd
from Utilities.Quests import *

from Classes.Events import *
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime
from report_api.Utilities.Utils import time_count, sigma, get_timediff

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[],
               days_left=7):
    """
    Глобальные конверсии по квестам и уровням в них и отвалы с монетами на момент отвала

    !!!ВАЖНО!!! Порядок и положение туториалов меняется в зависимости от версии игры

    :param os_list:
    :param period_start:
    :param period_end:
    :param min_version:
    :param max_version:
    :param countries_list:
    :param days_left: кол-во дней, после которого человек отвалился
    :return:
    """

    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User, event_class=Event,
                            os=os_str, app=app, user_status_check=False)

        Report.set_installs_data(additional_parameters=[],
                                 period_start=period_start,
                                 period_end=period_end,
                                 min_version=min_version,
                                 max_version=max_version,
                                 countries_list=countries_list)
        Report.set_events_data(additional_parameters=[],
                               period_start=period_start,
                               period_end=None,
                               min_version=None,
                               max_version=None,
                               events_list=[("CityEvent", ["%StartGame%", '{"Quest%',
                                                           "%InitGameState%", "%BuyPremiumCoin%Success%"]),
                                            ("Tutorial",)])

        parameters = ["Retention", "Retention %", "Quest loss", "Level loss",  # "Loss",
                      "Last event loss", "loss %", "FinishGame", "Coins"]
        levels_list = get_levels_list(fail=True)

        opened_game = 1
        started_levels = set()
        completed_levels = set()
        finished_levels = set()
        started_quests = set()
        finished_quests = set()
        started_tutorials = set()
        finished_tutorials = set()
        last_game_event = None
        loss_premium_coins = {}
        # в зависимости от версии порядок туториалов меняется
        real_tutorial_order = []
        funnel_data = {}
        for l in levels_list:
            funnel_data[l] = dict.fromkeys(parameters, 0)

        def flush_user_info():
            for lvl1 in started_levels:
                funnel_data["Start  " + lvl1]["Retention"] += 1
            for lvl2 in completed_levels:
                funnel_data["Finish " + lvl2]["Retention"] += 1
            for lvl3 in finished_levels:
                funnel_data["Finish " + lvl3]["FinishGame"] += 1

            for quest in started_quests:
                funnel_data["Start  " + quest]["Retention"] += 1
            for quest in finished_quests:
                funnel_data["Finish " + quest]["Retention"] += 1

            for tutor in started_tutorials:
                funnel_data["Start  " + tutor]["Retention"] += 1
            for tutor in finished_tutorials:
                funnel_data["Finish " + tutor]["Retention"] += 1

            # Отвалы
            if get_timediff(Report.previous_user.last_enter.date(), datetime.now().date(),
                            measure="day") >= days_left:

                last_game_point = None
                # Отвал по последнему событию
                if last_game_event.__class__ is Match3StartGame:
                    last_game_point = "Start  " + last_game_event.level_num
                elif last_game_event.__class__ is Match3FailGame:
                    last_game_point = "Fail   " + last_game_event.level_num
                elif last_game_event.__class__ in (Match3CompleteTargets, Match3FinishGame):
                    last_game_point = "Finish " + last_game_event.level_num
                elif last_game_event.__class__ is CityEventsQuest:
                    if last_game_event.action == "Take":
                        last_game_point = "Start  " + last_game_event.quest
                    elif last_game_event.action in ("Сomplete", "Complete"):
                        last_game_point = "Finish " + last_game_event.quest
                elif last_game_event.__class__ is Tutorial:
                    if last_game_event.status == "Start":
                        last_game_point = "Start  " + last_game_event.tutorial_code
                    elif last_game_event.status == "Finish":
                        last_game_point = "Finish " + last_game_event.tutorial_code

                funnel_data[last_game_point]["Last event loss"] += 1

                # РАСПРЕДЕЛЕНИЕ МОНЕТ УШЕДШИХ
                if last_game_point not in loss_premium_coins.keys():
                    loss_premium_coins[last_game_point] = []
                loss_premium_coins[last_game_point].append(Report.previous_user.premium_coin)
                # ОСТАЛОСЬ: ПОСЧИТАТЬ СРЕДНЕЕ И +- СИГМЫ

        while Report.get_next_event():

            # следующий игрок, обновление данных таблицы, сброс персональных данных
            if Report.is_new_user():
                flush_user_info()
                opened_game += 1
                started_levels = set()
                completed_levels = set()
                finished_levels = set()
                started_quests = set()
                finished_quests = set()
                started_tutorials = set()
                finished_tutorials = set()

            if Report.current_event.__class__ is Match3StartGame:
                started_levels.add(Report.current_event.level_num)
                last_game_event = Report.current_event

            elif Report.current_event.__class__ is Match3FailGame:
                last_game_event = Report.current_event

            elif Report.current_event.__class__ is Match3CompleteTargets:
                completed_levels.add(Report.current_event.level_num)
                last_game_event = Report.current_event
            elif Report.current_event.__class__ is Match3FinishGame:
                finished_levels.add(Report.current_event.level_num)
                last_game_event = Report.current_event

            elif Report.current_event.__class__ is CityEventsQuest:
                if Report.current_event.action == "Take":
                    started_quests.add(Report.current_event.quest)
                elif Report.current_event.action in ("Сomplete", "Complete"):
                    finished_quests.add(Report.current_event.quest)
                last_game_event = Report.current_event
                quest_string = Report.current_event.action + " " + Report.current_event.quest
                if quest_string not in real_tutorial_order:
                    real_tutorial_order.append(quest_string)

            elif Report.current_event.__class__ is Tutorial:
                if Report.current_event.status == "Start":
                    started_tutorials.add(Report.current_event.tutorial_code)
                elif Report.current_event.status == "Finish":
                    finished_tutorials.add(Report.current_event.tutorial_code)
                last_game_event = Report.current_event
                '''
                if Report.current_event.status == "Start" and Report.current_user.installed_app_version==app_version:
                    if "Start  "+Report.current_event.tutorial_code not in real_tutorial_order:
                        real_tutorial_order.append("Start  "+Report.current_event.tutorial_code)
                        real_tutorial_order.append("Finish "+Report.current_event.tutorial_code)
                '''
                ind = "  " if Report.current_event.status == "Start" else " "
                tutor_string = Report.current_event.status + ind + Report.current_event.tutorial_code
                if tutor_string not in real_tutorial_order and Report.current_user.installed_app_version == min_version:
                    real_tutorial_order.append(tutor_string)
        flush_user_info()

        print(levels_list)
        print(real_tutorial_order)
        levels_list = get_levels_list(fail=True, tutorial_order=real_tutorial_order)
        print(levels_list)
        df = pd.DataFrame(index=levels_list,
                          columns=parameters)
        for lvl in levels_list:
            print(lvl)
            for param in parameters:
                df.at[lvl, param] = funnel_data[lvl][param]
                # print(lvl,df.at[lvl, "Retention"],funnel_data[lvl]["Retention"])
        df = df.fillna(0)

        previous_quest_value = Report.total_users

        sum_loss = sum(df["Last event loss"])

        for level in df.index.values:
            if df.at[level, "Retention"]:
                df.loc[level, "Retention %"] = str(round(df.at[level, "Retention"] * 100 / Report.total_users, 1)) + "%"
            diff = round((previous_quest_value - df.at[level, "Retention"]) * 100 / Report.total_users, 1)
            # Квесты и туториалы
            if len(level[8:]) > 4:
                df.loc[level, "Quest loss"] = "-" + str(diff) + "%"
                previous_quest_value = df.at[level, "Retention"]

            # Уровни
            else:
                if "Fail" not in level:
                    df.loc[level, "Level loss"] = "-" + str(diff) + "%"

                if "Finish" in level and df.at[level, "Retention"]:
                    df.loc[level, "FinishGame"] = str(
                        round(df.at[level, "FinishGame"] * 100 / df.at[level, "Retention"], 1)) + "%"

            if df.at[level, "Last event loss"]:
                df.loc[level, "loss %"] = str(round(df.at[level, "Last event loss"] * 100 / sum_loss, 1)) + "%"
            if level in loss_premium_coins.keys():
                df.loc[level, "Coins"] = str(
                    int((sum(loss_premium_coins[level]) / len(loss_premium_coins[level])))) + " +-" + str(
                    int(sigma(loss_premium_coins[level])))

        df["Level loss"].replace(0, "", inplace=True)
        df["Quest loss"].replace(0, "", inplace=True)
        df["loss %"].replace(0, "", inplace=True)
        df["Retention"].replace(0, "", inplace=True)
        df["Retention %"].replace(0, "", inplace=True)
        df["FinishGame"].replace(0, "", inplace=True)
        df["Last event loss"].replace(0, "", inplace=True)
        df["Coins"].replace(0, "", inplace=True)

        print("Loss after", days_left, "days.")
        print("Users opened game:", opened_game)
        print(df.to_string())

        for level in df.index.values:
            if "Start" in level:
                value = level[7:]
                new_level = "Start    " + value
                df = df.rename(index={level: new_level})
        writer = pd.ExcelWriter("Results/Глобальные отвалы/QuestsFunnel " + str(min_version) + " " + os_str + ".xlsx")
        df.to_excel(excel_writer=writer, sheet_name=str(min_version))
        writer.save()
