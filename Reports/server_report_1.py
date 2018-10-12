from enum import Enum
import re
import pandas as pd
import datetime
from datetime import timedelta
from functools import wraps
import time
import MySQLdb
try:
    import ujson as json
except ImportError:
    print("No ujson found. Using json.")
    import json

def time_count(fn):
    """
    Декоратор для подсчета времени выполнения функции
    :param fn: анализируемая функция
    :return: обернутая функция
    """

    @wraps(fn)
    def wrapped(*args, **kwargs):
        start_time = time.time()
        result = fn(*args, **kwargs)
        print("Время: %.3s сек.\n" % (time.time() - start_time))

        return result

    return wrapped


test_devices_ios = {
    "68653B88-C937-479D-8548-C3020DDEB3C2", "FB5A77D5-5067-4E16-9830-65492BA81174",
    "F0890F68-5D19-46A5-88D9-CA54243376F8", "16E124C9-EE34-4179-814A-BB511A0A9025",
    "47ADA9C1-DADD-4115-A332-52F3291FBD76", "1BF0CFFB-D192-430C-9B67-612845A8A430",
    "AE03F39E-F442-4F3B-BAE2-954D028099C5", "E7C12811-08FF-4A9E-83D5-44EE98B4F530",
    "51794505-B791-4BE9-B6AA-B4E718A69847", "DC416F15-B602-44E5-9AC3-B34D60284F0B",
    "00AB8828-4167-44C6-AEAC-A46558ECEBB1", "E9073059-D0A1-44F8-B206-72AE0D366381",
    "A322DE92-758A-4503-93D6-C2C58CF1B6A7", "7B633152-0E9F-478F-93DB-F5301D9BE271",
    "6AA563C5-65E0-416C-AC48-EBD79AB20D69", "A322DE92-758A-4503-93D6-C2C58CF1B6A7",
    "722870FC-3EC0-4690-8B22-C6ACC1BA6304", "25EAF46B-09D2-4BF0-8F92-3F7CC1E2435D"
                                            "47ADA9C1-DADD-4115-A332-52F3291FBD76",
    "2AB947E4-B36A-44DA-9666-8456D11DF47B",
    "07632979-F475-43D2-B006-7D17DCDEBCCF",
    "E66C4F64-5CEE-40C6-9A04-FA512D3B6FF3",
    "2FA9246C-1CEB-4904-872D-F5B07371A571",
    "CEB10F0B-57AE-4399-8B1F-19D1519380EC",
    "9B74F004-3894-4E23-8A89-7CEEE20753C1",
    "AD64F7A4-30CF-4C89-A33C-65AABE3D1061",

    "B4AB781D-654D-4AEB-AAE9-2F4ABF1BC92B",
    "DCE5132A-7691-4C96-ABD3-5E5A3308898B",

    # временно, пока не решу, что делать с людьми, меняющими девайсы и ifa
    "1E629546-A1E1-4B25-88DE-0AA4060F8509",
    "44D40C4B-77C4-4CB0-8B9C-CE846D2C7BE1",
    "60282134-AF9B-4BF5-A53A-BE84FE6CFD08",
    "E6F740F0-3E52-4A9B-9350-32257BCA2FD1",
    "42794211-5143-40C0-A126-4A0232F87C9E"

}
class Report():
    '''
    Класс Report - ядро отчёта. Оно осуществляет подключение к базе данных, извлечение событий, их парсинг,
    определение статуса текущего пользователя, появление нового пользователя, исключает тестеров,
    контролирует солблюдение версии приложения, автоматически определяет первую сессию, время с установки,
    время с последнего входа..
    '''
    user_ifa_skip_list = set(test_devices_ios)
    user_ifv_skip_list = set(test_devices_ios)
    installs = None
    os = None
    total_users = 0
    testers = set()

    def __init__(self, sql_events,
                 os="ios",
                 user_status_check=False,
                 min_app_version="5.0",
                 exact=False,
                 get_installs=False,
                 installs_parameters=["tracker_name", "install_datetime", "country_iso_code"],
                 installs_period=[datetime.datetime.strptime("2018-06-14", "%Y-%m-%d").date(), str(datetime.datetime.now().date())],
                 min_install_version="0.0",
                 max_install_version=None
                 ):
        '''

        :param sql_events: SQL запрос для базы
        :param user_status_check: Нужна ли проверка статуса пользователя
        (для этого нужно добавить в запрос события с данными по валюте, покупкам..)
        :param min_app_version: Минимальная версия приложения
        :param exact: Должна ли версия приложения обязательно совпадать с минимальной
        '''

        Report.os = os
        Report.total_users = 0
        self.current_event = None
        self.previous_event = None
        self.current_user = None
        self.previous_user = None
        self.current_app_version = None
        self.event_data = None

        self.user_status_check = user_status_check
        self.min_app_version = min_app_version
        self.exact = exact

        if get_installs:
            Report.installs = get_installs_list(os="ios",
                                                period_start=installs_period[0],
                                                period_end=installs_period[1],
                                                parameters=installs_parameters,
                                                min_version=min_install_version,
                                                max_version=max_install_version
                                                )
            sql_events = Report._insert_installs_in_sql(sql_events)
        # print(sql_events)
        events, db = get_data(sql=sql_events)
        self.events = events
        self.db = db

    def get_next_event(self):
        '''
        Получение и обработка следующего события из базы.
        В случае, когда события закончатся, база данных отключается
        :return: True - Событие обработано, получен игрок и событие, None - события закончились
        '''
        event = None
        while not event:
            # Попытка достать из потока базы событие
            event_data = self.events.fetch_row(maxrows=1, how=1)

            # Если оно существует
            if event_data:
                # то берем 0й элемент, т.к. оно приходит в виду (event_data,)
                self.event_data = event_data[0]
                event = None

                # пытаемся получить игрока из события
                got_user = self.get_next_user()
                # если с ним нет проблем (прошел все проверки)
                if got_user:
                    # получаем следующее время события и версию приложения
                    # получаем следующее время события и версию приложения

                    if "app_version_name" in self.event_data.keys():
                        self.current_app_version = self.event_data["app_version_name"]
                    # заменяем предыдущее событие текущим
                    if self.current_event:
                        self.previous_event = self.current_event
                    # парсим событие
                    if "event_json" in self.event_data.keys():
                        json = self.event_data["event_json"]
                    else:
                        json = None
                    event = parse_event(event_name=self.event_data["event_name"],
                                        event_json=json, datetime=self.get_datetime())
                    self.current_event = event

                    # если нужно, обновляем статус игрока
                    if self.user_status_check:
                        self.user_status_update()

                    # проверка первой сессии
                    if not self.is_new_user() and self.current_user and self.current_user.first_session and self.current_event.__class__ is CityEventsInitGameState:
                        self.current_user.first_session = False

                    # если это первое событие, то делаем предыдущее событие равным ему
                    if not self.previous_event:
                        self.previous_event = self.current_event
                # если все хорошо, и мы получили текущего игрока и событие, они передадутся в отчёт
                # в противном случае возьмем следующее событие по циклу
                if got_user and event:
                    return True

            # если больше нет событий, закрываем базу и останавливаем цикл в отчёте
            else:
                self.db.close()

                return None

    def get_next_user(self):
        '''
        Получить игрока текущего события
        :return: True - игрок получен (старый или новый),
                    None - игрок не получен (тестер, установка неверной версии приложения, в списке пропуска)
        '''
        user_id1 = self.event_data["ios_ifa"]
        user_id2 = self.event_data["ios_ifv"]

        # делаем текущего предыдущим (будет верно даже если следующий "не подойдет")
        if self.current_user:
            self.previous_user = self.current_user

        # если пользователь отличается от предыдущего
        if self.is_new_user(next_id1=user_id1, next_id2=user_id2):
            new_user = User(id_1=user_id1,
                            id_2=user_id2)
            new_user.install_date, new_user.publisher, new_user.source = \
                Report._get_install_data(user_id1, user_id2) if Report.installs \
                    else (self.event_data["event_datetime"].date(), None, None)

            if "app_version_name" in self.event_data.keys():
                new_user.installed_app_version = self.event_data["app_version_name"]
            if "country_iso_code" in self.event_data.keys():
                new_user.country = self.event_data["country_iso_code"]

            new_user.first_session = True

            # БЛОК ПРОВЕРОК ПОЛЬЗОВАТЕЛЯ
            # проверка версии приложения
            if self.min_app_version and (
                            (not self.exact and new_user.installed_app_version < self.min_app_version) or (
                                    self.exact and new_user.installed_app_version != self.min_app_version) or (
                                    user_id1 in Report.user_ifa_skip_list or
                                    user_id2 in Report.user_ifv_skip_list)):
                Report.user_ifa_skip_list.add(user_id1)
                Report.user_ifv_skip_list.add(user_id2)
                new_user.skipped = True
                return None

                # проверка на тестеров
            elif {user_id1, user_id2} & (test_devices_ios):
                Report.testers.add(new_user.user_id)
                return None
                # проверка на установку
            elif Report.installs and not Report._in_installs(user_id1, user_id2):
                Report.user_ifa_skip_list.add(user_id1)
                Report.user_ifv_skip_list.add(user_id2)
                new_user.skipped = True
                return None

            # если он прошел проверки на версию установленного приложения и на тестера, то становится
            # новым текущим пользователем
            else:
                self.current_user = new_user
                Report.total_users += 1

        if self.current_user:
            # Обновляем заходы пользователя
            if self.event_data["event_datetime"].date() not in self.current_user.entries:
                self.current_user.entries.append(self.event_data["event_datetime"].date())
            if "event_datetime" in self.event_data.keys():
                self.current_user.last_enter = self.event_data["event_datetime"]

            # Проверка, текущего пользователя могли добавить в пропуск
            if self.current_user.is_skipped():
                return None

        # если текущий юзер первый, то вначале мы не смогли обновить предыдущего, поэтому делаем предыдущего им же
        if not self.previous_user:
            self.previous_user = self.current_user

        return True

    def get_datetime(self):
        '''
        Получение datetime текущего события
        '''
        if "event_datetime" not in self.event_data.keys():
            # print("No datetime in data")
            return
        return self.event_data["event_datetime"]

    def is_new_user(self, next_id1=None, next_id2=None):
        '''
        Определение новый ли пользователь
        :param next_id1: id первого пользоваетели
        :param next_id2: id второго пользователя
        :return: новый ли пользователь
        '''
        # отличается ли от текущего
        if self.current_user and (next_id1 or next_id2):
            return self.current_user.user_id != next_id1 and self.current_user.user_id != next_id2
        # новый пользователь
        elif self.current_user and self.previous_user:
            if self.current_user.user_id == "" and self.previous_user.user_id == "":
                if "country_iso_code" in self.event_data.keys() and self.previous_user.country != self.current_user.country:
                    return True
                if "app_version_name" in self.event_data.keys() and self.previous_user.installed_app_version > self.current_user.installed_app_version:
                    return True
            return self.current_user.user_id != self.previous_user.user_id
        # самый первый
        elif not self.current_user:
            return True
        else:
            return False
    @staticmethod
    def _insert_installs_in_sql(sql):
        """
        Функция для добавления в SQL запрос строк с проверкой на вхождение в списки установок
        (сохраняет txt файл в корне проекта с последним исполненным запросом для проверки руками)
        :param sql: оригинальный SQL запрос
        :return: SQL запрос с вставленными строками
        """
        user_id1_list = []
        user_id2_list = []
        for install in Report.installs:
            user_id1_list.append(install["ios_ifa"])
            user_id2_list.append(install["ios_ifv"])
        lines = sql.splitlines()
        last_line_index = -2
        first_lines = lines
        for index, line in enumerate(lines):
            if "order by" in line:
                first_lines = lines[:-(len(lines) - index)]
                last_line_index = index

        new_sql = '\n'.join(first_lines)
        new_sql += """
        and
        (
        ios_ifa in ("{}") 
        and
        ios_ifv in ("{}")
        )
""".format('","'.join(map(str, user_id1_list)), '","'.join(map(str, user_id2_list)))
        new_sql += lines[last_line_index]
        file = open("sql.txt", "w")
        file.write(new_sql)
        return new_sql

    @staticmethod
    def _get_install_data(user_id1, user_id2):
        """
        Получение данных о дате установки, паблишере и трекере
        :param user_id1: ads_id
        :param user_id2: device_id
        :return: (дата установки, паблишер, трекер)
        """
        for install in Report.installs:
            if user_id2 != "" and user_id2 in install["ios_ifv"] or \
                                    user_id1 != "" and user_id1 in install["ios_ifa"]:
                publisher_name = install["publisher_name"] if install["publisher_name"] != "" else "Organic"
                return install["install_datetime"].date(), publisher_name, install["tracker_name"]
        return None, None

    @staticmethod
    def _in_installs(user_id1, user_id2):
        """
        Проверка на вхождение юзера в список загрузок
        :param user_id1: ads_id
        :param user_id2: device_id
        :return:
        """
        if Report.installs:
            for install in Report.installs:
                if user_id2 != "" and user_id2 in install["ios_ifv"] or \
                                        user_id1 != "" and user_id1 in install["ios_ifa"]:
                    return True
            return False
        else:
            return True

    def user_status_update(self):
        '''
        обновление статуса игрока
        для корректной работы необходимо включить в запрос события, включающие данные о валюте, покупках, жизнях и тд
        '''
        user = self.current_user
        event = self.current_event

        # при старте матч3 вычитаем выбранные и прибавляем купленные бонусы, обновляем жизни
        if event.__class__ is Match3StartGame:
            user.bonuses.plus(event.buy_bonuses_count)
            user.bonuses.minus(event.start_bonuses)
            if event.lives:
                user.lives = event.lives

        # в конце игры, если цели выполнены (а они должны быть выполнены по идее) вычитаем полученную за игру пыль
        # и прибавляем пыль после magic time
        elif event.__class__ is Match3FinishGame:
            user.previous_game_coin = user.game_coin
            if self.previous_event.__class__ is Match3CompleteTargets:
                user.game_coin -= int(self.previous_event.game_currency_count)
            user.game_coin += int(event.game_currency_count)

        # прибавляем полученную за игру пыль (на случай, когда не дожидаются FinishGame)
        elif event.__class__ is Match3CompleteTargets:
            user.previous_game_coin = user.game_coin
            user.game_coin += event.game_currency_count

        # обновляем жизни
        elif event.__class__ is Match3FailGame:
            if self.previous_event is not Match3FailGame:
                user.lost_life_datetime = self.current_event.datetime
            if event.lives:
                user.lives = event.lives

        # обновляем валюту и бонусы
        elif event.__class__ is CityEventsStartGame:
            user.premium_coin = event.premium_coin
            user.previous_game_coin = user.game_coin
            user.game_coin = event.game_coin
            user.bonuses = event.start_bonuses

        # обновляем валюту
        elif event.__class__ is CityEventsInitGameState:
            user.premium_coin = event.premium_coin
            user.previous_game_coin = user.game_coin
            user.game_coin = event.game_coin
    def skip_current_user(self):
        '''
        Пропуск последующих событий текущего игрока
        '''
        Report.user_ifa_skip_list.add(self.event_data["ios_ifa"])
        Report.user_ifv_skip_list.add(self.event_data["ios_ifv"])
        self.current_user.skipped = True



