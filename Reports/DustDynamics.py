from Utilities.Utils import time_count, outliers_iqr
import pandas as pd
from Utilities.Quests import get_locquests_list, get_locquest, get_next_locquest
from matplotlib import pyplot as plt
from Classes.Events import *
from Data import Parse
from Classes.User import User
from report_api.Report import Report

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    def array_average(array, exclude_outliers=True, multiplier=5.0, name=None):
        if exclude_outliers:
            array = outliers_iqr(array, multiplier=multiplier, where=name, adaptive=True)
        avg = 0
        if not array:
            return 0
        if min(array) == max(array):
            avg = min(array)
        else:
            for element in array:
                avg += element / len(array)
        return int(avg)

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
                               events_list=[("CityEvent", ["%BuyPremiumCoin%Success%", "%InitGameState%",
                                                           "%BuyDust%", "%UpdateBuilding%",
                                                           "%BuyDecoration%", "%Quest%",
                                                           "%StartGame%", "%Button%Dust%",
                                                           "%Button%Quest%", "%InitGameState%",
                                                           "%Restore%"]),
                                            ("Match3Events", "%FinishGame%")])
        df = pd.DataFrame(index=[0],
                          columns=[])
        df.fillna(0, inplace=True)

        # ПАРАМЕТРЫ
        parameters = ["Дошли до квеста", "Потратили пыль", "Собрано пыли", "Куплено пыли", "Потрачено пыли",
                      "Средняя пыль на руках (не плат)", "Средняя пыль на руках (плат)", "Собрано пыли в среднем",
                      "Средняя трата пыли", "Популярные объекты"]
        quests_list = get_locquests_list()
        df = pd.DataFrame(index=quests_list, columns=parameters)
        # df.fillna(0, inplace=True)

        # buy_decor и restore отвечают за факт покупки декорации/восстановления мусора в предыдущих событиях,
        #  которые не были обработаны. после следующего обновления количества валюты, они будут обнулены.
        # в дальнейшнем систему нужно поменять, т.к. должны отправляться стоимости после покупки
        # и не нужно будет ждать обновления баланса валюты
        current_quest = None
        previous_quest = None
        buy_decor = False
        coins_decor = 0
        buy_decor_quest = None
        restore = False
        coins_restore = 0
        restore_quest = None

        # Пользовательские параметры
        quests = {}
        user_started_quests = set()
        user_spent_on_quest = dict.fromkeys(quests_list, 0)
        user_restore_on_quest = dict.fromkeys(quests_list, 0)
        user_spends_dust = False
        user_got_dust_on_quest = 0
        user_dust_on_hands = dict.fromkeys(quests_list, 0)

        for quest in quests_list:
            quests[quest] = dict.fromkeys(parameters, 0)
            quests[quest]["Популярные объекты"] = {}
            quests[quest]["Средняя трата пыли"] = []
            quests[quest]["Средняя пыль на руках (не плат)"] = []
            quests[quest]["Средняя пыль на руках (плат)"] = []
            quests[quest]["Собрано пыли в среднем"] = []

        # Запись пользовательских данных в общие
        def flush_user_data():

            for user_quest in user_started_quests:
                quests[user_quest]["Дошли до квеста"] += 1
                # Платящий или не платящий
                if user_spends_dust:
                    quests[user_quest]["Средняя пыль на руках (плат)"].append(user_dust_on_hands[user_quest])
                else:
                    quests[user_quest]["Средняя пыль на руках (не плат)"].append(user_dust_on_hands[user_quest])
                    # if user_quest > "loc01q07":
                    # print(user_quest, Report.previous_user.user_id, user_dust_on_hands[user_quest])

            # траты пыли
            for user_quest, user_spent in user_spent_on_quest.items():
                if user_spent > 0:
                    quests[user_quest]["Потрачено пыли"] += user_spent
                    quests[user_quest]["Средняя трата пыли"].append(user_spent)
                if user_spent > 0 or user_restore_on_quest[user_quest] > 0:
                    quests[user_quest]["Потратили пыль"] += 1

        endgame_quest_error_handled = False
        while Report.get_next_event():

            if Report.is_new_user():
                # Обнуляем пользовательские данные, добавляем их в общие
                flush_user_data()
                user_started_quests = set()
                user_spent_on_quest = dict.fromkeys(quests, 0)
                user_restore_on_quest = dict.fromkeys(quests_list, 0)
                user_spends_dust = False
                previous_quest = None
                current_quest = "loc00q00"
                buy_decor = False
                coins_decor = 0
                buy_decor_quest = None
                restore = False
                coins_restore = 0
                restore_quest = None

            # Определеяем текущий квест пользователя.
            # ИЗ-ЗА ПРОЕБА, ПРИ UPDATEBUILDING КВЕСТ НЕ ОТСЫЛАЕТСЯ, ПРОСТО НЕ БУДЕМ МЕНЯТЬ
            if Report.current_event.__class__.__name__ in {CityEventsBuyDust.__name__, CityEventsBuyDecoration.__name__,
                                                           CityEventsQuest.__name__, CityEventsButton.__name__}:
                previous_quest = current_quest
                if Report.current_event.quest == "endgame":
                    if not endgame_quest_error_handled:
                        current_quest = get_next_locquest(current_quest)
                    endgame_quest_error_handled = True
                else:
                    current_quest = Report.current_event.quest

            elif Report.current_event.__class__.__name__ in {Match3FinishGame.__name__, CityEventsStartGame.__name__}:
                previous_quest = current_quest
                current_quest = get_locquest(Report.current_event.level_num)

            # Добавляем новый квест и параметры начала квеста
            if current_quest and current_quest not in user_started_quests:
                if previous_quest:
                    quests[previous_quest]["Собрано пыли в среднем"].append(user_got_dust_on_quest)
                    user_got_dust_on_quest = 0
                user_dust_on_hands[current_quest] = Report.current_user.game_coin
                user_started_quests.add(current_quest)

            # Покупка пыли
            if Report.current_event.__class__ is CityEventsBuyDust:
                bought = Report.current_user.game_coin - Report.current_user.previous_game_coin
                quests[current_quest]["Куплено пыли"] += bought

            # Обновление значения пыли после событий покупки/восстановления,
            #  определение потраченой суммы (добавить restore, когда обновят)
            if (buy_decor or restore) and Report.current_event.__class__ in (
                    CityEventsBuyDecoration, CityEventsButton, CityEventsBuyDust, CityEventsStartGame,
                    CityEventsInitGameState):
                spent = 0
                if not Report.is_new_user():
                    if buy_decor:
                        spent = coins_decor - Report.current_user.game_coin
                        coins_decor = 0
                    elif restore:
                        spent = coins_restore - Report.current_user.game_coin
                        coins_restore = 0
                    if spent > 0:
                        if buy_decor:
                            if buy_decor_quest != "loc01q04":
                                user_spends_dust = True
                            user_spent_on_quest[buy_decor_quest] += spent

                            if purchase not in quests[buy_decor_quest]["Популярные объекты"].keys():
                                quests[buy_decor_quest]["Популярные объекты"][purchase] = 0
                            quant = 1
                            if purchase == "road":
                                quant = int(spent / 10)
                            quests[buy_decor_quest]["Популярные объекты"][purchase] += quant
                            buy_decor = False
                        elif restore:
                            user_spends_dust = True
                            user_spent_on_quest[restore_quest] += spent
                            restore = False

            if Report.current_event.__class__ is CityEventsBuyDecoration and Report.current_event.status == "Success":
                buy_decor = True
                coins_decor = Report.current_user.game_coin
                buy_decor_quest = current_quest
                purchase = Report.current_event.purchase

            # обрабатываем восстановление мусора
            if Report.current_event.__class__.__name__ == CityEventsRestore.__name__:
                '''or (
                                not Report.is_new_user() and (
                                        Report.current_user.game_coin < Report.current_user.previous_game_coin) and
                                Report.current_app_version == "6.0" and not buy_decor):'''

                user_spends_dust = True
                if "Restore" not in quests[current_quest]["Популярные объекты"].keys():
                    quests[current_quest]["Популярные объекты"]["Restore"] = 0
                quests[current_quest]["Популярные объекты"]["Restore"] += 1
                user_restore_on_quest[current_quest] = 1
                if not buy_decor:
                    restore = True
                coins_restore = Report.current_user.game_coin
                restore_quest = current_quest

            # конец уроня, зарабатывание пыли
            if Report.current_event.__class__ is Match3FinishGame:
                user_got_dust_on_quest += Report.current_event.game_currency_count
                quests[current_quest]["Собрано пыли"] += Report.current_event.game_currency_count

        flush_user_data()

        # Перенос данных в таблицу
        for quest in quests.keys():
            if quest == "loc02q10":
                print(quest, quests[quest]["Средняя пыль на руках (плат)"])
            if quest == "loc02q11":
                print(quest, quests[quest]["Средняя пыль на руках (плат)"])
            quests[quest]["Средняя трата пыли"] = array_average(quests[quest]["Средняя трата пыли"],
                                                                name=quest + " " + "Средняя трата пыли", multiplier=5)
            quests[quest]["Средняя пыль на руках (плат)"] = array_average(
                quests[quest]["Средняя пыль на руках (плат)"],
                name=quest + " " + "Средняя пыль на руках (плат)",
                multiplier=4)
            quests[quest]["Средняя пыль на руках (не плат)"] = array_average(
                quests[quest]["Средняя пыль на руках (не плат)"], name=quest + " " + "Средняя пыль на руках (не плат)",
                multiplier=4)
            quests[quest]["Собрано пыли в среднем"] = array_average(quests[quest]["Собрано пыли в среднем"],
                                                                    name=quest + " " + "Собрано пыли в среднем",
                                                                    multiplier=4)

            top_objects = ""
            sorted_list = list(sorted(quests[quest]["Популярные объекты"].items(), reverse=True, key=lambda x: x[1]))

            if len(quests[quest]["Популярные объекты"].keys()) > 0:
                for index, (purchase, p_count) in enumerate(sorted_list):
                    if index < 5:
                        top_objects += purchase + ": " + str(p_count)
                    if index < min(4, len(quests[quest]["Популярные объекты"].keys()) - 1):
                        top_objects += ", "
            quests[quest]["Популярные объекты"] = top_objects

            for param in parameters:
                if quests[quest][param]:
                    df.at[quest, param] = quests[quest][param]
        # Вывод
        df.fillna(0, inplace=True)
        pd.options.display.max_colwidth = 150
        print(df.to_string())
        writer = pd.ExcelWriter("Results/Динамика пыли/DustDynamics " + str(min_version) + " " + os_str + ".xlsx")
        df.to_excel(excel_writer=writer)
        writer.save()

        # Рисуем гистограммы
        plt.figure(1, figsize=(18, 8))
        ax = plt.subplot(111)

        ax.bar(range(len(quests_list)), df["Средняя пыль на руках (плат)"], alpha=0.5,
               label="Средняя пыль на руках в начале")
        ax.bar(range(len(quests_list)), df["Собрано пыли в среднем"], alpha=0.5, label="Собрано пыли в среднем")
        ax.bar(range(len(quests_list)), df["Средняя трата пыли"], alpha=0.5, label="Средняя трата пыли")
        ax.set_xticks(range(len(quests_list)))
        ax.set_xticklabels(quests_list)

        for tick in ax.get_xticklabels():
            tick.set_rotation(90)
        ax.legend()
        plt.title("Тратящие пыль")
        plt.savefig("Results/Динамика пыли/Dust Dynamics плат" + str(min_version) + ".png")
        plt.show()

        plt.figure(2, figsize=(18, 8))
        ax = plt.subplot(111)
        ax.bar(range(len(quests_list)), df["Средняя пыль на руках (не плат)"], alpha=0.5,
               label="Средняя пыль на руках в начале")
        ax.bar(range(len(quests_list)), df["Собрано пыли в среднем"], alpha=0.5, label="Собрано пыли в среднем")
        ax.set_xticks(range(len(quests_list)))
        ax.set_xticklabels(quests_list)
        for tick in ax.get_xticklabels():
            tick.set_rotation(90)
        ax.legend()
        plt.title("Не тратящие пыль")
        plt.savefig("Results/Динамика пыли/Dust Dynamics не плат" + str(min_version) + ".png")
        plt.show()
