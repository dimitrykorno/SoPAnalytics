from sop_analytics.Utilities.Shop import get_price
import pandas as pd
from datetime import timedelta
from sop_analytics.Utilities.Quests import get_level_names
from sop_analytics.Classes.Events import *
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from report_api.Report import Report
from datetime import datetime
from report_api.Utilities.Utils import time_count, outliers_iqr, try_save_writer, check_folder, check_arguments
import os




# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS","Android"],
               period_start="2018-11-01",
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[],
               start=1,
               quantity=100,
               days_left=None,
               days_max=None,
               china=False):
    app = "sop"
    if china:
        app="sopchina"
    errors = check_arguments(locals())
    result_files = []
    folder_dest = "Results/Отчёт по качеству уровней/"
    if hasattr(new_report,'user'):
        folder_dest+=str(new_report.user)+"/"
    check_folder(folder_dest)
    #print(errors)
    if errors:
        return errors, result_files

    if not days_max:
        days_max = 365
    days_max = int(days_max)
    if not days_left:
        if days_max >= 28:
            days_left = 14
        elif days_max >= 14:
            days_left = 7
        elif days_max >= 7:
            days_left = 3
        else:
            days_left = 999
    else:
        days_left=int(days_left)
    if start is None:
        start=1
    else:
        start=int(start)
    if quantity is None:
        quantity=200
    else:
        quantity=int(quantity)
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.strptime(period_end, "%Y-%m-%d").date()
    if min_version:
        min_version.replace(",", ".")
    if max_version:
        max_version.replace(",", ".")


    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User,
                            os=os_str, app=app, user_status_check=True)

        Report.set_installs_data(additional_parameters=[],
                                 period_start=period_start,
                                 period_end=period_end,
                                 min_version=min_version,
                                 max_version=max_version,
                                 countries_list=countries_list)
        # поддержка а-б тестов
        Report.set_events_data(additional_parameters=[],
                               period_start=period_start,
                               period_end=None,
                               min_version=None,
                               max_version=None,
                               events_list=[("Match3Events",),
                                            ("", "%Match3Events%"),
                                            ("CityEvent", "%StartGame%"),
                                            ("", "%CityEvent%StartGame%")])

        left_par = "Left " + str(days_left) + "+ days"
        levels = get_level_names(start, quantity)
        parameters = ["Started", "Finished", "Start Convertion", "Clean Start", "Clean Finish", left_par,
                      "Difficulty", "Clean Difficulty", "Attempts", "Clean Attempts",
                      "Purchases Sum", "Purchases", "First purchase", "ARPU", "Dust", "Dust on hands"]

        def start_finish():
            if Report.current_event.__class__ is Match3StartGame:
                started_levels.add(current_level)
            elif Report.current_event.__class__ in (Match3FinishGame, Match3CompleteTargets):
                finished_levels.add(current_level)

        def clean_start_finish():
            if Report.current_event.__class__ is Match3StartGame:
                if Report.current_event.start_bonuses.first or \
                        Report.current_event.start_bonuses.second or \
                        Report.current_event.start_bonuses.third:
                    return False
                else:
                    user_levels_data[current_level]["Clean Start"] += 1
                    return True

            elif Report.current_event.__class__ is Match3CompleteTargets:
                # проверка на чистую игру на этой версии приложения
                if clean_start:
                    # если не использовал молоток, то чисто
                    if Report.current_event.ingame_bonuses == 0:
                        user_levels_data[current_level]["Clean Finish"] += 1
                        return True
                    else:
                        # если использовал - отбираем чистый старт
                        user_levels_data[current_level]["Clean Start"] -= 1
                        return False
            return clean_start

        def difficulty():
            if Report.current_event.__class__ is Match3StartGame:
                # в сложнотсти считаем все старты уровней
                user_levels_data[current_level]["Difficulty"] += 1

        def attempts():

            if Report.current_event.__class__ is Match3CompleteTargets:
                # количество попыток пройти уровень
                if user_levels_data[current_level]["Attempts"] == 0:
                    user_levels_data[current_level]["Attempts"] = 1

            elif Report.current_event.__class__ is Match3FailGame:
                # Увеличиваем счетчик попыток
                user_levels_data[current_level]["Attempts"] += 1

        def clean_attempts():

            if Report.current_event.__class__ is Match3CompleteTargets:
                if clean_start and Report.current_event.ingame_bonuses == 0:
                    # количество чистых попыток пройти уровень
                    if user_levels_data[current_level]["Clean Attempts"] == 0:
                        user_levels_data[current_level]["Clean Attempts"] = 1

            elif Report.current_event.__class__ is Match3FailGame:
                if clean_start and Report.current_event.ingame_bonuses == 0:
                    user_levels_data[current_level]["Clean Attempts"] += 1

        def purchases():
            if Report.current_event.__class__ is Match3BuyPremiumCoin and Report.current_event.status == "Success":
                user_levels_data[current_level]["Purchases"] += 1
                user_levels_data[current_level]["Purchases Sum"] += get_price(Report.current_event.obj_name,
                                                                              money="rub")

                # Считаем первые покупки игроков
                if first_purchase:
                    user_levels_data[current_level]["First purchase"] += 1
                    return False
            return first_purchase

        def dust():
            if Report.current_event.__class__ is Match3FinishGame:
                # Добавляем собранную на уровне пыль
                user_levels_data[current_level]["Dust"] = Report.current_event.game_currency_count
                # Добавляем пыль на руках у игроков
                user_levels_data[current_level]["Dust on hands"] = Report.current_user.game_coin

        # Стартовые параметры
        user_test_groups = set()
        report_data = {}
        users_count = {}

        def add_new_test(test_name):
            report_data[test_name] = {}
            for level in levels:
                report_data[test_name][level] = dict.fromkeys(parameters, 0)
                report_data[test_name][level]["Attempts"] = []
                report_data[test_name][level]["Clean Attempts"] = []
                report_data[test_name][level]["Dust"] = []
                report_data[test_name][level]["Dust on hands"] = []

        user_levels_data = {}
        for level in levels:
            user_levels_data[level] = dict.fromkeys(parameters, 0)
        started_levels = set()
        finished_levels = set()
        first_purchase = True
        current_level = None
        clean_start = True

        def flush_user_data():
            # если вышло время, то работаем с текущим пользователем
            if Report.is_new_user():
                user = Report.previous_user
            else:
                user = Report.current_user
            # если игрок попал в группу АБ-теста, мы не добавляем его в группу А
            for test_name in [group for group in user_test_groups if
                              not (group == "A" and len(user_test_groups) > 1)]:
                if test_name not in report_data:
                    add_new_test(test_name)
                    users_count[test_name] = 0
                    users_count["total"] = 0
                # считаем юзеров в каждом тесте
                users_count[test_name] += 1
                users_count["total"] += 1
                # переносим пользовательские данные
                for param in ["Clean Start", "Clean Finish", "Difficulty",
                              "Purchases Sum", "Purchases", "First purchase"]:
                    for lvl in started_levels:
                        report_data[test_name][lvl][param] += user_levels_data[lvl][param]
                        report_data["total"][lvl][param] += user_levels_data[lvl][param]
                for param in ["Attempts", "Clean Attempts", "Dust", "Dust on hands"]:
                    for lvl in started_levels:
                        if param in ("Attempts", "Clean Attempts") and user_levels_data[lvl][param] == 0:
                            continue
                        report_data[test_name][lvl][param].append(user_levels_data[lvl][param])
                        report_data["total"][lvl][param].append(user_levels_data[lvl][param])
                for level1 in started_levels:
                    report_data[test_name][level1]["Started"] += 1
                    report_data["total"][level1]["Started"] += 1
                for level2 in finished_levels:
                    report_data[test_name][level2]["Finished"] += 1
                    report_data["total"][level2]["Finished"] += 1

                # Проверка на отвал
                # При отсутствии максимального дня в игре (для среза выборки) берется макс дата из базы данных.
                # print(days_max, user.install_date + timedelta(days=days_max) > datetime.now().date(),Report.get_timediff(user.last_enter.date(), datetime.now().date(), measure="day"),days_left)
                if ((not days_max or user.install_date + timedelta(days=days_max) > datetime.now().date()) and
                            Report.get_timediff(user.last_enter.date(), datetime.now().date(),
                                                measure="day") >= days_left) \
                        or \
                        (days_max and user.last_enter.date() > user.install_date + timedelta(days=days_max) and
                                 Report.get_timediff(user.last_enter.date(), user.install_date + timedelta(
                                     days=days_max), measure="day") > days_left):
                    # print("got")
                    if started_levels:
                        for level3 in list(started_levels - finished_levels):
                            report_data[test_name][level3][left_par] += 1

        add_new_test("total")
        while Report.get_next_event():

            # Событие М3 - может смениться уровень
            if Report.current_event.__class__ in (
                    Match3BuyPremiumCoin, Match3CompleteTargets, Match3FinishGame, Match3StartGame, Match3FailGame):
                current_level = Report.current_event.level_num


            # print(current_level,levels,Report.current_event.__class__.__name__)
            # print(Report.current_event.to_string())
            # Нвоый пользователь
            if (Report.is_new_user() and not Report.previous_user.is_skipped()) or (
                        Report.get_time_since_install() > days_max):
                flush_user_data()
                # сброс личных параметров
                user_test_groups = set()
                user_levels_data = {}
                for level in levels:
                    user_levels_data[level] = dict.fromkeys(parameters, 0)
                started_levels = set()
                finished_levels = set()
                first_purchase = True
                clean_start = True

                if days_max and not Report.is_new_user() and Report.get_time_since_install(
                        user="current") > days_max:
                    Report.skip_current_user()
                    continue

                #если странный пользователь, у которого первый уровень не 0001, то не рассматрвиаем
                if current_level != "0001":
                    Report.skip_current_user()
                    continue
            # Если уровень из списка рассматрвиаемых
            if current_level in levels:
                start_finish()
                clean_start = clean_start_finish()
                difficulty()
                attempts()
                clean_attempts()
                first_purchase = purchases()
                dust()
                # поддержка АБ-тестов
                user_test_groups.add(Report.current_event.test_name)

        flush_user_data()

        file_name = folder_dest + "Levels " + str(start) + "-" + str(
            start + quantity - 1) + " " + str(min_version) + " " + os_str + ".xlsx"
        writer = pd.ExcelWriter(file_name)

        for test in report_data:
            df = pd.DataFrame(index=levels,
                              columns=parameters)
            df = df.fillna(0)

            for level in levels:
                df.at[level, "Started"] = report_data[test][level]["Started"]
                df.at[level, "Finished"] = report_data[test][level]["Finished"]
                df.at[level, "Purchases"] = report_data[test][level]["Purchases"]
                df.at[level, "Purchases Sum"] = report_data[test][level]["Purchases Sum"]
                df.at[level, "First purchase"] = report_data[test][level]["First purchase"]
                df.at[level, "Clean Start"] = report_data[test][level]["Clean Start"]
                df.at[level, "Clean Finish"] = report_data[test][level]["Clean Finish"]
                df.at[level, "Difficulty"] = report_data[test][level]["Difficulty"]
                df.at[level, left_par] = report_data[test][level][left_par]

            # Финальные рассчеты
            df["Start Convertion"] = round(df["Started"] * 100 / users_count[test], 1)
            df["Difficulty"] = round(100 - df["Finished"] * 100 / df["Difficulty"], 0)
            df["Clean Difficulty"] = round(100 - df["Clean Finish"] * 100 / df["Clean Start"], 0)
            df["ARPU"] = round(df["Purchases Sum"] / df["Started"], 1)
            for level in levels:
                # проверка на выбросы в попытках
                if len(report_data[test][level]["Attempts"]) > 0:
                    report_data[test][level]["Attempts"] = outliers_iqr(report_data[test][level]["Attempts"],
                                                                        level + " attempts", multiplier=10,
                                                                        print_excl=False)
                    df.at[level, "Attempts"] = round(
                        1 - 1 / (
                        sum(report_data[test][level]["Attempts"]) / len(report_data[test][level]["Attempts"])),
                        3) * 100

                if len(report_data[test][level]["Clean Attempts"]) > 0:
                    report_data[test][level]["Clean Attempts"] = outliers_iqr(
                        report_data[test][level]["Clean Attempts"], level + " clean attempts",
                        multiplier=30, print_excl=False)
                    df.at[level, "Clean Attempts"] = round(
                        1 - 1 / (sum(report_data[test][level]["Clean Attempts"]) / len(
                            report_data[test][level]["Clean Attempts"])),
                        3) * 100

                # Проверка на выбросы в значениях пыли
                if len(report_data[test][level]["Dust"]) > 0:
                    if len(report_data[test][level]["Dust"]) > 10:
                        report_data[test][level]["Dust"] = outliers_iqr(report_data[test][level]["Dust"],
                                                                        level + " collected dust", multiplier=5,
                                                                        print_excl=False)
                    df.at[level, "Dust"] = round(
                        sum(report_data[test][level]["Dust"]) / float(len(report_data[test][level]["Dust"])), 1)

                if len(report_data[test][level]["Dust on hands"]) > 0:
                    if len(report_data[test][level]["Dust on hands"]) > 10:
                        report_data[test][level]["Dust on hands"] = outliers_iqr(
                            data_list=report_data[test][level]["Dust on hands"], where=level + " user dust",
                            max_outliers=False, min_outliers=True, multiplier=15, print_excl=False)
                        report_data[test][level]["Dust on hands"] = outliers_iqr(
                            report_data[test][level]["Dust on hands"], level + " user dust", multiplier=5,
                            print_excl=False)
                    df.at[level, "Dust on hands"] = round(sum(report_data[test][level]["Dust on hands"]) / float(
                        len(report_data[test][level]["Dust on hands"])), 1)

            # Печать
            # print("Total users group", test, users_count[test])
            # print(df.to_string())

            df.to_excel(excel_writer=writer, sheet_name=test)
        try_save_writer(writer,file_name)
        result_files.append(os.path.abspath(file_name))
    return errors, result_files
