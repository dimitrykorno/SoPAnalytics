import pandas as pd
from sop_analytics.Utilities.Quests import get_last_locquest, loc_quest_level
import itertools
from sop_analytics.Classes.Events import *
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from report_api.Report import Report
from report_api.Utilities.Utils import time_count,check_arguments,try_save_writer,check_folder
import os
app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(game_point="0030",
               os_list=["iOS","Android"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    """
    Подробный разбор событий, предшествующих отвалу
    :param os_list:
    :param period_start:
    :param period_end:
    :param min_version:
    :param max_version:
    :param countries_list:
    :param game_point: Номер квеста или уровня
    :return:
    """
    errors = check_arguments(locals())
    result_files = []
    folder_dest = "Results/Подробный анализ уровня/"
    if hasattr(new_report,'user'):
        folder_dest+=str(new_report.user)+"/"
    check_folder(folder_dest)

    if errors:
        return errors, result_files

    # БАЗА ДАННЫХ
    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User, os=os_str, app=app, user_status_check=True)

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
                                            ("CityEvent", '{"Quest"%'),
                                            ("","%Match3Events%"),
                                            ("", '{"CityEvent":{"Quest":%')
                                            ])
        df = pd.DataFrame(index=[0],
                          columns=["Event", "Users", "Users %"])
        df.fillna(0, inplace=True)

        # ПАРАМЕТРЫ

        previous_quest = get_last_locquest(game_point)
        loc = previous_quest[:5]
        quest = previous_quest[5:]

        levels = loc_quest_level[loc][quest]
        orders = list(itertools.permutations(levels))

        user_events = []

        list_orders = {}
        for order in orders:
            list_orders[order] = 0

        in_area = False

        while Report.get_next_event():

            if Report.is_new_user():
                in_area = False
                if user_events:
                    user_orders = corresponding_orders(user_events)
                    if user_orders in orders:
                        list_orders[user_orders] += 1
                user_events = []

            if issubclass(Report.current_event.__class__, Match3Event) and in_area:
                user_events.append(Report.current_event.__class__.__name__ + " " + str(Report.current_event.level_num))
            else:

                if isinstance(Report.current_event, CityEventsQuest) and Report.current_event.quest == previous_quest:
                    if Report.current_event.action == "Take":
                        in_area = True
                    # \u0421omplete, ага, жесть
                    elif Report.current_event.action in ("Сomplete", "Complete"):
                        in_area = False
                if in_area:
                    user_events.append(Report.current_event.__class__.__name__)

        df = pd.DataFrame(index=orders, columns=["Users", "Users %"])
        for order in orders:
            df.at[order, "Users"] = list_orders[order]
        df["Users %"] = df["Users"] * 100 / Report.total_users
        # Вывод
        df.fillna("", inplace=True)
        #print(df.to_string())
        filename=folder_dest+"DetailedFunnel " + str(min_version) + " " + os_str + "+.xlsx"
        writer = pd.ExcelWriter(filename)
        df.to_excel(excel_writer=writer)
        try_save_writer(writer,filename)
        result_files.append(os.path.abspath(filename))
    return errors,result_files


def corresponding_orders(user_events):
    user_order = []
    for event in user_events:
        if "Match3FinishGame" in event:
            user_order.append(event[-4:])
    return tuple(user_order)
