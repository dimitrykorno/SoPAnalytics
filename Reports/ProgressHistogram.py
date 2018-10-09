from report_api.Utilities.Utils import time_count
from matplotlib import pyplot as plt
import math
from itertools import chain
from Classes.Events import *
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(max_level=121,
               days=[2, 3],
               app_versions=["6.0", "6.3"],
               users_last_day=False,
               os_list=["iOS"],
               period_start=None,
               period_end=None, ):
    # Приводим границы периода к виду datetime.date
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.strptime(period_end, "%Y-%m-%d").date()

    # с 1 (0, чтобы точнее были деления) по n (включительно) + 3 финишера (15?)
    levels = list(range(0, max_level + 2))
    for os_str in os_list:
        days = list(map(int, days))
        progress = {}
        users = dict.fromkeys(app_versions, 0)
        for version in app_versions:
            # БАЗА ДАННЫХ

            Report.set_app_data(parser=Parse, event_class=Event, user_class=User, os=os_str, app=app,
                                user_status_check=False)

            Report.set_installs_data(additional_parameters=None,
                                     period_start=period_start,
                                     period_end=period_end,
                                     min_version=version,
                                     max_version=version,
                                     countries_list=[])

            Report.set_events_data(additional_parameters=None,
                                   period_start=period_start,
                                   period_end=str(datetime.now().date()),
                                   min_version=version,
                                   max_version=None,
                                   countries_list=[],
                                   events_list=[("Match3Events", ["%CompleteTargets%", "%FinishGame%"])])
            # ПАРАМЕТРЫ


            finished_levels = set()
            previous_day = None
            progress[version] = {}
            for day in days:
                progress[version][day] = [0] * len(levels)

            while Report.get_next_event():

                day_in_game = Report.get_time_since_install(measure="day")
                if Report.is_new_user() or (not users_last_day and (previous_day and day_in_game != previous_day)):
                    # НЕ КАЖДОЕ СОБЫТИЕ А ТОЛЬКО КОГДА МЕНЯЕТСЯ ДЕНЬ, либо только когда меняется пользователь, если только для тех, у кого это последний день
                    if previous_day in days and finished_levels:
                        max_user_level = int(max(finished_levels))

                        # учитываем финишеры
                        if max_user_level < 9000:
                            progress[version][previous_day][min(max_user_level, max_level)] += 1
                        else:
                            progress[version][previous_day][max_level + 1] += 1

                if Report.is_new_user():
                    finished_levels = set()
                    previous_day = None

                finished_levels.add(Report.current_event.level_num)
                previous_day = day_in_game
            print(os_str + " " + version, "Total users:", Report.total_users)
            users[version] = Report.total_users

        # Рисовка гистограммы
        max_on_screen = 4
        columns = min(2, len(days))
        # columns=2
        lines_wanted = 2
        plots_left = len(days)
        screens = int(math.ceil(plots_left / max_on_screen))
        for i in range(screens):

            lines = lines_wanted if plots_left >= max_on_screen else math.ceil(plots_left / columns)
            fig, axs = plt.subplots(lines, columns, figsize=(18, 8), facecolor='w', edgecolor='k')
            fig.subplots_adjust(hspace=.5, wspace=.2)
            if columns > 1:
                axs = axs.ravel()

            for subplot, day in enumerate(days[i * max_on_screen: min((i + 1) * max_on_screen, len(days))]):
                if columns > 1:
                    ax = axs[subplot]
                else:
                    ax = axs
                for version in app_versions:
                    ax.bar(levels, progress[version][day], alpha=0.5, label=version)
                    ax.legend()
                    ax.set_xticks(list(chain(range(0, max_level + 1, 10), [max_level + 2])))
                    ax.set_xticklabels(list(range(0, max_level + 1, 10)) + ["X"])
                    ax.set_title("day " + str(day))
            plt.savefig(
                "Histograms/progress_histo_absolute" + os_str + " " + str(app_versions) + " (" + str(i) + ").png")
            plt.show()

            plots_left -= columns * lines

            # Рисовка гистограммы
            max_on_screen = 4
            columns = min(2, len(days))
            # columns = 2
            lines_wanted = 2
            plots_left = len(days)
            screens = int(math.ceil(plots_left / max_on_screen))
            for i in range(screens):

                lines = lines_wanted if plots_left >= max_on_screen else math.ceil(plots_left / columns)
                fig, axs = plt.subplots(lines, columns, figsize=(18, 8), facecolor='w', edgecolor='k')
                fig.subplots_adjust(hspace=.5, wspace=.2)

                if columns > 1:
                    axs = axs.ravel()

                for subplot, day in enumerate(days[i * max_on_screen: min((i + 1) * max_on_screen, len(days))]):
                    if columns > 1:
                        ax = axs[subplot]
                    else:
                        ax = axs
                    for version in app_versions:
                        ax.bar(levels,
                               [round(user_count * 100 / users[version], 1) for user_count in progress[version][day]],
                               alpha=0.5, label=version)
                        ax.legend()
                        ax.set_xticks(list(chain(range(0, max_level + 1, 10), [max_level + 2])))
                        ax.set_xticklabels(list(range(0, max_level + 1, 10)) + ["X"])
                        ax.set_title("day " + str(day))
                plt.savefig("Histograms/progress_histo " + os_str + " " + str(app_versions) + " (" + str(i) + ").png")
                plt.show()

                plots_left -= columns * lines
