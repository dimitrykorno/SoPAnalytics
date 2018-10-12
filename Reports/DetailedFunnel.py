from Classes.Report import Report
from Utilities.Utils import time_count
import pandas as pd
from Classes.Events import *
from Utilities.Quests import get_last_loc_quest, loc_quest_level
import itertools


@time_count
def new_report(game_point="0030", min_app_version="5.3", exact=True):
    '''
    Подробный разбор событий, предшествующих отвалу
    :param game_point: Номер квеста или уровня
    :param min_app_version: мин версия приложения
    :param exact: должна ли версия приложения обязательно совпадать с минимальной
    :return:
    '''
    # БАЗА ДАННЫХ
    sql = """
        SELECT ios_ifa, ios_ifv, event_name, event_json, event_datetime, app_version_name
        FROM sop_events.events_ios
        order by ios_ifa, ios_ifv,  event_datetime
        """
    report = Report(sql_events=sql, min_app_version=min_app_version, exact=exact)

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

    while report.get_next_event():

        if report.is_new_user():
            in_area = False
            if user_events:
                user_orders = corresponding_orders(user_events, orders)
            user_events = []

        if issubclass(report.current_event.__class__, Match3Event) and in_area:
            user_events.append(report.current_event.__class__.__name__ + " " + str(report.current_event.level_num))
        else:

            if report.current_event.__class__ is CityEventsQuest and report.current_event.quest_id == previous_quest:
                print(report.current_event.to_string())
                if report.current_event.action == "Take":
                    in_area = True
                # \u0421omplete, ага, жесть
                elif report.current_event.action in("Сomplete","Complete"):
                    in_area = False
                else:
                    print(report.current_event.action,report.current_event.action.__class__)
            if in_area:
                user_events.append(report.current_event.__class__.__name__)

    # Вывод
    df.fillna("", inplace=True)
    print(df.to_string())
    writer = pd.ExcelWriter("DetailedFunnel " + min_app_version + "+.xlsx")
    df.to_excel(excel_writer=writer)
    writer.save()


def corresponding_orders(user_events, orders):
    orders_list = orders.copy()
    user_order = []
    for event in user_events:
        if "Match3FinishGame" in event:
            print(event)
            user_order.append(event[-4:])
            print(user_order)

    print("Orders:", orders_list)
    print("user", user_order)
    for index, user_order in enumerate(user_order):
        orders_list = [order for order in orders_list if order[index] == user_order]
    print("result", orders_list)
