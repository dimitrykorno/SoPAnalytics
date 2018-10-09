from datetime import datetime
import pandas as pd
from report_api.Utilities.Utils import time_count
from report_api.Report import Report
from report_api.OS import OS
from Classes.Events import Event
from Classes.User import User
from Data import Parse
app="sop"

@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    # Приводим границы периода к виду datetime.date
    if isinstance(period_start, str):
        period_start = datetime.datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.datetime.strptime(period_end, "%Y-%m-%d").date()

    # БАЗА ДАННЫХ
    for os_str in os_list:
        os = OS.get_os(os_str)

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

    # ПАРАМЕТРЫ
    parameters = {}

    # Запись пользовательских данных в общие
    def flush_user_data():
        pass

    while Report.get_next_event():

        if Report.is_new_user():
            flush_user_data()

    flush_user_data()

    df = pd.DataFrame(index=[],
                      columns=[])
    df.fillna(0, inplace=True)

    # Вывод
    print(df.to_string())
    writer = pd.ExcelWriter("/ " +os_str + ".xlsx")

    df.to_excel(excel_writer=writer)
    writer.save()
