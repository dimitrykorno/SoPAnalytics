from sop_analytics.Classes.Events import *
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from report_api.Report import Report
from datetime import date
from report_api.Utilities.Utils import time_count

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(short_info=True,
               first_session=False,
               user_status=True,
               detailed_events=list(),
               os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    # БАЗА ДАННЫХ
    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User, event_class=Event,
                            os=os_str, app=app, user_status_check=True)

        Report.set_installs_data(additional_parameters=[],
                                 period_start=period_start,
                                 period_end=period_end,
                                 min_version=min_version,
                                 max_version=max_version,
                                 countries_list=countries_list)
        Report.set_events_data(additional_parameters=[],
                               period_start=period_start,
                               period_end=None,
                               min_version=None,
                               max_version=None,
                               events_list=[])

        # ФАЙЛЫ ВЫВОДА
        output_file = None
        output_file_returned = None
        output_file_not_returned = None
        if not first_session:
            output_file = open("Results/Печать сессий/UserSessions.txt", "w")
        else:
            output_file_returned = open("Results/Печать сессий/UserSessions.txt", "w")
            output_file_not_returned = open("Results/Печать сессий/UserSessions.txt", "w")

        # ПАРАМЕТРЫ
        returned_user = False
        output_string = ""
        events_string = ""
        first_session_status = ""

        while Report.get_next_event():

            # НОВЫЙ ПОЛЬЗОВАТЕЛЬ
            if Report.is_new_user():

                # Создаем текст сессий на вывод
                output_string += "\n\nNew user: " + str(Report.previous_user.user_id) + "\n"
                output_string += events_string
                if user_status:
                    if first_session:
                        output_string += first_session_status
                    else:
                        output_string += Report.previous_user.get_status()

                # Вывод в файлы
                if Report.previous_user.install_date >= date(2018, 6, 25):
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
                if Report.get_time_since_install("day") > 0:
                    returned_user = True

                # Первая ли сессия
                if Report.current_user.first_session:
                    first_session_status = Report.current_user.get_status()

            # Добавление текста события
            if (first_session and Report.current_user.first_session) or not first_session:
                if Report.current_event.__class__ is CityEventsInitGameState:
                    events_string += "---\n"
                if short_info and (
                            not detailed_events or detailed_events and Report.current_event.__class__.__name__
                        not in detailed_events):
                    events_string += str(
                        Report.current_event.datetime) + " " + Report.current_event.to_short_string() + "\n"
                else:
                    events_string += str(Report.current_event.datetime) + " " + Report.current_event.to_string() + "\n"
