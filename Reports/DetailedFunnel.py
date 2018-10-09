from report_api.Utilities.Utils import time_count
import pandas as pd
from Classes.Events import *
from Utilities.Quests import get_last_loc_quest, loc_quest_level
import itertools
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime

app = "sop"


# noinspection PyDefaultArgument
@time_count
def new_report(game_point="0030",
               os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None, ):
    """
    Подробный разбор событий, предшествующих отвалу
    :param game_point:
    :param os_list:
    :param period_start:
    :param period_end:
    :param min_version:
    :param max_version:
    :return:
    """

    # Приводим границы периода к виду datetime.date
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.strptime(period_end, "%Y-%m-%d").date()

    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, event_class=Event, user_class=User, os=os_str, app=app,
                            user_status_check=False)
        Report.set_installs_data(additional_parameters=None,
                                 period_start=period_start,
                                 period_end=period_end,
                                 min_version=min_version,
                                 max_version=max_version,
                                 countries_list=[])

        Report.set_events_data(additional_parameters=None,
                               period_start=period_start,
                               period_end=str(datetime.now().date()),
                               min_version=min_version,
                               max_version=None,
                               countries_list=[],
                               events_list=[])

        df = pd.DataFrame(index=[0],
                          columns=["Event", "Users", "Users %"])
        df.fillna(0, inplace=True)

        # ПАРАМЕТРЫ

        previous_quest = get_last_loc_quest(game_point)
        loc = previous_quest[:5]
        quest = previous_quest[5:]

        levels = loc_quest_level[loc][quest]
        orders = list(itertools.permutations(levels))

        user_orders = None
        user_events = []

        df_orders = {}
        list_orders = {}
        for order in orders:
            df_orders[order] = pd.DataFrame(
                columns=["Event", "Users", "Users %"])
            df_orders[order].fillna(0, inplace=True)

            list_orders[order] = []

        in_area = False

        while Report.get_next_event():

            if Report.is_new_user():
                in_area = False
                if user_events:
                    user_orders = corresponding_orders(user_events, orders)
                user_events = []

            if issubclass(Report.current_event.__class__, Match3Event) and in_area:
                user_events.append(Report.current_event.__class__.__name__ + " " + str(Report.current_event.level_num))
            else:

                if Report.current_event.__class__ is CityEventsQuest and Report.current_event.quest == previous_quest:
                    if Report.current_event.action == "Take":
                        in_area = True
                    # \u0421omplete, ага, жесть
                    elif Report.current_event.action in ("Сomplete", "Complete"):
                        in_area = False
                    else:
                        print(Report.current_event.action, Report.current_event.action.__class__)
                if in_area:
                    user_events.append(Report.current_event.__class__.__name__)

        # Вывод
        df.fillna("", inplace=True)
        print(df.to_string())
        writer = pd.ExcelWriter(
            "Detailed Level Loss/DetailedFunnel " + os_str + " " + game_point + " " + min_version + "+.xlsx")
        df.to_excel(excel_writer=writer)
        writer.save()


def corresponding_orders(user_events, orders):
    orders_list = orders.copy()
    user_order = []
    for event in user_events:
        if "Match3FinishGame" in event:
            user_order.append(event[-4:])

    print("Orders:", orders_list)
    print("user", user_order)
    for index, user_order in enumerate(user_order):
        orders_list = [order for order in orders_list if list(orders_list[index]) == user_order]
    print("result", orders_list)
