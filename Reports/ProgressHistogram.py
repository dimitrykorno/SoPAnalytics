from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from sop_analytics.Classes.Events import *
from report_api.Report import Report
from report_api.Utilities.Utils import time_count, draw_subplot
from sop_analytics.Utilities.Quests import loc_quest_level, get_locquest

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument,PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               max_level=60,
               days=[0, 1, 2, 3, 4],
               app_version=["7.5"],
               period_start="2018-11-15",
               period_end="2018-11-18",
               countries_list=[],
               users_last_day=False):
    days = list(map(int, days))
    if not isinstance(app_version, list):
        app_version = list(app_version)
    progress_levels = {}
    progress_quests = {}
    users = dict.fromkeys(app_version, 0)
    # с 1 (0, чтобы точнее были деления) по n (включительно) + 3 финишера (15?)
    levels = list(range(0, max_level + 2))
    quests = []
    end = False
    for location in loc_quest_level:
        for quest in loc_quest_level[location]:
            if str(max_level).rjust(4, '0') not in loc_quest_level[location][quest]:
                quests.append(location + quest)
            else:
                quests.append(location + quest)
                end = True
                break
        if end:
            break

    for os_str in os_list:
        for version in app_version:
            # БАЗА ДАННЫХ
            Report.set_app_data(parser=Parse, user_class=User, event_class=Event,
                                os=os_str, app=app, user_status_check=False)

            Report.set_installs_data(additional_parameters=[],
                                     period_start=period_start,
                                     period_end=period_end,
                                     min_version=version,
                                     max_version=version,
                                     countries_list=countries_list)
            Report.set_events_data(additional_parameters=[],
                                   period_start=period_start,
                                   period_end=None,
                                   min_version=None,
                                   max_version=None,
                                   events_list=[("Match3Events",
                                                 ["%CompleteTargets%", "%StartGame%", "%FailGame%", "%FinishGame%"]),
                                                ("CityEvent", "%InitGameState"),
                                                ("",
                                                 ["%Match3Events%CompleteTargets%", "%Match3Events%StartGame%",
                                                  "%Match3Events%FailGame%", "%Match3Events%FinishGame%"]),
                                                ("", "%CityEvent%InitGameState%")])

            # ПАРАМЕТРЫ
            previous_day = None
            progress_levels[version] = {}
            progress_quests[version] = {}
            for day in days:
                progress_levels[version][str(day) + " day"] = []
                progress_quests[version][str(day) + " day"] = [0] * len(quests)
                for _ in levels:
                    progress_levels[version][str(day) + " day"].append([0, 0, 0])

            previous_m3_event = None if users_last_day else Match3StartGame(level_num="0001")
            last_updated_day = 0

            def add_event(event, d):
                level = int(event.level_num)
                if level < max_level:
                    if isinstance(event, Match3CompleteTargets) \
                            or isinstance(event, Match3FinishGame):
                        progress_levels[version][str(d) + " day"][level][2] += 1
                    elif isinstance(event, Match3StartGame):
                        quest = get_locquest(str(level).rjust(4, '0'))
                        progress_quests[version][str(d) + " day"][quests.index(quest)] += 1
                        progress_levels[version][str(d) + " day"][level][0] += 1
                    elif isinstance(event, Match3FailGame):
                        progress_levels[version][str(d) + " day"][level][1] += 1

            def add_user_progress():
                if not users_last_day:
                    for day in [d for d in range(last_updated_day, day_in_game) if d in days]:
                        add_event(previous_m3_event, day)

            def flush_user_info():
                if previous_day in days:
                        add_event(previous_m3_event, previous_day)
                if not users_last_day:
                    for day in [d for d in days if d > previous_day]:
                        add_event(previous_m3_event, day)

            while Report.get_next_event():
                day_in_game = Report.get_time_since_install(measure="day")

                # НЕ КАЖДОЕ СОБЫТИЕ А ТОЛЬКО КОГДА МЕНЯЕТСЯ ДЕНЬ,
                #  либо только когда меняется пользователь, если только для тех, у кого это последний день
                if Report.is_new_user():
                    if previous_m3_event:
                        flush_user_info()
                    previous_m3_event = None if users_last_day else Match3StartGame(level_num="0001")
                    last_updated_day = 0

                elif not users_last_day and previous_day is not None and day_in_game != previous_day:
                    add_user_progress()
                    last_updated_day = max(max([0] + [d for d in range(last_updated_day, day_in_game) if d in days]) + 1,last_updated_day)

                if issubclass(Report.current_event.__class__, Match3Event):
                    previous_m3_event = Report.current_event
                previous_day = day_in_game

            if previous_m3_event:
                flush_user_info()

            print("Version", version, "Total users:", Report.total_users)
            users[version] = Report.total_users
            for day in days:
                print("day:", day, progress_levels[version][str(day) + " day"])


        title = os_str+ " Гистограма прогресса " + str(period_start) + "-" + str(
            period_end)
        if users_last_day:
            title += " last day"
        for version in app_version:
            draw_subplot(levels, progress_levels[version], plot_type="bar", additional_labels=["Start", "Fail", "Finish"], show=True, colors=["y", "r", "g"], title=title+" "+version,
                  size=(2, 1), folder="Results/Гистограма прогресса/")