@time_count
def new_report(start=1, quantity=100, days_left=None, days_max=3, install_app_version="6.5", exact=False,
               report_app_version=None):
    if not report_app_version:
        report_app_version = install_app_version
    if not days_left:
        if days_max >= 28:
            days_left = 14
        elif days_max >= 14:
            days_left = 7
        elif days_max >= 7:
            days_left = 3
        else:
            days_left = 999

    sql = """
        SELECT ios_ifa,ios_ifv, event_name, event_json, event_datetime, app_version_name
        FROM sop_events.events_ios
        WHERE 
        (event_name = "Match3Events" 
            or (event_name = "CityEvent" 
                and (event_json like "%StartGame%"
                    )
                )
        )
        and
        (ios_ifa <>"" or ios_ifv <>"")
        order by ios_ifv, event_datetime,ios_ifv
        """

    report = Report(sql_events=sql, user_status_check=True, exact=exact, min_app_version=install_app_version,
                    get_installs=True, min_install_version=install_app_version, max_install_version=install_app_version)
    left_par = "Left " + str(days_left) + "+ days"
    levels = get_level_names(start, quantity)
    df = pd.DataFrame(index=levels,
                      columns=["Started", "Finished", "Start Convertion", "Clean Start", "Clean Finish", left_par,
                               "Difficulty", "Clean Difficulty", "Attempts", "Clean Attempts",
                               "Purchases Sum", "Purchases", "First purchase", "ARPU", "Dust", "Dust on hands"])
    df = df.fillna(0)

    def start_finish():
        if report.current_event.__class__ is Match3StartGame:
            started_levels.add(current_level)
        elif report.current_event.__class__ in (Match3FinishGame, Match3CompleteTargets):
            finished_levels.add(current_level)

    def clean_start_finish():
        if report.current_event.__class__ is Match3StartGame:

            if report.current_app_version >= report_app_version:
                if report.current_event.start_bonuses.first or \
                        report.current_event.start_bonuses.second or \
                        report.current_event.start_bonuses.third:
                    return False
                else:
                    df.loc[current_level, "Clean Start"] += 1
                    return True

        elif report.current_event.__class__ is Match3CompleteTargets:
            # проверка на чистую игру на этой версии приложения
            if report.current_app_version >= report_app_version and clean_start:
                # если не использовал молоток, то чисто
                if report.current_event.ingame_bonuses == 0:
                    df.loc[current_level, "Clean Finish"] += 1
                    return True
                else:
                    # если использовал - отбираем чистый старт
                    df.loc[current_level, "Clean Start"] -= 1
                    return False
        return clean_start

    def difficulty():
        if report.current_event.__class__ is Match3StartGame:
            # в сложнотсти считаем все старты уровней
            df.loc[current_level, "Difficulty"] += 1

    def attempts():

        if report.current_event.__class__ is Match3CompleteTargets:
            # количество попыток пройти уровень
            if user_attempts[current_level] == 0:
                user_attempts[current_level] = 1
            level_attempts[current_level].append(user_attempts[current_level])

        elif report.current_event.__class__ is Match3FailGame:
            # Увеличиваем счетчик попыток
            user_attempts[current_level] += 1

    def clean_attempts():

        if report.current_event.__class__ is Match3CompleteTargets:
            if report.current_app_version >= report_app_version:
                if clean_start and report.current_event.ingame_bonuses == 0:
                    # количество чистых попыток пройти уровень
                    if user_clean_attempts[current_level] == 0:
                        user_clean_attempts[current_level] = 1
                    level_clean_attempts[current_level].append(user_clean_attempts[current_level])

        elif report.current_event.__class__ is Match3FailGame:
            if report.current_app_version >= report_app_version:
                if clean_start and report.current_event.ingame_bonuses == 0:
                    user_clean_attempts[current_level] += 1

    def purchases():
        if report.current_event.__class__ is Match3BuyPremiumCoin and report.current_event.status == "Success":
            df.loc[current_level, "Purchases"] += 1
            df.loc[current_level, "Purchases Sum"] += get_price(report.current_event.purchase, money="rub")

            # Считаем первые покупки игроков
            if first_purchase:
                df.loc[current_level, "First purchase"] += 1
                return False
        return first_purchase

    def dust():
        if report.current_event.__class__ is Match3FinishGame:
            # Добавляем собранную на уровне пыль
            collected_dust[current_level].append(int(report.current_event.game_currency_count))
            # Добавляем пыль на руках у игроков
            user_dust[current_level].append(report.current_user.game_coin)

    # Стартовые параметры
    level_attempts = dict.fromkeys(levels)
    level_clean_attempts = dict.fromkeys(levels)
    user_attempts = dict.fromkeys(levels, 0)
    user_clean_attempts = dict.fromkeys(levels, 0)
    collected_dust = dict.fromkeys(levels)
    user_dust = dict.fromkeys(levels)
    user_clean_start = dict.fromkeys(levels)
    for level in levels:
        level_attempts[level] = []
        level_clean_attempts[level] = []
        collected_dust[level] = []
        user_dust[level] = []
        user_clean_start[level] = []

    started_levels = set()
    finished_levels = set()
    first_purchase = True
    current_level = None
    clean_start = True

    while report.get_next_event():

        # Событие М3 - может смениться уровень
        if report.current_event.__class__ in (
                Match3BuyPremiumCoin, Match3CompleteTargets, Match3FinishGame, Match3StartGame, Match3FailGame):
            current_level = report.current_event.level_num

        # Если уровень из списка рассматрвиаемых
        if current_level in levels:
            # if report.get_timediff(measure="day")>=1 or report.is_new_user():
            # print(report.current_user.user_id, report.get_time_since_install(), report.get_time_since_last_enter(), report.current_user.entries[-1], report.is_new_user() )

            # Нвоый пользователь
            if (report.is_new_user() and not report.previous_user.is_skipped()) or (
                            abs((report.current_user.install_date - report.current_event.datetime.date()).days)> days_max):
                # print("flush",report.is_new_user(), (report.get_time_since_install() > days_max))
                # если вышло время, то работаем с текущим пользователем
                if report.is_new_user():
                    user = report.previous_user
                    user_str = "previous"
                else:
                    user = report.current_user
                    user_str = "current"

                for level in started_levels:
                    df.loc[level, "Started"] += 1
                for level in finished_levels:
                    df.loc[level, "Finished"] += 1

                # Проверка на отвал
                # При отсутствии максимального дня в игре (для среза выборки) берется макс дата из базы данных.
                if (not days_max and abs((user.last_enter.date()- datetime.datetime.now().date()).days) >= days_left) or \
                        (days_max and abs((user.last_enter.date()-(user.install_date + timedelta(days=days_max))).days) > days_left):
                    if started_levels:
                        for level in list(started_levels - finished_levels):
                            df.loc[level, left_par] += 1

                # сброс личных параметров
                started_levels = set()
                finished_levels = set()
                user_attempts = dict.fromkeys(levels, 0)
                user_clean_attempts = dict.fromkeys(levels, 0)
                first_purchase = True

                if not report.is_new_user() and abs((report.current_user.install_date - report.current_event.datetime.date()).days) > days_max:
                    report.skip_current_user()
                    continue

            start_finish()
            clean_start = clean_start_finish()
            difficulty()
            attempts()
            clean_attempts()
            first_purchase = purchases()
            dust()

    # Финальные рассчеты
    df["Start Convertion"] = round(df["Started"] * 100 / report.total_users, 1)
    df["Difficulty"] = round(100 - df["Finished"] * 100 / df["Difficulty"], 1)
    df["Clean Difficulty"] = round(100 - df["Clean Finish"] * 100 / df["Clean Start"], 1)
    df["ARPU"] = round(df["Purchases Sum"] / df["Started"], 1)
    for level in levels:
        # проверка на выбросы в попытках
        if len(level_attempts[level]) > 0:
            level_attempts[level] = outliers_iqr(level_attempts[level], level + " attempts", multiplier=10)
            df.loc[level, "Attempts"] = round(1 - 1 / (sum(level_attempts[level]) / len(level_attempts[level])),
                                              3) * 100

        if len(level_clean_attempts[level]) > 0:
            level_clean_attempts[level] = outliers_iqr(level_clean_attempts[level], level + " clean attempts",
                                                       multiplier=4)
            df.loc[level, "Clean Attempts"] = round(
                1 - 1 / (sum(level_clean_attempts[level]) / len(level_clean_attempts[level])),
                3) * 100
        # Проверка на выбросы в значениях пыли
        if len(collected_dust[level]) > 0:
            if len(collected_dust[level]) > 10:
                collected_dust[level] = outliers_iqr(collected_dust[level], level + " collected dust", multiplier=5)
            df.loc[level, "Dust"] = round(sum(collected_dust[level]) / float(len(collected_dust[level])), 1)

        if len(user_dust[level]) > 0:
            if len(user_dust[level]) > 10:
                user_dust[level] = outliers_iqr(data_list=user_dust[level], where=level + " user dust",
                                                max_outliers=False, min_outliers=True, multiplier=15)
                user_dust[level] = outliers_iqr(user_dust[level], level + " user dust", multiplier=5)
            df.loc[level, "Dust on hands"] = round(sum(user_dust[level]) / float(len(user_dust[level])), 1)

    # Печать
    print("Total users:", report.total_users)
    print("Testers:", len(report.testers))
    print(df.to_string())

    writer = pd.ExcelWriter(
        "Levels " + str(start) + "-" + str(start + quantity - 1) + " " + report_app_version + " " + str(
            days_max) + "days" + ".xlsx")
    df.to_excel(excel_writer=writer)
    writer.save()
    del report


