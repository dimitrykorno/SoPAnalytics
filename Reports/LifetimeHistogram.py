from report_api.Utilities.Utils import time_count
import matplotlib.pyplot as plt
from report_api.Data import Data


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               max_days=100,
               app_versions=['5.1', '5.3']):
    '''
    Построение графиков Lifetime по одному/нескольким версиям одновременно
    :param max_days: максимальное кол-во дней на графике
    :param app_versions: версии приложения (вводить в виде '5.1', '5,3' )
    :return:
    '''

    plt.figure(figsize=(12, 8))
    plt.title("Отвалы")
    for os_str in os_list:
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
            lifetime_values, db = Data.get_data(sql=sql, by_row=False, name="Запрос lifetime.")
            # получаем массив tuple, делаем из них плоский массив
            lifetime_values = [item["lifetime_sec"] for item in lifetime_values]
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

            print("Average lifetime", os_str, app_version, ":", average_lifetime, "дней")
            plt.plot(range(len(lt)), lt, label=app_version)
            plt.savefig("Histograms/Отвалы по дням " + os_str + " " + app_version + ".png")
        plt.legend()
        # plt.show()
