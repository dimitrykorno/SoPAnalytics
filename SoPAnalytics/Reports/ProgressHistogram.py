from Classes.Report import Report
from Utilities.Utils import time_count
from matplotlib import pyplot as plt
import itertools
import math
import numpy as np
from itertools import chain


@time_count
def new_report(max_level=121, days=[2, 3], min_app_version=["6.0","6.3"], exact=True, users_last_day=False):
    days = list(map(int, days))
    progress = {}
    users=dict.fromkeys(min_app_version,0)
    # с 1 (0, чтобы точнее были деления) по n (включительно) + 3 финишера (15?)
    levels = list(range(0, max_level + 2))
    for version in min_app_version:
        # БАЗА ДАННЫХ
        sql = """
            SELECT ios_ifa, ios_ifv, event_name, event_json, event_datetime, app_version_name
            FROM sop_events.events_ios
            where event_name = "Match3Events" and ( event_json like "%CompleteTargets%" or event_json like "%FinishGame%")
            order by ios_ifa, ios_ifv,  event_datetime
            """
        report = Report(sql_events=sql, min_app_version=version, exact=exact)

        # ПАРАМЕТРЫ


        finished_levels = set()
        previous_day = None
        progress[version]={}
        for day in days:
            progress[version][day] = [0] * len(levels)

        while report.get_next_event():

            day_in_game = report.get_time_since_install(measure="day")
            if report.is_new_user() or (not users_last_day and (previous_day and day_in_game != previous_day)):
                # НЕ КАЖДОЕ СОБЫТИЕ А ТОЛЬКО КОГДА МЕНЯЕТСЯ ДЕНЬ, либо только когда меняется пользователь, если только для тех, у кого это последний день
                if previous_day in days and finished_levels:
                    max_user_level = int(max(finished_levels))

                    # учитываем финишеры
                    if max_user_level < 9000:
                        progress[version][previous_day][min(max_user_level, max_level)] += 1
                    else:
                        progress[version][previous_day][max_level + 1] += 1

            if report.is_new_user():
                finished_levels = set()
                previous_day = None

            finished_levels.add(report.current_event.level_num)
            previous_day = day_in_game
        print(version,"Total users:", report.total_users)
        users[version]=report.total_users
        del report

    # Рисовка гистограммы
    max_on_screen = 4
    columns = min(2,len(days))
    #columns=2
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
            if columns>1:
                ax=axs[subplot]
            else:
                ax = axs
            for version in min_app_version:
                ax.bar(levels, progress[version][day], alpha=0.5, label=version)
                ax.legend()
                ax.set_xticks(list(chain(range(0, max_level + 1, 10), [max_level + 2])))
                ax.set_xticklabels(list(range(0, max_level + 1, 10)) + ["X"])
                ax.set_title("day " + str(day))
        plt.savefig("progress_histo_absolute" + str(min_app_version) + " (" + str(i) + ").png")
        plt.show()

        plots_left -= columns * lines

        # Рисовка гистограммы
        max_on_screen = 4
        columns = min(2,len(days))
        #columns = 2
        lines_wanted = 2
        plots_left = len(days)
        screens = int(math.ceil(plots_left / max_on_screen))
        for i in range(screens):

            lines = lines_wanted if plots_left >= max_on_screen else math.ceil(plots_left / columns)
            fig, axs = plt.subplots(lines, columns, figsize=(18, 8), facecolor='w', edgecolor='k')
            fig.subplots_adjust(hspace=.5, wspace=.2)

            if columns>1:
                axs = axs.ravel()

            for subplot, day in enumerate(days[i * max_on_screen: min((i + 1) * max_on_screen, len(days))]):
                if columns > 1:
                    ax = axs[subplot]
                else:
                    ax = axs
                for version in min_app_version:
                    ax.bar(levels, [round(user_count*100/users[version],1) for user_count in progress[version][day]], alpha=0.5, label=version)
                    ax.legend()
                    ax.set_xticks(list(chain(range(0, max_level + 1, 10), [max_level + 2])))
                    ax.set_xticklabels(list(range(0, max_level + 1, 10)) + ["X"])
                    ax.set_title("day " + str(day))
            plt.savefig("progress_histo " + str(min_app_version) + " (" + str(i) + ").png")
            plt.show()

            plots_left -= columns * lines