def get_level_names(start, quantity):
    return list((str(x).rjust(4, '0') for x in range(start, start + quantity)))



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

def get_installs_list(os="ios",
                      period_start=datetime.datetime.strptime("2018-06-14", "%Y-%m-%d").date(),
                      period_end=str(datetime.datetime.now().date()),
                      min_version="0.0",
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
    user_id1 = "ios_ifa"
    user_id2 = "ios_ifv"
    if isinstance(period_start, str):
        period_start = datetime.datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.datetime.strptime(period_end, "%Y-%m-%d").date()

    parameters = [user_id1, user_id2] + parameters
    if "install_datetime" not in parameters:
        parameters += ["install_datetime"]
    if "publisher_name" not in parameters:
        parameters += ["publisher_name"]
    if "tracker_name" not in parameters:
        parameters += ["tracker_name"]

    max_version = "and app_version_name <= " + str(max_version) if max_version else ""
    sql = """
    select {} 
    from sop_events.installs_{}
    where 
    install_datetime between '{}' and '{}'
    and
    app_version_name >= {} {}
    """.format(','.join(parameters), os, period_start,
               period_end, min_version, max_version)
    # print(sql)
    data, db = get_data(sql=sql, name="Загрузка установок.")

    installs = []

    installs_data = data.fetch_row(how=1, maxrows=1)
    fetched_install_data = installs_data[0]
    while installs_data:
        install = dict.fromkeys(parameters)
        for param in parameters:
            install[param] = fetched_install_data[param]
        installs.append(install)

        installs_data = data.fetch_row(how=1, maxrows=1)
        if installs_data:
            fetched_install_data = installs_data[0]

    db.close()
    return installs

def parse_event(event_name, event_json, datetime):
    # заменяем двойные двойные кавычки на одинакрные двойные кавычки (да, тупо...)
    event_json = re.sub(r'""', r'"', event_json)

    try:
        parameters = json.loads(event_json)
    except ValueError as er:
        print("Json error:", event_name, event_json)
        return None
    except Exception as er:
        print(er.args)
        print(event_name, event_json)
        return None

    try:

        if event_name == "Match3Events":
            new_event = parse_match3_event(parameters, datetime)
        elif event_name == "CityEvent":
            new_event = parse_city_event(parameters, datetime)
        #elif event_name == "TutorialSteps":
        #    new_event = parse_tutorial_steps(parameters, datetime)
        #elif event_name == "Tutorial":
        #    new_event = parse_tutorial_complete(parameters, datetime)
        else:
            raise ValueError("Event parse: Unknown event name:", event_name, datetime)

    except Exception as error:
        print("Error:", event_name, "\nJson:", event_json)
        print(error.args)
        return

    return new_event


class Event:
    def __init__(self, datetime):
        self.datetime = datetime
        pass


class Match3Event(Event):
    def __init__(self, level_num, session_id, datetime):
        super().__init__(datetime)
        self.level_num = level_num
        self.session_id = session_id


class Match3StartGame(Match3Event):
    def __init__(self, level_num, session_id, turn_count, lives, buy_bonuses_count, targets_list, start_bonuses,
                 datetime):
        super().__init__(level_num, session_id, datetime)
        self.turn_count = turn_count
        self.lives = lives
        self.buy_bonuses_count = buy_bonuses_count
        self.targets_list = targets_list
        self.start_bonuses = start_bonuses


class Match3FinishGame(Match3Event):
    def __init__(self, level_num, session_id, turn_count, game_currency_count, targets_list, datetime):
        super().__init__(level_num, session_id, datetime)
        self.turn_count = turn_count
        self.game_currency_count = game_currency_count
        self.targets_list = targets_list


class Match3CompleteTargets(Match3Event):
    def __init__(self, level_num, session_id, turn_count, game_currency_count, buy_steps_count, ingame_bonuses,
                 elements_count, targets_list, datetime):
        super().__init__(level_num, session_id, datetime)
        self.turn_count = turn_count
        self.game_currency_count = game_currency_count
        self.buy_steps_count = buy_steps_count
        self.targets_list = targets_list
        self.ingame_bonuses = ingame_bonuses
        self.elements_count = elements_count


class Match3FailGame(Match3Event):
    def __init__(self, fail_count, level_num, session_id, turn_count, buy_steps_count, lives, ingame_bonuses,
                 elements_count, targets_list, datetime):
        super().__init__(level_num, session_id, datetime)
        self.fail_count = fail_count
        self.turn_count = turn_count
        self.buy_steps_count = buy_steps_count
        self.lives = lives
        self.targets_list = targets_list
        self.ingame_bonuses = ingame_bonuses
        self.elements_count = elements_count


class PurchaseEvent(Event):
    def __init__(self, quest, purchase, status, datetime):
        super().__init__(datetime)
        self.quest = quest
        self.purchase = purchase
        self.status = status


class Match3BuyPremiumCoin(PurchaseEvent):
    def __init__(self, level_num, quest, app_purchase_sku, status, premium_coin, datetime):
        super().__init__(quest, app_purchase_sku, status, datetime)
        self.level_num = level_num
        self.premium_coin = premium_coin

class CityEventsStartGame(Event):
    def __init__(self, level_num, premium_coin, game_coin, start_bonuses, ingame_bonuses, datetime):
        super().__init__(datetime)
        self.level_num = level_num
        self.premium_coin = premium_coin
        self.game_coin = game_coin
        self.start_bonuses = start_bonuses
        self.ingame_bonuses = ingame_bonuses

class CityEventsInitGameState(Event):
    def __init__(self, premium_coin, game_coin, datetime):
        super().__init__(datetime)
        self.premium_coin = premium_coin
        self.game_coin = game_coin

class User:
    def __init__(self, id_2, id_1=None):
        if id_1:
            self.user_id = id_1
        else:
            self.user_id = id_2

        self.first_session = True
        self.install_date = None
        self.publisher = None
        self.source = None
        self.entries = []
        self.last_enter = None
        self.country = None

        self.lives = 5
        self.bonuses = Bonuses(0, 0, 0)
        self.premium_coin = 300
        self.game_coin = 400
        self.previous_game_coin = 400

        self.installed_app_version = None
        self.skipped = False

    def get_status(self):
        return str("Final status: Premium coin: " + str(self.premium_coin) + " Game coin: " + str(self.game_coin) +
                   " Lives: " + str(self.lives) + " Bonuses: " + self.bonuses.to_string())

    def is_skipped(self):
        return self.skipped

class Bonuses:
    __slots__ = {'first', 'second', 'third'}

    def __init__(self, first_bonus=0, second_bonus=0, third_bonus=0):
        self.first = first_bonus
        self.second = second_bonus
        self.third = third_bonus

    def to_string(self):
        info = "First: " + str(self.first) + ", Second: " + str(self.second) + ", Third: " + str(self.third)
        return info

    def plus(self, bonuses):
        if bonuses.__class__ is Bonuses:
            self.first += bonuses.first
            self.second += bonuses.second
            self.third += bonuses.third
        else:
            print("Ошибка типа при сложении бонусов")

    def minus(self, bonuses):
        if bonuses.__class__ is Bonuses:
            self.first -= bonuses.first
            self.second -= bonuses.second
            self.third -= bonuses.third
        else:
            print("Ошибка типа при вычитании бонусов")

def get_price(coins,money="rub"):
    if coins=="100gold":
        if money=="rub":
            return 75
    elif coins == "550gold":
        if money == "rub":
            return 459
    elif coins == "1200gold":
        if money == "rub":
            return 999
    elif coins == "2500gold":
        if money == "rub":
            return 1890
    elif coins == "5300gold":
        if money == "rub":
            return 3790
    elif coins == "11000gold":
        if money == "rub":
            return 7490
def outliers_iqr(data_list, where=None, max_outliers=True, min_outliers=False, multiplier=1.5, print_excl=True,
                 adaptive=False):
    """
    IQR-анализ выбросов
    :param data_list: список данных
    :param where: имя, что рассчитывем для понятного вывода
    :param max_outliers: максимальные выбросы
    :param min_outliers: минимальные выбросы
    :param multiplier: множитель
    :param print_excl: печать удаленных данных
    :param adaptive: подстраивающийся под объем массива множитель
    :return:
    """

    data_without_outliers = data_list
    excluded = None
    if adaptive and len(data_list) < 15:
        multiplier = round(multiplier * 0.25, 1)
    elif adaptive and len(data_list) > 150:
        multiplier = round(multiplier * 3, 1)

    if len(data_list) > 3:
        data_series = pd.Series(data_list)

        q1 = int(data_series.quantile([0.25]))
        q3 = int(data_series.quantile([0.75]))
        iqr = multiplier * (q3 - q1)
        data_list = sorted(data_list, reverse=True)

        if q1 != q3:
            if max_outliers:
                data_without_outliers = list(x for x in data_list if x < q3 + iqr)
                data_without_outliers = sorted(data_without_outliers, reverse=True)
                excluded = list(x for x in data_list if x >= q3 + iqr)

            if min_outliers:
                data_without_outliers = list(x for x in data_list if x > q1 - iqr)
                data_without_outliers = sorted(data_without_outliers, reverse=True)
                excluded = list(x for x in data_list if x <= q1 - iqr)

        if print_excl and excluded and len(excluded) > 0:
            print("Выбросы в:", where)
            print("изначально:", data_list)
            print("исключили:", excluded, "Q1:", q1, "Q3:", q3, str(multiplier) + "*IQR", iqr)

    return data_without_outliers

def parse_match3_event(parameters, datetime):
    level_num = list(parameters.keys())[0]
    level_num_corrected = level_num
    if "X" in level_num:
        level_num_corrected = "9" + level_num[2:]
    event_type = list(parameters[level_num].keys())[0]

    try:
        if event_type == "StartGame":

            # костыль, Lives появились в 5.3
            if "Lives" in list(parameters[level_num][event_type].keys()):
                lives = int(parameters[level_num][event_type]["Lives"])
                # print("start m3 lives", lives)
            else:
                lives = None

            return Match3StartGame(
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                lives=lives,
                buy_bonuses_count=get_bought_bonuses(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                start_bonuses=get_bonuses(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif event_type == "FinishGame":

            return Match3FinishGame(
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                game_currency_count=get_currency_count(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif event_type == "CompleteTargets":
            return Match3CompleteTargets(
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                game_currency_count=get_currency_count(parameters[level_num][event_type]),
                buy_steps_count=int(parameters[level_num][event_type]["BuyStepsCount"]),
                ingame_bonuses=int(parameters[level_num][event_type]["InGameBonuses"]["Hammer"]),
                elements_count=get_elements(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif "FailGame" in event_type:

            # костыль, Lives появились в 5.3
            if "Lives" in list(parameters[level_num][event_type].keys()):
                lives = int(parameters[level_num][event_type]["Lives"])
                # print("fail m3 lives", lives)
            else:
                lives = None

            return Match3FailGame(
                fail_count=event_type[9:],
                level_num=level_num_corrected,
                session_id=parameters[level_num][event_type]["LevelSessionID"],
                turn_count=int(parameters[level_num][event_type]["TurnCount"]),
                buy_steps_count=int(parameters[level_num][event_type]["BuyStepsCount"]),
                lives=lives,
                ingame_bonuses=int(parameters[level_num][event_type]["InGameBonuses"]["Hammer"]),
                elements_count=get_elements(parameters[level_num][event_type]),
                targets_list=get_targets_list(parameters[level_num][event_type]),
                datetime=datetime
            )

        elif event_type == "BuyPremiumCoinM3":

            # костыль
            if "premiumCoin" in list(parameters[level_num][event_type].keys()):
                premium_coin = int(parameters[level_num][event_type]["premiumCoin"])
                # print("buy premium m3 premium coin", premium_coin)
            else:
                premium_coin = None

            return Match3BuyPremiumCoin(
                level_num=level_num_corrected,
                quest=parameters[level_num][event_type]["Quest"],
                app_purchase_sku=parameters[level_num][event_type]["AppPurchaseSKU"],
                status=parameters[level_num][event_type]["Status"],
                premium_coin=premium_coin,
                datetime=datetime
            )

        else:
            raise ValueError("Event parse: Unknown Match 3 event type:", event_type)

    except ValueError as error:
        print(error.args)

def get_targets_list(params):
    first_target = Target(
        params["FirstTarget"]["TargetCount"],
        params["FirstTarget"]["Target"],
        params["FirstTarget"]["OverflowTargetCount"]
    )

    if params["SecondTarget"]:
        second_target = Target(
            params["SecondTarget"]["TargetCount"],
            params["SecondTarget"]["Target"],
            params["SecondTarget"]["OverflowTargetCount"]
        )

        return first_target, second_target
    return first_target, None

class Target:
    __slots__ = {'target_count', 'target', 'overflow_target_cunt'}

    def __init__(self, target_count, target, overflow_target_count):
        self.target_count = target_count
        self.target = target
        self.overflow_target_cunt = overflow_target_count

def get_elements(params):
    # print(params["ElementsCount"])
    supers = {}
    colors = {}
    targets = {}
    others = {}
    for key, value in params["ElementsCount"].items():
        color = Colors.get_color(key)
        if color:
            colors[color] = value
            continue
        sup = Supers.get_super(key)
        if sup:
            supers[sup] = value
            continue
        target = Targets.get_target(key)
        if target:
            targets[target] = value
            continue

        print("Elements parse: Unknown object:", key)
        others[key] = value

    return Elements(super_count=supers, targets_count=targets, colors_count=colors, others_count=others)

class Elements:
    def __init__(self, colors_count, super_count, targets_count, others_count):
        self.colors_count = colors_count
        self.super_count = super_count
        self.targets_count = targets_count
        self.others_count = others_count

class Colors(Enum):
    Blue = 0,
    Red = 1,
    Yellow = 2,
    Green = 3,
    Black = 4,
    White = 5

    @staticmethod
    def get_color(color):
        if color == "Color6_Blue":
            return Colors.Blue
        elif color == "Color6_Red":
            return Colors.Red
        elif color == "Color6_Yellow":
            return Colors.Yellow
        elif color == "Color6_Green":
            return Colors.Green
        elif color == "Color6_Black":
            return Colors.Black
        elif color == "Color6_White":
            return Colors.White
        else:
            #print("Unknown color", color)
            return

class Supers(Enum):
    SmallLightning_h = 0,
    SmallLightning_v = 1,
    FireSpark = 2,
    FireRing = 3,
    BigLightning_h = 4,
    BigLightning_v = 5,
    SphereOfFire = 6
    TwoStarBonus = 7

    StarBonus = 8

    @staticmethod
    def get_super(super_token):
        if super_token == "Super_SmallLightning_h":
            return Supers.SmallLightning_h
        elif super_token == "Super_SmallLightning_v":
            return Supers.SmallLightning_v
        elif super_token == "Super_FireSpark":
            return Supers.FireSpark
        elif super_token == "Super_FireRing":
            return Supers.FireRing
        elif super_token == "Super_BigLightning_h":
            return Supers.BigLightning_h
        elif super_token == "Super_BigLightning_v":
            return Supers.BigLightning_v
        elif super_token == "Super_SphereOfFire":
            return Supers.SphereOfFire
        elif super_token == "Super_TwoStarBonus":
            return Supers.TwoStarBonus
        elif super_token == "StarBonus":
            return Supers.StarBonus
        else:
            #print("Unknown super token", super_token)
            return

class Targets(Enum):
    Ballon = 0,
    Box_l1 = 1,
    Box_l2 = 2,
    Box_l3 = 3,
    Carpet_l1 = 4,
    Carpet_l2 = 5,
    Unicorn = 6,
    Weight = 7,
    LightStar = 8,
    Chain_l1 = 9,
    Stone = 10,
    Granite_l1 = 11,
    Granite_l2 = 12,
    Ice_l1 = 13,
    Ice_l2 = 14
    Diamond_Level1 = 15,
    Diamond_Level2 = 16,
    Diamond_Level3 = 17,
    Sand = 18,
    CrystalBall = 19

    @staticmethod
    def get_target(target):
        if target == "Ballon":
            return Targets.Ballon
        elif target == "Box_Level1":
            return Targets.Box_l1
        elif target == "Carpet_Level1":
            return Targets.Carpet_l1
        elif target == "Box_Level2":
            return Targets.Box_l2
        elif target == "Box_Level3":
            return Targets.Box_l3
        elif target == "Carpet_Level2":
            return Targets.Carpet_l2
        elif target == "Stone":
            return Targets.Stone
        elif target == "Unicorn":
            return Targets.Black
        elif target == "Weight":
            return Targets.Weight
        elif target == "LightStar":
            return Targets.LightStar
        elif target == "Chain_Level1":
            return Targets.Chain_l1
        elif target == "Granite_Level1":
            return Targets.Granite_l1
        elif target == "Granite_Level2":
            return Targets.Granite_l2
        elif target == "Ice_Level1":
            return Targets.Ice_l1
        elif target == "Ice_Level2":
            return Targets.Ice_l2
        elif target == "Diamond_Level3":
            return Targets.Diamond_Level3
        elif target == "Diamond_Level2":
            return Targets.Diamond_Level2
        elif target == "Diamond_Level1":
            return Targets.Diamond_Level1
        elif target == "Sand":
            return Targets.Sand
        elif target == "CrystalBall":
            return Targets.CrystalBall
        else:
            #print("Unknown target", target)
            return

def get_bought_bonuses(params):
    bought_bonuses = Bonuses()
    if "FirstIntroductory" in params["BuyBonusesCount"]:
        bought_bonuses.first = params["BuyBonusesCount"]["FirstIntroductory"]

    if "SecondIntroductory" in params["BuyBonusesCount"]:
        bought_bonuses.second = params["BuyBonusesCount"]["SecondIntroductory"]

    if "ThirdIntroductory" in params["BuyBonusesCount"]:
        bought_bonuses.third = params["BuyBonusesCount"]["ThirdIntroductory"]

    return bought_bonuses


def get_bonuses(params):
    return Bonuses(
        int(params["StartBonuses"]["First"]),
        int(params["StartBonuses"]["Second"]),
        int(params["StartBonuses"]["Third"])
    )


def get_currency_count(params):
    if params["GameCurrencyCount"] == "not calculate points":
        return 0
    else:
        return int(params["GameCurrencyCount"])


def parse_city_event(parameters, datetime):
    event_type = list(parameters.keys())[0]

    try:
        if event_type == "StartGame":

            level_num = list(parameters[event_type].keys())[0]
            level_num_corrected = level_num
            if "X" in level_num:
                level_num_corrected = "9" + level_num[2:]

            return CityEventsStartGame(
                level_num=level_num_corrected,
                premium_coin=int(parameters[event_type][level_num]["premiumCoin"]),
                game_coin=int(parameters[event_type][level_num]["gameCoin"]),
                start_bonuses=get_bonuses(parameters[event_type][level_num]),
                ingame_bonuses=int(parameters[event_type][level_num]["InGameBonuses"]["Hammer"]),
                datetime=datetime
            )
    except ValueError as error:
        print(error.args)