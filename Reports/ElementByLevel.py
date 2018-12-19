from report_api.Utilities.Utils import time_count, try_save_writer, check_arguments, check_folder
import pandas as pd
from sop_analytics.Utilities.Quests import get_level_names
from sop_analytics.Utilities.Colors import Colors
from sop_analytics.Utilities.Targets import Targets
from sop_analytics.Utilities.Super import Supers
from sop_analytics.Classes.Events import *
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from report_api.Report import Report
import os
app = "sop"


@time_count
def new_report(os_list=["iOS"],
               levels_start=1,
               levels_quant=200,
               elements=["StarBonus"],
               period_start=None,
               period_end=None,
               min_version="7.4",
               max_version=None,
               countries_list=[]):
    errors = check_arguments(locals())
    result_files = []
    folder_dest = "Results/Анализ элементов на уровне/"
    if hasattr(new_report,'user'):
        folder_dest+=str(new_report.user)+"/"
    check_folder(folder_dest)

    if errors:
        return errors, result_files

    for i in range(len(elements)):
        if Supers.get_super(elements[i]):
            continue
        elif Supers.get_super("Super_" + elements[i]):
            elements[i] = "Super_" + elements[i]
            continue
        elif Targets.get_target(elements[i]):
            continue
        elif Colors.get_color(elements[i]):
            continue
        elif Colors.get_color("Color6_" + elements[i]):
            elements[i] = "Color6_" + elements[i]
            continue
        else:
            #print("Элемента нет в базе:", elements[i], ". Это может вызвать ошибки.")
            errors += "Элемента нет в базе: " + str(elements[i]) + ". Это может вызвать ошибки.\n"
    if not levels_start:
        levels_start=1
    else:
        levels_start=int(levels_start)
    if not levels_quant:
        levels_quant=200
    else:
        levels_quant=int(levels_quant)
    # БАЗА ДАННЫХ
    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User, event_class=Event,
                            os=os_str, app=app, user_status_check=True)

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
                               events_list=[("Match3Events", ["%StartGame%", "%FailGame%", "%CompleteTarget%"]),
                                            ("", ["%Match3Events%StartGame%", "%Match3Events%FailGame%",
                                                  "%Match3Events%CompleteTarget%"])])

        levels = get_level_names(start=levels_start, quantity=levels_quant)
        report_data = {}

        def add_test(name):
            report_data[name] = {}
            for lvl in levels:
                report_data[name][lvl] = {}
                for element in elements:
                    report_data[name][lvl][element] = []

        add_test("total")
        session_id = None
        current_level = None
        test_name = None
        start_bonuses = (0, 0, 0)
        start_bonus_names = (
            ["Super_BigLightning_h", "Super_BigLightning_v"], ["StarBonus"], ["StarBonus", "Super_FireSpark"])
        in_game_bonus_names = ["Hammer"]
        while Report.get_next_event():

            if isinstance(Report.current_event, Match3StartGame):

                test_name = Report.current_event.test_name
                current_level = Report.current_event.level_num
                # если уровень больше. а без session_id дальше не пойдет
                if current_level not in levels:
                    current_level = None
                    continue
                session_id = Report.current_event.session_id
                start_bonuses = (Report.current_event.start_bonuses.first,
                                 Report.current_event.start_bonuses.second,
                                 Report.current_event.start_bonuses.third)
            # Если фейл, то сбрасываем session_id, чтобы не учитывать слующий CompleteTarget
            elif isinstance(Report.current_event, Match3FailGame) \
                    and Report.current_event.session_id == session_id \
                    and Report.current_event.level_num == current_level:
                session_id = None
                start_bonuses = (0, 0, 0)
            # Если это событие завершения задачи из той же сессии, что и старт уровня и не было фейла перед ней
            elif isinstance(Report.current_event, Match3CompleteTargets) \
                    and Report.current_event.session_id == session_id \
                    and Report.current_event.level_num == current_level:
                # считаем бонусы, взятые перед началом уровня
                taken_bonuses = []
                for i in range(3):
                    if start_bonuses[i] == 1:
                        taken_bonuses += start_bonus_names[i]
                        # print("new taken bonuses", taken_bonuses)
                for i in range(1):
                    if Report.current_event.ingame_bonuses == 1:
                        taken_bonuses += in_game_bonus_names[i]
                # добавляем категрию с текущей группой аб-теста (А, если теста нет)
                if test_name not in report_data:
                    add_test(test_name)
                # print(Report.current_event.to_string())

                # по искомым элементам смотрим, сколько из них было взорвано во время игры и вычитаем,
                # если они были в стартовых бонусах
                for element in [e for e in elements if e not in in_game_bonus_names]:
                    # print(element, sum(report_data["total"][current_level][element]), "+",
                    #       Report.current_event.elements_count.get_element_count(element), "-",
                    #       taken_bonuses.count(element), "=", end="")
                    report_data[test_name][current_level][element].append(max(
                        Report.current_event.elements_count.get_element_count(element) - taken_bonuses.count(element),
                        0))
                    report_data["total"][current_level][element].append(max(
                        Report.current_event.elements_count.get_element_count(element) - taken_bonuses.count(element),
                        0))
                for element in [e for e in elements if e in in_game_bonus_names]:
                    report_data[test_name][current_level][element].append(Report.current_event.ingame_bonuses)
                    report_data["total"][current_level][element].append(Report.current_event.ingame_bonuses)
                    # print(sum(report_data["total"][current_level][element]))

        filename = folder_dest + os_str + " " + min_version + " " + ",".join(
            elements) + " " + min(levels) + "-" + max(
            levels) + ".xlsx"
        writer = pd.ExcelWriter(filename)
        for test_name in report_data:
            df = pd.DataFrame(index=levels, columns=elements)
            df.fillna(0.0, inplace=True)
            for lvl in levels:
                # if lvl<"0015":
                #     print(test_name,lvl, report_data[test_name][lvl])
                for element in elements:
                    if len(report_data[test_name][lvl][element]) > 0:
                        df.at[lvl, element] = round(
                            sum(report_data[test_name][lvl][element]) / len(report_data[test_name][lvl][element]), 1)
                    else:
                        df.at[lvl, element] = 0

            df.to_excel(writer, sheet_name=test_name)
        try_save_writer(writer, filename)
        result_files.append(os.path.abspath(filename))
    return errors, result_files
