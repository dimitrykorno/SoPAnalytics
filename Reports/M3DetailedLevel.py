import pandas as pd
from Classes.Events import *
from report_api.OS import OS
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime
from report_api.Utilities.Utils import time_count

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[],
               level_num="0030"):
    # БАЗА ДАННЫХ

    for os_str in os_list:
        os = OS.get_os(os_str)
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
                               events_list=[("Match3Events", "%{}%".format(level_num))])

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

        while Report.get_next_event():

            # Начало М3
            if Report.current_event.__class__ is Match3StartGame and Report.current_event.level_num == level_num:
                index += 1
                # Начало игры
                df.loc[index, "Start"] = Report.current_event.datetime
                # Общее кол-во данных шагов
                df.loc[index, "Steps total"] = round(int(Report.current_event.turn_count), 0)
                # Цели 1 2
                df.loc[index, "Goal 1 total"] = str(Report.current_event.targets_list[0].target) + ": " + str(
                    Report.current_event.targets_list[0].target_count)
                if Report.current_event.targets_list[1]:
                    df.loc[index, "Goal 2 total"] = str(Report.current_event.targets_list[1].target) + ": " + str(
                        Report.current_event.targets_list[1].target_count)
                # Взятые стартовые бонусы
                df.loc[index, "B 1"] = int(Report.current_event.start_bonuses.first)
                df.loc[index, "B 2"] = int(Report.current_event.start_bonuses.second)
                df.loc[index, "B 3"] = int(Report.current_event.start_bonuses.third)
                # Проверка на совпадение сессии
                current_session = Report.current_event.session_id

            elif Report.current_event.__class__ is Match3CompleteTargets and \
                            Report.current_event.session_id == current_session:
                # Выполнение целей
                df.loc[index, "Finish"] = Report.current_event.datetime
                # Время на уровне
                df.loc[index, "Time"] = str(
                    int(df.loc[index, "Finish"].timestamp() - df.loc[index, "Start"].timestamp())) + "s"
                # Победа
                df.loc[index, "Win"] = 1
                # Использованные и оставшиеся ходы
                df.loc[index, "Steps used"] = Report.current_event.turn_count
                df.loc[index, "Steps left"] = df.loc[index, "Steps total"] - Report.current_event.turn_count
                # Цели 1 2
                df.loc[index, "Goal 1"] = str(Report.current_event.targets_list[0].target_count)
                if Report.current_event.targets_list[1]:
                    df.loc[index, "Goal 2"] = str(Report.current_event.targets_list[1].target_count)
                # Собранная пыль
                df.loc[index, "Got coins"] = Report.current_event.game_currency_count
                # Использование молотка
                df.loc[index, "Hammer"] = Report.current_event.ingame_bonuses
                # Собранные элементы
                add_elements(df, index, Report.current_event)

            elif Report.current_event.__class__ is Match3FinishGame and \
                            Report.current_event.session_id == current_session:
                # Конец уровня (перезапись)
                df.loc[index, "Finish"] = Report.current_event.datetime
                # Получено пыли (дополнение после magic time)
                df.loc[index, "Got coins"] = Report.current_event.game_currency_count

            elif Report.current_event.__class__ is Match3FailGame and \
                            Report.current_event.session_id == current_session:
                # Конец уровня
                df.loc[index, "Finish"] = Report.current_event.datetime
                # Поражение
                df.loc[index, "Lose"] = 1
                # Время на уровне
                df.loc[index, "Time"] = str(
                    int(df.loc[index, "Finish"].timestamp() - df.loc[index, "Start"].timestamp())) + "s"
                # Использованные и оставшиеся ходы
                df.loc[index, "Steps used"] = Report.current_event.turn_count
                df.loc[index, "Steps left"] = df.loc[index, "Steps total"] - Report.current_event.turn_count
                # Цели 1 2
                df.loc[index, "Goal 1"] = str(Report.current_event.targets_list[0].target_count)
                if Report.current_event.targets_list[1]:
                    df.loc[index, "Goal 2"] = str(Report.current_event.targets_list[1].target_count)
                df.loc[index, "Hammer"] = Report.current_event.ingame_bonuses
                add_elements(df, index, Report.current_event)

        # Вывод
        df.fillna("", inplace=True)
        print(df.to_string())
        writer = pd.ExcelWriter(
            "Results/Анализ прохождения уровня/Detailed level " + str(level_num) + " " + os_str + ".xlsx")
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
