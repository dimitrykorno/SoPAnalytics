from Data import Data
import pandas as pd
from Classes.Events import *
from Classes.OS import OS
from Classes.Report import Report
from Utilities.Quests import *
from Utilities.Utils import time_count, sigma, get_timediff


@time_count
def new_report(os=OS.ios, days_left=7, app_version="6.0", exact=True):
    '''
    Глобальные конверсии по квестам и уровням в них и отвалы с монетами на момент отвала

    !!!ВАЖНО!!! Порядок и положение туториалов меняется в зависимости от версии игры

    :param days_left: кол-во дней, после которого человек отвалился
    :param min_app_version: минимальная версия приложения
    :param exact: точное соответствие версии
    :return:
    '''
    last_event_date = Data.get_last_event_date(os)

    sql = """
    SELECT ios_ifv, ios_ifa,  event_name, event_json, event_datetime, app_version_name
    FROM sop_events.events_ios
    WHERE (event_name="Match3Events" 
    OR (event_name="CityEvent" and (
             event_json like "%StartGame%" 
             or event_json like '{"Quest%'
             or event_json like "%InitGameState%"
             or event_json like "%BuyPremiumCoin%Success%"))
    OR (event_name="Tutorial"))

    order by ios_ifa,ios_ifv, event_datetime
    """

    report = Report(sql_events=sql, user_status_check=True, min_app_version=app_version, exact=exact,
                    get_installs=True, max_install_version=app_version, min_install_version=app_version)
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
    for lvl in levels_list:
        funnel_data[lvl] = dict.fromkeys(parameters, 0)

    def flush_user_info():
        for lvl in started_levels:
            funnel_data["Start  " + lvl]["Retention"] += 1
        for lvl in completed_levels:
            funnel_data["Finish " + lvl]["Retention"] += 1
        for lvl in finished_levels:
            funnel_data["Finish " + lvl]["FinishGame"] += 1

        for quest in started_quests:
            funnel_data["Start  " + quest]["Retention"] += 1
        for quest in finished_quests:
            funnel_data["Finish " + quest]["Retention"] += 1

        for tutor in started_tutorials:
            funnel_data["Start  " + tutor]["Retention"] += 1
        for tutor in finished_tutorials:
            funnel_data["Finish " + tutor]["Retention"] += 1

        # Отвалы
        if get_timediff(report.previous_user.last_enter.date(), last_event_date,
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
            loss_premium_coins[last_game_point].append(report.previous_user.premium_coin)
            # ОСТАЛОСЬ: ПОСЧИТАТЬ СРЕДНЕЕ И +- СИГМЫ

    while report.get_next_event():

        # следующий игрок, обновление данных таблицы, сброс персональных данных
        if report.is_new_user():
            flush_user_info()
            opened_game += 1
            started_levels = set()
            completed_levels = set()
            finished_levels = set()
            started_quests = set()
            finished_quests = set()
            started_tutorials = set()
            finished_tutorials = set()

        if report.current_event.__class__ is Match3StartGame:
            started_levels.add(report.current_event.level_num)
            last_game_event = report.current_event

        elif report.current_event.__class__ is Match3FailGame:
            last_game_event = report.current_event

        elif report.current_event.__class__ is Match3CompleteTargets:
            completed_levels.add(report.current_event.level_num)
            last_game_event = report.current_event
        elif report.current_event.__class__ is Match3FinishGame:
            finished_levels.add(report.current_event.level_num)
            last_game_event = report.current_event

        elif report.current_event.__class__ is CityEventsQuest:
            if report.current_event.action == "Take":
                started_quests.add(report.current_event.quest)
            elif report.current_event.action in ("Сomplete", "Complete"):
                finished_quests.add(report.current_event.quest)
            last_game_event = report.current_event
            quest_string = report.current_event.action + " " + report.current_event.quest
            if quest_string not in real_tutorial_order:
                real_tutorial_order.append(quest_string)

        elif report.current_event.__class__ is Tutorial:
            if report.current_event.status == "Start":
                started_tutorials.add(report.current_event.tutorial_code)
            elif report.current_event.status == "Finish":
                finished_tutorials.add(report.current_event.tutorial_code)
            last_game_event = report.current_event
            '''
            if report.current_event.status == "Start" and report.current_user.installed_app_version==app_version:
                if "Start  "+report.current_event.tutorial_code not in real_tutorial_order:
                    real_tutorial_order.append("Start  "+report.current_event.tutorial_code)
                    real_tutorial_order.append("Finish "+report.current_event.tutorial_code)
            '''
            indent = "  " if report.current_event.status == "Start" else " "
            tutor_string = report.current_event.status + indent + report.current_event.tutorial_code
            if tutor_string not in real_tutorial_order and report.current_user.installed_app_version == app_version:
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

    previous_quest_value = report.total_users

    sum_loss = sum(df["Last event loss"])

    for level in df.index.values:
        if df.at[level, "Retention"]:
            df.loc[level, "Retention %"] = str(round(df.at[level, "Retention"] * 100 / report.total_users, 1)) + "%"
        diff = round((previous_quest_value - df.at[level, "Retention"]) * 100 / report.total_users, 1)
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
    writer = pd.ExcelWriter("QuestsFunnel " + app_version + ".xlsx")
    df.to_excel(excel_writer=writer, sheet_name=app_version)
    writer.save()
