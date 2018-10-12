from Classes.Report import Report
from collections import OrderedDict
from matplotlib import pyplot as plt


def new_report(min_app_version="5.1"):
    sql = """
    select ios_ifa, ios_ifv, event_name, event_json, event_datetime, app_version_name
    from sop_events.events_ios
    order by ios_ifa, ios_ifv, event_datetime
    """
    report = Report(sql_events=sql, min_app_version=min_app_version)
    events = {}

    while report.get_next_event():

        if report.is_new_user():
            # Анализируется последние событие каждого игрока
            last_event_class = report.previous_event.__class__.__name__
            # Оно добавляется в список последних событий
            if last_event_class not in events.keys():
                events[last_event_class] = 0
            events[last_event_class] += 1

    ordered_events = OrderedDict(sorted(events.items(), key=lambda t: t[1]))

    # Рисовка гистограммы
    plt.figure(figsize=(15, 6))
    plt.barh(range(len(list(ordered_events.values()))), list(ordered_events.values()))
    plt.yticks(range(len(list(ordered_events.values()))), list(ordered_events.keys()))
    plt.savefig("last_event_histo.png")
    plt.show()
