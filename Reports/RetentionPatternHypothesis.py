import pandas as pd
from Classes.PatternPresets import *
from Classes.Events import *
from report_api.OS import OS
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime
from report_api.Utilities.Utils import time_count

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(patt="ВНИМАНИЕ! ЗАДАЙТЕ ПАТТЕРНЫ ВРУЧНУЮ.",
               os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[],
               days_since_install=28,
               min_quest=None,
               classic_retention=True):
    """
    Расчет накопительного ARPU и ROI по паблишерам и трекинговым ссылкам(источникам)
    :param patt:
    :param os_list:
    :param min_version:
    :param max_version:
    :param countries_list:
    :param min_quest:
    :param classic_retention:
    :param period_start: начало периода
    :param period_end: конец периода
    :param days_since_install: рассчитное кол-во дней после установки
    :return:
    """

    # БАЗА ДАННЫХ

    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User, event_class=Event,
                            os=os_str, app=app, user_status_check=False)

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
                               events_list=[("CityEvent", ['{"Quest%', "%BuyDecoration%",
                                                           "%InitGameState%", "%BuyHealth%",
                                                           "%BuyPremiumCoin%Success%"]),
                                            ("Match3Events", ["%BuyPremiumCoinM3%Success%",
                                                              "%CompleteTargets%",
                                                              "%FailGame%"])])
        # ПАТТЕРНЫ
        # ВАЖНО! МНОЖЕСТВА ПОЛЬЗОВАТЕЛЕЙ, ПОДХОДЯЩИХ ПОД ПАТТЕРНЫ НЕ ДОЛЖНЫ ПЕРЕСЕКАТЬСЯ! (есть вывод по пропущенным)
        '''
        patterns_list = [
            pattern_BuyDecoration(completed_once=False, min_completions=2),
            pattern_BuyDecoration(completed_once=True),
            pattern_BuyDecoration(completed_once=False, max_completions=0, same_day_pattern=False)
        ]
        ''''''
        patterns_list = [
            pattern_BuyHealth(completed_once=False, min_completions=2),
            pattern_BuyHealth(completed_once=True),
            pattern_BuyHealth(completed_once=False, max_completions=0, same_day_pattern=False)
        ]
        '''
        patterns_list = [
            PatternWinRow(completed_once=False, min_completions=2, same_session_pattern=True),
            PatternWinRow(completed_once=True, same_session_pattern=True),
            PatternWinRow(completed_once=False, max_completions=0, same_day_pattern=True, same_session_pattern=False)
        ]
        # ПАРАМЕТРЫ
        parameters = ["Retention Period", "Pattern", "Users"]
        accumulating_parameters = [str(i) + "d" for i in range(0, days_since_install + 1)]
        parameters += accumulating_parameters
        # ПЕРИОДЫ РЕТЕНШЕНА
        retention_periods = ["0", "1-2", "3-6", "7-13", "14-27", "28+", "Never"]
        pattern_analysis = {}
        for retention_period in retention_periods:
            pattern_analysis[retention_period] = {}
            for pattern_name in [pattern.name for pattern in patterns_list]:
                pattern_analysis[retention_period][pattern_name] = dict.fromkeys(["Users"] + accumulating_parameters, 0)

        # функции ретеншена
        def get_retention_period(d):
            if d == 0:
                return "0"
            elif d < 3:
                return "1-2"
            elif d < 7:
                return "3-6"
            elif d < 14:
                return "7-13"
            elif d < 28:
                return "14-27"
            else:
                return "28+"

        def get_max_retention_day(user_entries_list, classic_ret=classic_retention):
            if classic_ret:
                for i in range(1, len(user_entries_list)):
                    if user_entries_list[i] == 0:
                        return i - 1
            else:
                for i in range(len(user_entries_list) - 1, -1, -1):
                    if user_entries_list[i] > 0:
                        return i

        def make_rolling_retention(user_entries_list):
            for i in range(len(user_entries_list) - 1, 0, -1):
                if user_entries_list[i - 1] < user_entries_list[i]:
                    user_entries_list[i - 1] = user_entries_list[i]
            return user_entries_list

        # Пользовательские параметры
        user_session_events = []
        user_day_events = []
        previous_day_in_game = 0
        if min_quest:
            min_quest = CityEventsQuest(quest_id=min_quest, action="Take", datetime=None)
        user_retention = [0] * (days_since_install + 1)
        user_events = {}
        for i in range(0, (days_since_install + 1)):
            user_events[i] = []

        # Запись пользовательских данных в общие
        def flush_user_data():
            user_found_pattern = False
            # проверяем каждый паттерн
            for patt in patterns_list:
                # постепенно собираем данные в один массив для паттерном,
                #  которые рассматриваются на всех событиях в куче
                user_accumulating_events = []
                # выполнение паттерна на отрезке ретеншена
                user_pattern_completion = dict.fromkeys(retention_periods, 0)
                # по каждому дню лайфтайма
                for d in range(0, days_since_install + 1):
                    user_day_accumulated_events = []
                    for session_events in user_events[d]:
                        # паттерн по каждой сессии
                        if patt.same_day_pattern and patt.same_session_pattern:
                            user_pattern_completion[get_retention_period(d)] += int(
                                patt.is_followed(session_events))
                        user_day_accumulated_events += session_events
                        user_accumulating_events += session_events
                    # паттер по дыннм с одного дня
                    if patt.same_day_pattern and not patt.same_session_pattern:
                        user_pattern_completion[get_retention_period(d)] += int(
                            patt.is_followed(user_day_accumulated_events))
                    # паттерн по всем данным всех дней
                    if not patt.same_day_pattern:
                        user_pattern_completion[get_retention_period(d)] += int(
                            patt.is_followed(user_accumulating_events))

                # суммарное выполнение паттерна
                overall_pattern_completions = 0
                # окончательный период выполнения паттерна
                final_completion_period = None
                for period in retention_periods:
                    # если паттерн на совершение события, то берем первый период его выполнения
                    if not final_completion_period and \
                                    user_pattern_completion[period] > 0 and \
                            (patt.max_completions is not None and patt.max_completions > 0
                             or patt.max_completions is None):
                        final_completion_period = period
                    overall_pattern_completions += user_pattern_completion[period]
                # если паттерн выполнен меньше минимума или больше максимума раз - выходим, не подходит
                if (patt.max_completions and patt.max_completions < overall_pattern_completions) \
                        or patt.min_completions > overall_pattern_completions:
                    continue
                # паттерн на не выполнения события
                if not final_completion_period and patt.max_completions == 0 and overall_pattern_completions == 0:
                    final_completion_period = "Never"

                # если выбрали подходящий период,
                # добавляем в общие данные показатели ретеншена и увеличиваем кол-во юзеров
                if final_completion_period:
                    for i in range(0, get_max_retention_day(user_retention) + 1):
                        pattern_analysis[final_completion_period][patt.name][str(i) + "d"] += user_retention[i]
                    pattern_analysis[final_completion_period][patt.name]["Users"] += 1
                    user_found_pattern = True
            if not user_found_pattern:
                Pattern.users_not_covered_with_pattern.add(Report.previous_user.user_id)

        # ЦИКЛ ОБРАБОТКИ ДАННЫХ
        while Report.get_next_event():

            if Report.is_new_user():
                if not classic_retention:
                    user_retention = make_rolling_retention(user_retention)
                user_day_events.append(user_session_events)
                user_events[day_in_game] = user_day_events
                flush_user_data()
                user_day_events = []
                user_session_events = []
                previous_day_in_game = 0
                user_retention = [0] * (days_since_install + 1)
                for day in range(0, days_since_install + 1):
                    user_events[day] = []

            # определяем день в игре и увеличиваем ртеншен
            day_in_game = Report.get_time_since_install("d")
            if day_in_game >= len(user_retention):
                Report.skip_current_user()
                continue
            user_retention[day_in_game] = 1
            if isinstance(Report.current_event, CityEventsQuest) and min_quest:
                if CityEventsQuest.compare_quests(Report.current_event.quest, min_quest) == -1:
                    continue
            # если новая сессия, добавляем список событий сессии в общие события игрока
            if isinstance(Report.current_event, CityEventsInitGameState):
                user_day_events.append(user_session_events)
                # если новый день, добавляем данные по дню в общие данные
                if day_in_game != previous_day_in_game:
                    user_events[previous_day_in_game] = user_day_events
                    previous_day_in_game = day_in_game
                    user_day_events = []
                user_session_events = []
            user_session_events.append(Report.current_event)
        flush_user_data()

        print("Инсталлов:", Report.total_users)
        print("Не прошли по паттернам:", len(Pattern.users_not_covered_with_pattern))

        df = pd.DataFrame(index=[],
                          columns=parameters)

        for retention_period in pattern_analysis.keys():
            for pattern in pattern_analysis[retention_period].keys():
                if pattern_analysis[retention_period][pattern]["Users"] > 0:
                    for i in range(0, days_since_install + 1):
                        pattern_analysis[retention_period][pattern][str(i) + "d"] = str(round(
                            pattern_analysis[retention_period][pattern][str(i) + "d"] * 100 /
                            pattern_analysis[retention_period][pattern]["Users"], 1)) + "%"

                    df = df.append({
                        "Retention Period": retention_period,
                        "Pattern": pattern,
                        **pattern_analysis[retention_period][pattern]},
                        ignore_index=True
                    )
        df.fillna(0, inplace=True)
        df.sort_values(by=["Retention Period", "Pattern"], ascending=True, inplace=True)
        # Вывод
        print(df.to_string(index=False))
        string = "ClassicRetention" if classic_retention else "RollingRetention"
        writer = pd.ExcelWriter(
            "Results/Паттерны/" + Pattern.filename + " " + string + " " + os_str + ".xlsx")
        df.to_excel(excel_writer=writer, index=False)
        writer.save()
