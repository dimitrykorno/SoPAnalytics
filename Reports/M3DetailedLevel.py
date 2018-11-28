import pandas as pd
from datetime import datetime
from Classes.Events import *
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from report_api.Utilities.Utils import time_count
from Utilities.Colors import Colors
from Utilities.Targets import Targets
from Utilities.Super import Supers
from Utilities.Quests import get_levels, get_next_locquest

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[],
               level_num="0030",
               days_left=1):
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
        next_quest = get_next_locquest(level_num)
        next_quest_levels = get_levels(locquest=next_quest)
        Report.set_events_data(additional_parameters=[],
                               period_start=period_start,
                               period_end=None,
                               min_version=None,
                               max_version=None,
                               events_list=[("Match3Events", "%{}%".format(level_num)),
                                            ("CityEvent", ["%InitGameState%"] + ["%StartGame%{}%".format(lvl) for lvl in
                                                                                 next_quest_levels])])

        df_detailed_play = pd.DataFrame(index=[0],
                                        columns=["Start", "Finish", "Time", "Win", "Lose", "Steps used", "Steps left",
                                                 "Steps total",
                                                 "Goal 1", "Goal 2", "Goal 1 total", "Goal 2 total", "B 1", "B 2",
                                                 "B 3", "Hammer",
                                                 "Got coins", "Red", "Yellow", "Blue", "Green", "White", "Black",
                                                 "SmallLightning_h",
                                                 "SmallLightning_v",
                                                 "FireSpark", "FireRing", "BigLightning_h", "BigLightning_v",
                                                 "SphereOfFire", "Stone",
                                                 "Weight", "Lamp", "TwoStarBonus", "StarBonus",
                                                 "Box_l1", "Box_l2", "Box_l3", "Carpet_l1", "Carpet_l2", "Chain_l1"])
        df_detailed_play.fillna(0, inplace=True)

        left_par = "Left {}d+".format(days_left)
        user_param = ["Users"]
        params = ["Completed", left_par, "0 Lives", "Played next quest"]
        parameters = user_param + params
        df_fails_funnel = pd.DataFrame(index=["Fail 0", "Fail 1", "Fail 2", "Fail 3", "Fail 4", "Fail 5", "Fail 6+"],
                                       columns=parameters)
        df_fails_funnel.fillna(0, inplace=True)

        # ПАРАМЕТРЫ
        index = -1
        current_session = None
        user_started_level = False
        user_fails_count = 0
        user_fail_data = dict.fromkeys(parameters, 0)
        fails_data = {}

        def flush_user_info():
            fail_index = "Fail " + str(user_fails_count) if user_fails_count <= 5 else "Fail 6+"
            if fail_index not in fails_data.keys():
                fails_data[fail_index] = dict.fromkeys(parameters, 0)
            if user_fail_data["Completed"]:
                user_fail_data["0 Lives"] = 0
            else:
                if Report.get_timediff(Report.previous_event.datetime, datetime.now().date(),
                                       measure="day") >= days_left:
                    user_fail_data[left_par] = 1
            for param in params:
                fails_data[fail_index][param] += user_fail_data[param]
            fails_data[fail_index]["Users"] += 1

        while Report.get_next_event():
            if Report.is_new_user():
                if user_started_level:
                    flush_user_info()
                user_fails_count = 0
                user_fail_data = dict.fromkeys(params, 0)
                user_started_level = False

            if isinstance(Report.current_event, Match3FailGame) and Report.current_event.level_num == level_num:
                user_fails_count += 1
                user_fail_data["0 Lives"] = int(Report.current_event.lives == 0)
            elif isinstance(Report.current_event,
                            Match3CompleteTargets) and Report.current_event.level_num == level_num:
                user_fail_data["Completed"] = 1
                user_fail_data["0 Lives"] = 0
            elif isinstance(Report.current_event,
                            CityEventsStartGame) and Report.current_event.level_num in next_quest_levels:
                user_fail_data["Played next quest"] = 1

            # Начало М3
            if Report.current_event.__class__ is Match3StartGame and Report.current_event.level_num == level_num:
                user_started_level = True
                index += 1
                # Начало игры
                df_detailed_play.at[index, "Start"] = Report.current_event.datetime
                # Общее кол-во данных шагов
                df_detailed_play.at[index, "Steps total"] = round(int(Report.current_event.turn_count), 0)
                # Цели 1 2
                df_detailed_play.loc[index, "Goal 1 total"] = str(
                    Report.current_event.targets_list[0].target) + ": " + str(
                    Report.current_event.targets_list[0].target_count)
                if Report.current_event.targets_list[1]:
                    df_detailed_play.loc[index, "Goal 2 total"] = str(
                        Report.current_event.targets_list[1].target) + ": " + str(
                        Report.current_event.targets_list[1].target_count)
                # Взятые стартовые бонусы
                df_detailed_play.at[index, "B 1"] = int(Report.current_event.start_bonuses.first)
                df_detailed_play.at[index, "B 2"] = int(Report.current_event.start_bonuses.second)
                df_detailed_play.at[index, "B 3"] = int(Report.current_event.start_bonuses.third)
                # Проверка на совпадение сессии
                current_session = Report.current_event.session_id

            elif Report.current_event.__class__ is Match3CompleteTargets and \
                            Report.current_event.session_id == current_session:
                # Выполнение целей
                df_detailed_play.at[index, "Finish"] = Report.current_event.datetime
                # Время на уровне
                df_detailed_play.loc[index, "Time"] = str(
                    int(df_detailed_play.loc[index, "Finish"].timestamp() - df_detailed_play.loc[
                        index, "Start"].timestamp())) + "s"
                # Победа
                df_detailed_play.at[index, "Win"] = 1
                # Использованные и оставшиеся ходы
                df_detailed_play.at[index, "Steps used"] = Report.current_event.turn_count
                df_detailed_play.at[index, "Steps left"] = df_detailed_play.at[
                                                               index, "Steps total"] - Report.current_event.turn_count
                # Цели 1 2
                df_detailed_play.loc[index, "Goal 1"] = str(Report.current_event.targets_list[0].target_count)
                if Report.current_event.targets_list[1]:
                    df_detailed_play.loc[index, "Goal 2"] = str(Report.current_event.targets_list[1].target_count)
                # Собранная пыль
                df_detailed_play.at[index, "Got coins"] = Report.current_event.game_currency_count
                # Использование молотка
                df_detailed_play.at[index, "Hammer"] = Report.current_event.ingame_bonuses
                # Собранные элементы
                add_elements(df_detailed_play, index, Report.current_event)

            elif Report.current_event.__class__ is Match3FinishGame and \
                            Report.current_event.session_id == current_session:
                # Конец уровня (перезапись)
                df_detailed_play.at[index, "Finish"] = Report.current_event.datetime
                # Получено пыли (дополнение после magic time)
                df_detailed_play.at[index, "Got coins"] = Report.current_event.game_currency_count

            elif Report.current_event.__class__ is Match3FailGame and \
                            Report.current_event.session_id == current_session:
                # Конец уровня
                df_detailed_play.at[index, "Finish"] = Report.current_event.datetime
                # Поражение
                df_detailed_play.at[index, "Lose"] = 1
                # Время на уровне
                df_detailed_play.loc[index, "Time"] = str(
                    int(df_detailed_play.loc[index, "Finish"].timestamp() - df_detailed_play.at[
                        index, "Start"].timestamp())) + "s"
                # Использованные и оставшиеся ходы
                df_detailed_play.at[index, "Steps used"] = Report.current_event.turn_count
                df_detailed_play.at[index, "Steps left"] = df_detailed_play.at[
                                                               index, "Steps total"] - Report.current_event.turn_count
                # Цели 1 2
                df_detailed_play.loc[index, "Goal 1"] = str(Report.current_event.targets_list[0].target_count)
                if Report.current_event.targets_list[1]:
                    df_detailed_play.loc[index, "Goal 2"] = str(Report.current_event.targets_list[1].target_count)
                df_detailed_play.at[index, "Hammer"] = Report.current_event.ingame_bonuses
                add_elements(df_detailed_play, index, Report.current_event)
        if user_started_level:
            flush_user_info()
        # Вывод
        df_detailed_play.fillna("", inplace=True)
        print(df_detailed_play.to_string())
        writer = pd.ExcelWriter(
            "Results/Анализ прохождения уровня/Detailed level " + str(level_num) + " " + os_str + ".xlsx")
        df_detailed_play.to_excel(excel_writer=writer)
        writer.save()

        for fails_count in fails_data:
            df_fails_funnel.loc[fails_count, "Users"] = fails_data[fails_count]["Users"]
            df_fails_funnel.loc[fails_count, "Completed"] = str(fails_data[fails_count]["Completed"]) + " (" + str(
                round(fails_data[fails_count]["Completed"] * 100 / fails_data[fails_count]["Users"])) + "%)"
            df_fails_funnel.loc[fails_count, left_par] = str(fails_data[fails_count][left_par]) + " (-" + str(
                round(fails_data[fails_count][left_par] * 100 / fails_data[fails_count]["Users"])) + "%)"
            df_fails_funnel.loc[fails_count, "0 Lives"] = str(fails_data[fails_count]["0 Lives"]) + " (" + str(
                round(fails_data[fails_count]["0 Lives"] * 100 / fails_data[fails_count][left_par])) + "%)"
            df_fails_funnel.loc[fails_count, "Played next quest"] = str(
                fails_data[fails_count]["Played next quest"]) + " (" + str(
                round(fails_data[fails_count]["Played next quest"] * 100 / fails_data[fails_count]["Completed"])) + "%)"
        print(df_fails_funnel.to_string())
        writer = pd.ExcelWriter(
            "Results/Анализ прохождения уровня/Воронка фейлов " + str(level_num) + " " + os_str + ".xlsx")
        df_fails_funnel.to_excel(excel_writer=writer)
        writer.save()


def add_elements(df, index, event):
    for element in event.elements_count.colors_count:
        element_obj=Colors.get_super(element)
        if element_obj:
            element_name = element if not element.startswith("Super_") else element[7:]
            df.loc[index,element_name] = event.elements_count.colors_count[element]
    for element in event.elements_count.super_count:
        element_obj = Supers.get_super(element)
        if element_obj:
            element_name = element if not element.startswith("Super_") else element[7:]
            df.loc[index, element_name] = event.elements_count.super_count[element]
    for element in event.elements_count.targets_count:
        element_obj = Targets.get_super(element)
        if element_obj:
            element_name = element if not element.startswith("Super_") else element[7:]
            df.loc[index, element_name] = event.elements_count.targets_count[element]
    for element in event.elements_count.others_count:
        element_name = element if not element.startswith("Super_") else element[7:]
        df.loc[index, element_name] = event.elements_count.others_count[element]
