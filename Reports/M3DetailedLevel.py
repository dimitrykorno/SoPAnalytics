from Classes.Report import Report
from Utilities.Utils import time_count
import pandas as pd
from Classes.Events import *
import datetime


@time_count
def new_report(level_num="0030", report_app_version="5.3"):
    # БАЗА ДАННЫХ
    sql = """
        SELECT ios_ifa, ios_ifv, event_name, event_json, event_datetime
        FROM sop_events.events_ios
        WHERE app_version_name={}
        AND event_name = "Match3Events" and event_json like "%{}%"
        order by ios_ifa, ios_ifv,  event_datetime
        """.format(report_app_version,level_num)
    report = Report(sql_events=sql)

    df = pd.DataFrame(index=[0],
                      columns=["Start", "Finish", "Time", "Win", "Lose", "Steps used", "Steps left", "Steps total",
                               "Goal 1", "Goal 2", "Goal 1 total", "Goal 2 total", "B 1", "B 2", "B 3", "Hammer",
                               "Got coins", "Red", "Yellow", "Blue", "Green", "White", "Black", "SmallLightning_h",
                               "SmallLightning_v",
                               "FireSpark", "FireRing", "BigLightning_h", "BigLightning_v", "SphereOfFire", "Stone",
                               "Weight", "Lamp", "TwoStarBonus", "StarBonus",
                               "Box_l1", "Box_l2", "Box_l3", "Carpet_l1", "Carpet_l2", "Chain_l1"])
    df.fillna("", inplace=True)

    # ПАРАМЕТРЫ
    index = -1
    current_session = None

    while report.get_next_event():

        # Начало М3
        if report.current_event.__class__ is Match3StartGame and report.current_event.level_num == level_num:
            index += 1
            # Начало игры
            df.loc[index, "Start"] = report.current_event.datetime
            # Общее кол-во данных шагов
            df.loc[index, "Steps total"] = round(int(report.current_event.turn_count), 0)
            # Цели 1 2
            df.loc[index, "Goal 1 total"] = str(report.current_event.targets_list[0].target) + ": " + str(
                report.current_event.targets_list[0].target_count)
            if report.current_event.targets_list[1]:
                df.loc[index, "Goal 2 total"] = str(report.current_event.targets_list[1].target) + ": " + str(
                    report.current_event.targets_list[1].target_count)
            # Взятые стартовые бонусы
            df.loc[index, "B 1"] = int(report.current_event.start_bonuses.first)
            df.loc[index, "B 2"] = int(report.current_event.start_bonuses.second)
            df.loc[index, "B 3"] = int(report.current_event.start_bonuses.third)
            # Проверка на совпадение сессии
            current_session = report.current_event.session_id

        elif report.current_event.__class__ is Match3CompleteTargets and report.current_event.session_id == current_session:
            # Выполнение целей
            df.loc[index, "Finish"] = report.current_event.datetime
            # Время на уровне
            df.loc[index, "Time"] = str(
                int(df.loc[index, "Finish"].timestamp() - df.loc[index, "Start"].timestamp())) + "s"
            # Победа
            df.loc[index, "Win"] = 1
            # Использованные и оставшиеся ходы
            df.loc[index, "Steps used"] = report.current_event.turn_count
            df.loc[index, "Steps left"] = df.loc[index, "Steps total"] - report.current_event.turn_count
            # Цели 1 2
            df.loc[index, "Goal 1"] = str(report.current_event.targets_list[0].target_count)
            if report.current_event.targets_list[1]:
                df.loc[index, "Goal 2"] = str(report.current_event.targets_list[1].target_count)
            # Собранная пыль
            df.loc[index, "Got coins"] = report.current_event.game_currency_count
            # Использование молотка
            df.loc[index, "Hammer"] = report.current_event.ingame_bonuses
            # Собранные элементы
            add_elements(df, index, report.current_event)

        elif report.current_event.__class__ is Match3FinishGame and report.current_event.session_id == current_session:
            # Конец уровня (перезапись)
            df.loc[index, "Finish"] = report.current_event.datetime
            # Получено пыли (дополнение после magic time)
            df.loc[index, "Got coins"] = report.current_event.game_currency_count

        elif report.current_event.__class__ is Match3FailGame and report.current_event.session_id == current_session:
            # Конец уровня
            df.loc[index, "Finish"] = report.current_event.datetime
            # Поражение
            df.loc[index, "Lose"] = 1
            # Время на уровне
            df.loc[index, "Time"] = str(
                int(df.loc[index, "Finish"].timestamp() - df.loc[index, "Start"].timestamp())) + "s"
            # Использованные и оставшиеся ходы
            df.loc[index, "Steps used"] = report.current_event.turn_count
            df.loc[index, "Steps left"] = df.loc[index, "Steps total"] - report.current_event.turn_count
            # Цели 1 2
            df.loc[index, "Goal 1"] = str(report.current_event.targets_list[0].target_count)
            if report.current_event.targets_list[1]:
                df.loc[index, "Goal 2"] = str(report.current_event.targets_list[1].target_count)
            df.loc[index, "Hammer"] = report.current_event.ingame_bonuses
            add_elements(df, index, report.current_event)

    # Вывод
    df.fillna("", inplace=True)
    print(df.to_string())
    writer = pd.ExcelWriter("Detailed level " + str(level_num) + ".xlsx")
    df.to_excel(excel_writer=writer)
    writer.save()



def add_elements(df, index, event):
    for element in event.elements_count.colors_count:
        df.loc[index, str(element)[7:]] = event.elements_count.colors_count[element]
    for element in event.elements_count.super_count:
        df.loc[index, str(element)[7:]] = event.elements_count.super_count[element]
    for element in event.elements_count.targets_count:
        df.loc[index, str(element)[8:]] = event.elements_count.targets_count[element]
    for element in event.elements_count.others_count:
        df.loc[index, str(element)] = event.elements_count.others_count[element]
