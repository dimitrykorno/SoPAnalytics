from Classes.Report import Report
from Classes.Events import CityEventsInitGameState
from Utilities.Utils import time_count, test_devices_ios
import datetime
import os

@time_count
def new_report(short_info=True, first_session=False, user_status=True, detailed_events=list(), install_app_version="5.5", exact_app_version=True):

    # БАЗА ДАННЫХ
    sql = """
        SELECT ios_ifa, ios_ifv, event_name, event_json, event_datetime, app_version_name
        FROM sop_events.events_ios
        order by ios_ifa, ios_ifv, event_datetime
        """

    report = Report(sql, user_status_check=True, min_app_version=install_app_version, exact=exact_app_version)

    # ФАЙЛЫ ВЫВОДА
    output_file = None
    output_file_returned = None
    output_file_not_returned = None
    if not first_session:
        output_file = open("UserSessions.txt", "w")
    else:
        output_file_returned = open("UserSessions.txt", "w")
        output_file_not_returned = open("UserSessions.txt", "w")


    # ПАРАМЕТРЫ
    skip_user_events = None
    returned_user = False
    output_string = ""
    events_string = ""
    first_session_status = ""

    while report.get_next_event():

        # НОВЫЙ ПОЛЬЗОВАТЕЛЬ
        if report.is_new_user():

            # Создаем текст сессий на вывод
            output_string += "\n\nNew user: " + str(report.previous_user.user_id) + "\n"
            if report.previous_user.user_id in test_devices_ios:
                output_string+="TESTER\n"
            output_string += events_string
            if user_status:
                if first_session:
                    output_string += first_session_status
                else:
                    output_string += report.previous_user.get_status()

            # Вывод в файлы
            if report.previous_user.first_enter.date() >= datetime.date(2018, 6, 25):
                if not first_session:
                    output_file.write(output_string)
                elif first_session and returned_user:
                    output_file_returned.write(output_string)
                elif first_session and not returned_user:
                    output_file_not_returned.write(output_string)

            # Обнуление параметров
            returned_user = False
            output_string = ""
            events_string = ""
            first_session_status = ""

        # ПЕРВЫЕ СЕССИИ
        if first_session:

            # Вернулся ли пользователь
            if report.get_time_since_install("day") > 0:
                returned_user = True

            # Первая ли сессия
            if report.current_user.first_session:
                first_session_status = report.current_user.get_status()

        # Добавление текста события
        if (first_session and report.current_user.first_session) or not first_session:
            if report.current_event.__class__ is CityEventsInitGameState:
                events_string += "---\n"
            if short_info and (not detailed_events or detailed_events and report.current_event.__class__.__name__  not in detailed_events):
                events_string += str(report.current_event.datetime) + " " + report.current_event.to_short_string() + "\n"
            else:
                events_string += str(report.current_event.datetime) + " " + report.current_event.to_string() + "\n"
