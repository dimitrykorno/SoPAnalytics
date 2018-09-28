from Data import Data, Parse
import pandas as pd
from Classes.Events import *
import datetime
from Utilities.Utils import *
import matplotlib.pyplot as plt


@time_count
def new_report(max_days=100, app_versions=['5.1', '5.3']):
    '''
    Построение графиков Lifetime по одному/нескольким версиям одновременно
    :param max_days: максимальное кол-во дней на графике
    :param app_versions: версии приложения (вводить в виде '5.1', '5,3' )
    :return:
    '''
    plt.figure(figsize=(12, 8))
    plt.title("Отвалы")
    for app_version in app_versions:
        # Пользователи, у которых первое событие с нужной версией приложения
        sql = """
        select (MAX(event_timestamp)-MIN(event_timestamp)) as lifetime_sec
        from sop_events.events_ios
        where ios_ifa in (select ios_ifa
                            from sop_events.events_ios
                            where ios_ifa<>""
                            group by ios_ifa, app_version_name
                            having MIN(app_version_name)={})
        group by ios_ifa
        """.format(app_version)
        data, db = Data.get_data(sql=sql, query_result="all")
        lifetime_values = data.fetch_row(how=0, maxrows=0)
        # получаем массив tuple, делаем из них плоский массив
        lifetime_values = [item for tuple in lifetime_values for item in tuple]
        db.close()

        lt = [0] * max_days

        # Формируем распределение лайфтаймов по дням
        for lifetime in lifetime_values:
            lifetime = round(lifetime / (60 * 60 * 24), 1)
            if int(lifetime) < max_days:
                lt[int(lifetime)] += 1
        average_lifetime = int((sum(lifetime_values) / len(lifetime_values)) / (60 * 60 * 24))

        # удаляем хвосты
        while lt[-1] == 0:
            lt.pop()

        print("Average lifetime", app_version, ":", average_lifetime, "дней")
        plt.plot(range(len(lt)), lt, label=app_version)
        plt.savefig("Отвалы по дням " + app_version + ".png")
    plt.legend()
    plt.show()
