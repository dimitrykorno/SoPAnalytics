from sop_analytics.Utilities.Quests import *
import pandas as pd
from sop_analytics.Classes.Events import *
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from report_api.Report import Report
from report_api.Utilities.Utils import time_count,check_arguments,check_folder,try_save_writer
import os
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
               quantity=200):
    errors = check_arguments(locals())
    result_files = []
    folder_dest = "Results/Использование бонусов/"
    if hasattr(new_report,'user'):
        folder_dest+=str(new_report.user)+"/"
    check_folder(folder_dest)

    if errors:
        return errors, result_files

    if start is None:
        start=1
    else:
        start=int(start)
    if quantity is None:
        quantity=200
    else:
        quantity=int(quantity)
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
                               events_list=[("Match3Events",)])

        hammer_price=63
        first_bonus_price=43
        second_bonus_price=53
        third_bonus_price=63
        steps_price=90
        levels = get_level_names(start, quantity)
        df = pd.DataFrame(index=levels,
                          columns=["Hammer", "First", "Second", "Third", "Buy steps","Spent"])
        df = df.fillna(0)

        # Параметры
        user_hammer = 3
        user_first = 3
        user_second = 3
        user_third = 3

        while Report.get_next_event():

            if Report.is_new_user():
                # Бесплатные бонусы
                user_hammer = 3
                user_first = 3
                user_second = 3
                user_third = 3

            current_level = Report.current_event.level_num
            if current_level in levels and current_level:
                if Report.current_event.__class__ is Match3StartGame:

                    # На 11 уровне дается первый бонус, он бесплатен при переигрывании
                    if current_level != "0011":
                        if user_first <= 0:
                            df.at[current_level, "First"] += int(Report.current_event.start_bonuses.first)
                        else:
                            user_first -= int(Report.current_event.start_bonuses.first)

                    # На 16 уровне дается второй бонус, он бесплатен при переигрывании
                    if current_level != "0016":
                        if user_second <= 0:
                            df.at[current_level, "Second"] += int(Report.current_event.start_bonuses.second)
                        else:
                            user_second -= int(Report.current_event.start_bonuses.second)

                    # На 19 уровне дается третий бонус, он бесплатен при переигрывании
                    if current_level != "0019":
                        if user_third <= 0:
                            df.at[current_level, "Third"] += int(Report.current_event.start_bonuses.third)
                        else:
                            user_third -= int(Report.current_event.start_bonuses.third)

                elif Report.current_event.__class__ is Match3CompleteTargets:
                    # На 7 уровне дается молоток, он бесплатен при переигрывании
                    if current_level != "0007":
                        if user_hammer <= 0:
                            df.at[current_level, "Hammer"] += Report.current_event.ingame_bonuses
                        else:
                            user_hammer -= Report.current_event.ingame_bonuses

                    # При завершении уровней на обучение бонусу отбирается 1 бонус при его использовании
                    if Report.previous_event.__class__ is Match3StartGame:
                        if Report.previous_event.level_num == "0011":
                            user_first -= int(Report.previous_event.start_bonuses.first)
                        elif Report.previous_event.level_num == "0016":
                            user_second -= int(Report.previous_event.start_bonuses.second)
                        elif Report.previous_event.level_num == "0019":
                            user_third -= int(Report.previous_event.start_bonuses.third)
                        elif Report.previous_event.level_num == "0007":
                            user_hammer -= Report.current_event.ingame_bonuses

                    if Report.previous_event.__class__ is Match3FailGame:
                        df.at[current_level, "Buy steps"] += 1

                # Докупка ходов
                elif Report.current_event.__class__ is Match3FailGame:
                    df.at[current_level, "Buy steps"] += Report.current_event.fail_count
        for level in levels:
            df.at[level,"Spent"]=df.at[level,"Hammer"]*hammer_price+df.at[level,"First"]*first_bonus_price+df.at[level,"Second"]*second_bonus_price+df.at[level,"Third"]*third_bonus_price+df.at[level,"Buy steps"]*steps_price
        # Вывод
        #print(df.to_string())
        filename=folder_dest+"Level spend coins " + str(start) + "-" + str(start + quantity - 1) + ".xlsx"
        writer = pd.ExcelWriter(filename)
        df.to_excel(excel_writer=writer)
        try_save_writer(writer,filename)
        result_files.append(os.path.abspath(filename))
    return errors,result_files
