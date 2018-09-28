from Utilities.Quests import *
from Utilities.Utils import *
import pandas as pd
from Classes.Events import *
from Classes.Report import Report


@time_count
def new_report(start=1, quantity=121, min_app_version="5.3",exact=True):
    sql = """
    SELECT ios_ifa,ios_ifv, event_name, event_json, event_datetime, app_version_name
    FROM sop_events.events_ios
    WHERE event_name = "Match3Events" 
    order by ios_ifa,ios_ifv, event_datetime
    """

    report = Report(sql_events=sql, min_app_version=min_app_version, exact=exact)

    levels = get_level_names(start, quantity)
    df = pd.DataFrame(index=levels,
                      columns=["Hammer", "First", "Second", "Third", "Buy steps"])
    df = df.fillna(0)

    # Параметры
    user_hammer = 3
    user_first = 3
    user_second = 3
    user_third = 3

    while report.get_next_event():

        if report.is_new_user():
            # Бесплатные бонусы
            user_hammer = 3
            user_first = 3
            user_second = 3
            user_third = 3

        current_level = report.current_event.level_num
        if current_level in levels and current_level:
            if report.current_event.__class__ is Match3StartGame:

                # На 11 уровне дается первый бонус, он бесплатен при переигрывании
                if current_level != "0011":
                    if user_first <= 0:
                        df.loc[current_level, "First"] += int(report.current_event.start_bonuses.first)
                    else:
                        user_first -= int(report.current_event.start_bonuses.first)

                # На 16 уровне дается второй бонус, он бесплатен при переигрывании
                if current_level != "0016":
                    if user_second <= 0:
                        df.loc[current_level, "Second"] += int(report.current_event.start_bonuses.second)
                    else:
                        user_second -= int(report.current_event.start_bonuses.second)

                # На 19 уровне дается третий бонус, он бесплатен при переигрывании
                if current_level != "0019":
                    if user_third <= 0:
                        df.loc[current_level, "Third"] += int(report.current_event.start_bonuses.third)
                    else:
                        user_third -= int(report.current_event.start_bonuses.third)

            elif report.current_event.__class__ is Match3CompleteTargets:
                # На 7 уровне дается молоток, он бесплатен при переигрывании
                if current_level != "0007":
                    if user_hammer <= 0:
                        df.loc[current_level, "Hammer"] += report.current_event.ingame_bonuses
                    else:
                        user_hammer -= report.current_event.ingame_bonuses

                # При завершении уровней на обучение бонусу отбирается 1 бонус при его использовании
                if report.previous_event.__class__ is Match3StartGame:
                    if report.previous_event.level_num == "0011":
                        user_first -= int(report.previous_event.start_bonuses.first)
                    elif report.previous_event.level_num == "0016":
                        user_second -= int(report.previous_event.start_bonuses.second)
                    elif report.previous_event.level_num == "0019":
                        user_third -= int(report.previous_event.start_bonuses.third)
                    elif report.previous_event.level_num == "0007":
                        user_hammer -= report.current_event.ingame_bonuses

                if report.previous_event.__class__ is Match3FailGame:
                    df.loc[current_level, "Buy steps"] += 1

            # Докупка ходов
            elif report.current_event.__class__ is Match3FailGame:
                df.loc[current_level, "Buy steps"] += report.current_event.fail_count

    # Вывод
    print(df.to_string())
    writer = pd.ExcelWriter("Level spend coins " + str(start) + "-" + str(start + quantity - 1) + ".xlsx")
    df.to_excel(excel_writer=writer)
    writer.save()
