from Data import Data
from Utilities.Utils import *
from Utilities.Shop import get_price
import pandas as pd
from Classes.Events import *
from Classes.Report import Report
from datetime import timedelta
from Utilities.Quests import get_level_names


@time_count
def new_report(start=1, quantity=100, days_left=None, days_max=3, install_app_version="6.5", exact=False,
               report_app_version=None):
    if not report_app_version:
        report_app_version=install_app_version
    if not days_left:
        if days_max >= 28:
            days_left = 14
        elif days_max >= 14:
            days_left = 7
        elif days_max >= 7:
            days_left = 3
        else:
            days_left = 999

    last_event_date = Data.get_last_event_date()
    days_max=int(days_max)
    sql = """
        SELECT ios_ifa,ios_ifv, event_name, event_json, event_datetime, app_version_name
        FROM sop_events.events_ios
        WHERE 
        (event_name = "Match3Events" 
            or (event_name = "CityEvent" 
                and (event_json like "%StartGame%"
                    )
                )
        )
        and
        (ios_ifa <>"" or ios_ifv <>"")
        order by ios_ifv, event_datetime,ios_ifv
        """
    max_install_version=None if not exact else install_app_version
    report = Report(sql_events=sql, user_status_check=True, exact=exact, min_app_version=install_app_version,
                    get_installs=True, min_install_version=install_app_version, max_install_version=max_install_version)
    left_par = "Left " + str(days_left) + "+ days"
    levels = get_level_names(start, quantity)
    df = pd.DataFrame(index=levels,
                      columns=["Started", "Finished", "Start Convertion", "Clean Start", "Clean Finish", left_par,
                               "Difficulty", "Clean Difficulty", "Attempts", "Clean Attempts",
                               "Purchases Sum", "Purchases", "First purchase", "ARPU", "Dust", "Dust on hands"])
    df = df.fillna(0)

    def start_finish():
        if report.current_event.__class__ is Match3StartGame:
            started_levels.add(current_level)
        elif report.current_event.__class__ in (Match3FinishGame, Match3CompleteTargets):
            finished_levels.add(current_level)

    def clean_start_finish():
        if report.current_event.__class__ is Match3StartGame:

            if report.current_app_version >= report_app_version:
                if report.current_event.start_bonuses.first or \
                        report.current_event.start_bonuses.second or \
                        report.current_event.start_bonuses.third:
                    return False
                else:
                    df.loc[current_level, "Clean Start"] += 1
                    return True

        elif report.current_event.__class__ is Match3CompleteTargets:
            # проверка на чистую игру на этой версии приложения
            if report.current_app_version >= report_app_version and clean_start:
                # если не использовал молоток, то чисто
                if report.current_event.ingame_bonuses == 0:
                    df.loc[current_level, "Clean Finish"] += 1
                    return True
                else:
                    # если использовал - отбираем чистый старт
                    df.loc[current_level, "Clean Start"] -= 1
                    return False
        return clean_start

    def difficulty():
        if report.current_event.__class__ is Match3StartGame:
            # в сложнотсти считаем все старты уровней
            df.loc[current_level, "Difficulty"] += 1

    def attempts():

        if report.current_event.__class__ is Match3CompleteTargets:
            # количество попыток пройти уровень
            if user_attempts[current_level] == 0:
                user_attempts[current_level] = 1
            level_attempts[current_level].append(user_attempts[current_level])

        elif report.current_event.__class__ is Match3FailGame:
            # Увеличиваем счетчик попыток
            user_attempts[current_level] += 1

    def clean_attempts():

        if report.current_event.__class__ is Match3CompleteTargets:
            if report.current_app_version >= report_app_version:
                if clean_start and report.current_event.ingame_bonuses == 0:
                    # количество чистых попыток пройти уровень
                    if user_clean_attempts[current_level] == 0:
                        user_clean_attempts[current_level] = 1
                    level_clean_attempts[current_level].append(user_clean_attempts[current_level])

        elif report.current_event.__class__ is Match3FailGame:
            if report.current_app_version >= report_app_version:
                if clean_start and report.current_event.ingame_bonuses == 0:
                    user_clean_attempts[current_level] += 1

    def purchases():
        if report.current_event.__class__ is Match3BuyPremiumCoin and report.current_event.status == "Success":
            df.loc[current_level, "Purchases"] += 1
            df.loc[current_level, "Purchases Sum"] += get_price(report.current_event.purchase, money="rub")

            # Считаем первые покупки игроков
            if first_purchase:
                df.loc[current_level, "First purchase"] += 1
                return False
        return first_purchase

    def dust():
        if report.current_event.__class__ is Match3FinishGame:

            # Добавляем собранную на уровне пыль
            collected_dust[current_level].append(int(report.current_event.game_currency_count))
            # Добавляем пыль на руках у игроков
            user_dust[current_level].append(report.current_user.game_coin)

    # Стартовые параметры
    level_attempts = dict.fromkeys(levels)
    level_clean_attempts = dict.fromkeys(levels)
    user_attempts = dict.fromkeys(levels, 0)
    user_clean_attempts = dict.fromkeys(levels, 0)
    collected_dust = dict.fromkeys(levels)
    user_dust = dict.fromkeys(levels)
    user_clean_start = dict.fromkeys(levels)
    for level in levels:
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

    while report.get_next_event():

        # Событие М3 - может смениться уровень
        if report.current_event.__class__ in (
                Match3BuyPremiumCoin, Match3CompleteTargets, Match3FinishGame, Match3StartGame, Match3FailGame):
            current_level = report.current_event.level_num

        # Если уровень из списка рассматрвиаемых
        if current_level in levels:
            # if report.get_timediff(measure="day")>=1 or report.is_new_user():
            # print(report.current_user.user_id, report.get_time_since_install(), report.get_time_since_last_enter(), report.current_user.entries[-1], report.is_new_user() )

            # Нвоый пользователь
            if (report.is_new_user() and not report.previous_user.is_skipped()) or (
                        report.get_time_since_install() > days_max):
                # print("flush",report.is_new_user(), (report.get_time_since_install() > days_max))
                # если вышло время, то работаем с текущим пользователем
                if report.is_new_user():
                    user = report.previous_user
                    user_str = "previous"
                else:
                    user = report.current_user
                    user_str = "current"

                for level in started_levels:
                    df.loc[level, "Started"] += 1
                for level in finished_levels:
                    df.loc[level, "Finished"] += 1

                # Проверка на отвал
                # При отсутствии максимального дня в игре (для среза выборки) берется макс дата из базы данных.
                if (not days_max and get_timediff(user.last_enter.date(), last_event_date,
                                                         measure="day") >= days_left) or \
                        (days_max and get_timediff(user.last_enter.date(),
                                                          user.install_date + timedelta(
                                                              days=days_max), measure="day") > days_left):
                    if started_levels:
                        for level in list(started_levels - finished_levels):
                            df.loc[level, left_par] += 1

                # сброс личных параметров
                started_levels = set()
                finished_levels = set()
                user_attempts = dict.fromkeys(levels, 0)
                user_clean_attempts = dict.fromkeys(levels, 0)
                first_purchase = True

                if not report.is_new_user() and report.get_time_since_install(user="current") > days_max:
                    report.skip_current_user()
                    continue

            start_finish()
            clean_start = clean_start_finish()
            difficulty()
            attempts()
            clean_attempts()
            first_purchase = purchases()
            dust()

    # Финальные рассчеты
    df["Start Convertion"] = round(df["Started"] * 100 / report.total_users, 1)
    df["Difficulty"] = round(100 - df["Finished"] * 100 / df["Difficulty"], 1)
    df["Clean Difficulty"] = round(100 - df["Clean Finish"] * 100 / df["Clean Start"], 1)
    df["ARPU"] = round(df["Purchases Sum"] / df["Started"], 1)
    for level in levels:
        # проверка на выбросы в попытках
        if len(level_attempts[level]) > 0:
            level_attempts[level] = outliers_iqr(level_attempts[level], level + " attempts", multiplier=10)
            df.loc[level, "Attempts"] = round(1 - 1 / (sum(level_attempts[level]) / len(level_attempts[level])),
                                              3) * 100

        if len(level_clean_attempts[level]) > 0:
            level_clean_attempts[level] = outliers_iqr(level_clean_attempts[level], level + " clean attempts",
                                                       multiplier=4)
            df.loc[level, "Clean Attempts"] = round(
                1 - 1 / (sum(level_clean_attempts[level]) / len(level_clean_attempts[level])),
                3) * 100
        # Проверка на выбросы в значениях пыли
        if len(collected_dust[level]) > 0:
            if len(collected_dust[level]) > 10:
                collected_dust[level] = outliers_iqr(collected_dust[level], level + " collected dust", multiplier=5)
            df.loc[level, "Dust"] = round(sum(collected_dust[level]) / float(len(collected_dust[level])), 1)

        if len(user_dust[level]) > 0:
            if len(user_dust[level]) > 10:
                user_dust[level] = outliers_iqr(data_list=user_dust[level], where=level + " user dust",
                                                max_outliers=False, min_outliers=True, multiplier=15)
                user_dust[level] = outliers_iqr(user_dust[level], level + " user dust", multiplier=5)
            df.loc[level, "Dust on hands"] = round(sum(user_dust[level]) / float(len(user_dust[level])), 1)

    # Печать
    print("Total users:", report.total_users)
    print("Testers:", len(report.testers))
    print(df.to_string())

    writer = pd.ExcelWriter(
        "Levels " + str(start) + "-" + str(start + quantity - 1) + " " + report_app_version + " " + str(
            days_max) + "days" + ".xlsx")
    df.to_excel(excel_writer=writer)
    writer.save()
    del report
