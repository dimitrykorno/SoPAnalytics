from collections import OrderedDict
from matplotlib import pyplot as plt
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime
from Classes.Events import *
from report_api.Utilities.Utils import time_count

app = "sop"


@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None):
    for os_str in os_list:
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

        events = {}

        while Report.get_next_event():

            if Report.is_new_user():
                if Report.get_time_since_last_enter(user="previous", measure="day") > 14:
                    # Анализируется последние событие каждого игрока
                    last_event_class = Report.previous_event.__class__.__name__
                    # Оно добавляется в список последних событий
                    if last_event_class not in events.keys():
                        events[last_event_class] = 0
                    events[last_event_class] += 1

        ordered_events = OrderedDict(sorted(events.items(), key=lambda t: t[1]))

        # Рисовка гистограммы
        plt.figure(figsize=(15, 6))
        plt.barh(range(len(list(ordered_events.values()))), list(ordered_events.values()))
        plt.yticks(range(len(list(ordered_events.values()))), list(ordered_events.keys()))
        plt.savefig("Histograms/last_event_histo " + os_str + ".png")
        plt.show()
