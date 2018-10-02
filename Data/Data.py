import MySQLdb
from Utilities.Utils import time_count
from datetime import datetime, timedelta
from Classes.OS import OS


@time_count
def get_data(sql, query_result="by_row", name=""):
    print("Запрос к базе данных. " + name)
    db = MySQLdb.connect(host="localhost", user="root", passwd="0000", db="sop_events", charset='utf8')

    db.query(sql)

    if query_result == "by_row":
        result = db.use_result()
    else:
        result = db.store_result()

    if result:
        return result, db
    else:
        print("Ничего не найдено.")


def get_last_event_date(os):
    result, db = get_data(
        """
        SELECT MAX(event_datetime) as last_event
        FROM sop_events.events_{}
        """.format(OS.get_os_string(os))
        , name="Последнее событие.")
    event_data = result.fetch_row(maxrows=1, how=1)[0]
    db.close()
    last_event_date = event_data["last_event"].date()
    print(OS.get_os_string(os) + "Последнее событие в БД:", last_event_date)
    return last_event_date


def get_installs_list(os=OS.ios,
                      period_start=datetime.strptime("2018-06-14", "%Y-%m-%d").date(),
                      period_end=str(datetime.now().date()),
                      min_version=None,
                      max_version=None,
                      parameters=["publisher_name", "tracker_name", "install_datetime", "country_iso_code"]):
    """
    Получение данных об установках с заданными параметрами
    TO DO добавить отсев по версии и источнику
    :param os:
    :param period_start:
    :param period_end:
    :param parameters:
    :return:
    """
    user_id1 = OS.get_aid(os)
    user_id2 = OS.get_id(os)
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.strptime(period_end, "%Y-%m-%d").date()
    period_end += timedelta(days=1)

    parameters = (
        set(parameters) | {user_id1, user_id2, "install_datetime", "publisher_name", "tracker_name", "app_version_name",
                           "country_iso_code"})
    parameters = list(parameters)
    min_version = "and app_version_name >= " + str(min_version) if min_version else ""
    max_version = "and app_version_name <= " + str(max_version) if max_version else ""
    sql = """
    select {} 
    from sop_events.installs_{}
    where 
    install_datetime between '{}' and '{}'
    {} {}
    """.format(','.join(parameters), OS.get_os_string(os), period_start,
               period_end, min_version, max_version)
    # print(sql)
    data, db = get_data(sql=sql, name="Загрузка установок.")

    installs = []

    installs_data = data.fetch_row(how=1, maxrows=1)
    if installs_data:
        fetched_install_data = installs_data[0]
        while installs_data:
            install = dict.fromkeys(parameters)
            for param in parameters:
                install[param] = fetched_install_data[param]
            installs.append(install)

            installs_data = data.fetch_row(how=1, maxrows=1)
            if installs_data:
                fetched_install_data = installs_data[0]
    else:
        print("Установки не найдены.")
        print(sql)
    db.close()
    return installs
