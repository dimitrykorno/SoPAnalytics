from Utilities.Shop import get_price
import pandas as pd
from datetime import timedelta
from Utilities.Quests import get_level_names
from Classes.Events import *
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime
from report_api.Utilities.Utils import time_count, outliers_iqr

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[],
               start=1,
               quantity=100,
               days_left=None,
               days_max=3, ):
    if not days_left:
        if days_max >= 28:
            days_left = 14
        elif days_max >= 14:
            days_left = 7
        elif days_max >= 7:
            days_left = 3
        else:
            days_left = 999
    if not days_max:
        days_max = 365
    days_max = int(days_max)

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
                               events_list=[("Match3Events",),
                                            ("CityEvent", "%StartGame%")])

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
                    levels_data[current_level]["Clean Start"] += 1
                    return True

            elif Report.current_event.__class__ is Match3CompleteTargets:
                # проверка на чистую игру на этой версии приложения
                if clean_start:
                    # если не использовал молоток, то чисто
                    if Report.current_event.ingame_bonuses == 0:
                        levels_data[current_level]["Clean Finish"] += 1
                        return True
                    else:
                        # если использовал - отбираем чистый старт
                        levels_data[current_level]["Clean Start"] -= 1
                        return False
            return clean_start

        def difficulty():
            if Report.current_event.__class__ is Match3StartGame:
                # в сложнотсти считаем все старты уровней
                levels_data[current_level]["Difficulty"] += 1

        def attempts():

            if Report.current_event.__class__ is Match3CompleteTargets:
                # количество попыток пройти уровень
                if user_attempts[current_level] == 0:
                    user_attempts[current_level] = 1
                level_attempts[current_level].append(user_attempts[current_level])

            elif Report.current_event.__class__ is Match3FailGame:
                # Увеличиваем счетчик попыток
                user_attempts[current_level] += 1

        def clean_attempts():

            if Report.current_event.__class__ is Match3CompleteTargets:
                if clean_start and Report.current_event.ingame_bonuses == 0:
                    # количество чистых попыток пройти уровень
                    if user_clean_attempts[current_level] == 0:
                        user_clean_attempts[current_level] = 1
                    level_clean_attempts[current_level].append(user_clean_attempts[current_level])

            elif Report.current_event.__class__ is Match3FailGame:
                if clean_start and Report.current_event.ingame_bonuses == 0:
                    user_clean_attempts[current_level] += 1

        def purchases():
            if Report.current_event.__class__ is Match3BuyPremiumCoin and Report.current_event.status == "Success":
                levels_data[current_level]["Purchases"] += 1
                levels_data[current_level]["Purchases Sum"] += get_price(Report.current_event.obj_name, money="rub")

                # Считаем первые покупки игроков
                if first_purchase:
                    levels_data[current_level]["First purchase"] += 1
                    return False
            return first_purchase

        def dust():
            if Report.current_event.__class__ is Match3FinishGame:
                # Добавляем собранную на уровне пыль
                collected_dust[current_level].append(int(Report.current_event.game_currency_count))
                # Добавляем пыль на руках у игроков
                user_dust[current_level].append(Report.current_user.game_coin)

        # Стартовые параметры
        level_attempts = dict.fromkeys(levels)
        level_clean_attempts = dict.fromkeys(levels)
        user_attempts = dict.fromkeys(levels, 0)
        user_clean_attempts = dict.fromkeys(levels, 0)
        collected_dust = dict.fromkeys(levels)
        user_dust = dict.fromkeys(levels)
        user_clean_start = dict.fromkeys(levels)
        levels_data = {}
        for level in levels:
            levels_data[level] = dict.fromkeys(parameters, 0)
            level_attempts[level] = []
            level_clean_attempts[level] = []
            collected_dust[level] = []
            user_dust[level] = []
            user_clean_start[level] = []

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

            for level1 in finished_levels:
                levels_data[level1]["Started"] += 1
            for level2 in finished_levels:
                levels_data[level2]["Finished"] += 1

            # Проверка на отвал
            # При отсутствии максимального дня в игре (для среза выборки) берется макс дата из базы данных.
            #print(days_max, user.install_date + timedelta(days=days_max) > datetime.now().date(),Report.get_timediff(user.last_enter.date(), datetime.now().date(), measure="day"),days_left)
            if ((not days_max or user.install_date + timedelta(days=days_max) > datetime.now().date()) and
                        Report.get_timediff(user.last_enter.date(), datetime.now().date(), measure="day") >= days_left) \
                    or \
                    (days_max and user.last_enter.date()> user.install_date + timedelta(days=days_max) and
                             Report.get_timediff(user.last_enter.date(), user.install_date + timedelta(
                        days=days_max), measure="day") > days_left):
                #print("got")
                if started_levels:
                    for level3 in list(started_levels - finished_levels):
                        levels_data[level3][left_par] += 1

        while Report.get_next_event():

            # Событие М3 - может смениться уровень
            if Report.current_event.__class__ in (
                    Match3BuyPremiumCoin, Match3CompleteTargets, Match3FinishGame, Match3StartGame, Match3FailGame):
                current_level = Report.current_event.level_num

            # Если уровень из списка рассматрвиаемых
            if current_level in levels:
                # if Report.get_timediff(measure="day")>=1 or Report.is_new_user():
                # print(Report.current_user.user_id, Report.get_time_since_install(),
                # Report.get_time_since_last_enter(), Report.current_user.entries[-1], Report.is_new_user() )

                # Нвоый пользователь
                if (Report.is_new_user() and not Report.previous_user.is_skipped()) or (
                            Report.get_time_since_install() > days_max):
                    # print("flush",Report.is_new_user(), (Report.get_time_since_install() > days_max))
                    flush_user_data()
                    # сброс личных параметров
                    started_levels = set()
                    finished_levels = set()
                    user_attempts = dict.fromkeys(levels, 0)
                    user_clean_attempts = dict.fromkeys(levels, 0)
                    first_purchase = True

                    if days_max and not Report.is_new_user() and Report.get_time_since_install(
                            user="current") > days_max:
                        Report.skip_current_user()
                        continue
                start_finish()
                clean_start = clean_start_finish()
                difficulty()
                attempts()
                clean_attempts()
                first_purchase = purchases()
                dust()
        flush_user_data()

        df = pd.DataFrame(index=levels,
                          columns=parameters)
        df = df.fillna(0)

        for level in levels:
            df.at[level, "Started"] = levels_data[level]["Started"]
            df.at[level, "Finished"] = levels_data[level]["Finished"]
            df.at[level, "Purchases"] = levels_data[level]["Purchases"]
            df.at[level, "Purchases Sum"] = levels_data[level]["Purchases Sum"]
            df.at[level, "First purchase"] = levels_data[level]["First purchase"]
            df.at[level, "Clean Start"] = levels_data[level]["Clean Start"]
            df.at[level, "Clean Finish"] = levels_data[level]["Clean Finish"]
            df.at[level, "Difficulty"] = levels_data[level]["Difficulty"]
            df.at[level, left_par]=levels_data[level][left_par]

        # Финальные рассчеты
        df["Start Convertion"] = round(df["Started"] * 100 / Report.total_users, 1)
        df["Difficulty"] = round(100 - df["Finished"] * 100 / df["Difficulty"], 1)
        df["Clean Difficulty"] = round(100 - df["Clean Finish"] * 100 / df["Clean Start"], 1)
        df["ARPU"] = round(df["Purchases Sum"] / df["Started"], 1)
        for level in levels:
            # проверка на выбросы в попытках
            if len(level_attempts[level]) > 0:
                level_attempts[level] = outliers_iqr(level_attempts[level], level + " attempts", multiplier=10)
                df.at[level, "Attempts"] = round(1 - 1 / (sum(level_attempts[level]) / len(level_attempts[level])),
                                                 3) * 100

            if len(level_clean_attempts[level]) > 0:
                level_clean_attempts[level] = outliers_iqr(level_clean_attempts[level], level + " clean attempts",
                                                           multiplier=4)
                df.at[level, "Clean Attempts"] = round(
                    1 - 1 / (sum(level_clean_attempts[level]) / len(level_clean_attempts[level])),
                    3) * 100
            # Проверка на выбросы в значениях пыли
            if len(collected_dust[level]) > 0:
                if len(collected_dust[level]) > 10:
                    collected_dust[level] = outliers_iqr(collected_dust[level], level + " collected dust", multiplier=5)
                df.at[level, "Dust"] = round(sum(collected_dust[level]) / float(len(collected_dust[level])), 1)

            if len(user_dust[level]) > 0:
                if len(user_dust[level]) > 10:
                    user_dust[level] = outliers_iqr(data_list=user_dust[level], where=level + " user dust",
                                                    max_outliers=False, min_outliers=True, multiplier=15)
                    user_dust[level] = outliers_iqr(user_dust[level], level + " user dust", multiplier=5)
                df.at[level, "Dust on hands"] = round(sum(user_dust[level]) / float(len(user_dust[level])), 1)

        # Печать
        print("Total users:", Report.total_users)
        print(df.to_string())

        writer = pd.ExcelWriter(
            "Results/Отчёт по качеству уровней/Levels " + str(start) + "-" + str(
                start + quantity - 1) + " " + str(min_version) + " " + str(
                days_max) + "days " + os_str + ".xlsx")
        df.to_excel(excel_writer=writer)
        writer.save()
