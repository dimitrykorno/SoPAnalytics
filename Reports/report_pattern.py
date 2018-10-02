from Classes.Report import Report
from Utilities.Utils import time_count
import pandas as pd
from datetime import datetime, timedelta
from Classes.OS import OS
import matplotlib.pyplot as plt



@time_count
def new_report(os=OS.ios,period_start=datetime.strptime("2018-08-20", "%Y-%m-%d").date(), period_end=str(datetime.now().date()),
               days_since_install=28,
               min_app_version="4.7", exact=False):
    """
    Расчет накопительного ARPU и ROI по паблишерам и трекинговым ссылкам(источникам)
    :param period_start: начало периода
    :param period_end: конец периода
    :param days_since_install: рассчитное кол-во дней после установки
    :param min_app_version: мин версия приложения
    :param exact: точное соответствие версии приложения
    :return:
    """
    # Приводим границы периода к виду datetime.date
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.strptime(period_end, "%Y-%m-%d").date()

    # БАЗА ДАННЫХ
    sql = """
        SELECT ios_ifa, ios_ifv, event_name, event_json, event_datetime, app_version_name
        FROM sop_events.events_ios
        
        and
        (ios_ifv<>"" or ios_ifa <>"")
        order by ios_ifa, ios_ifv,  event_datetime
        """
    report = Report(sql_events=sql,min_app_version=min_app_version,exact=exact,get_installs=False)



    # ПАРАМЕТРЫ
    parameters = []
    # Запись пользовательских данных в общие
    def flush_user_data():

    while report.get_next_event():

        if report.is_new_user():
            pass


    flush_user_data()

    df = pd.DataFrame(index=[0],
                      columns=[])
    df.fillna(0, inplace=True)

    # Вывод
    df.fillna("", inplace=True)
    print(df.to_string())
    writer = pd.ExcelWriter(" " + ".xlsx")
    df.to_excel(excel_writer=writer)
    writer.save()