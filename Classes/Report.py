from Data.Data import get_data, get_installs_list
from Data.Parse import parse_event
from Classes.User import User
from Classes.Events import *
from Utilities.Utils import test_devices_android, test_devices_ios, get_timediff
from datetime import datetime, date
from weakref import WeakValueDictionary
from Classes.OS import OS


# works in Python 2 & 3

class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(_Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            print("Recreating Singleton object! Check your code.")
        return cls._instances[cls]

    def get_instance(self):
        if self._instances:
            return self._instances
        else:
            return None


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    def tearDown(cls):
        cls._instances = {}


class Report(Singleton):
    '''
    Класс Report - ядро отчёта. Оно осуществляет подключение к базе данных, извлечение событий, их парсинг,
    определение статуса текущего пользователя, появление нового пользователя, исключает тестеров,
    контролирует солблюдение версии приложения, автоматически определяет первую сессию, время с установки,
    время с последнего входа..
    '''
    user_ifa_skip_list = set(test_devices_ios | test_devices_android)
    user_ifv_skip_list = set(test_devices_ios | test_devices_android)
    installs = None
    os = None
    total_users = 0
    testers = set()

    def __init__(self, sql_events,
                 os=OS.ios,
                 user_status_check=False,
                 min_app_version="5.0",
                 exact=False,
                 countries=None,
                 get_installs=False,
                 installs_parameters=["tracker_name", "install_datetime", "country_iso_code"],
                 installs_period=[datetime.strptime("2018-06-14", "%Y-%m-%d").date(), str(datetime.now().date())],
                 min_install_version=None,
                 max_install_version=None
                 ):
        '''

        :param sql_events: SQL запрос для базы
        :param user_status_check: Нужна ли проверка статуса пользователя
        (для этого нужно добавить в запрос события с данными по валюте, покупкам..)
        :param min_app_version: Минимальная версия приложения
        :param exact: Должна ли версия приложения обязательно совпадать с минимальной
        '''
        if isinstance(os, OS):
            Report.os = os
        else:
            if os.lower() == "android":
                Report.os = OS.android
            elif os.lower() == "ios":
                Report.os = OS.ios
            elif os.lower() == "amazon":
                Report.os = OS.amazon
            else:
                print("Неверно введена операционная система. Выставлен Android по-умолчанию.")
                Report.os = OS.android
        Report.total_users = 0
        self.current_event = None
        self.previous_event = None
        self.current_user = None
        self.previous_user = None
        self.current_app_version = None
        self.event_data = None
        self.countries = countries

        self.user_status_check = user_status_check
        self.min_app_version = min_app_version
        self.exact = exact

        if get_installs:
            Report.installs = get_installs_list(os=os,
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
                        self.current_user.user_status_update(self.current_event, self.previous_event)

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
                Singleton.tearDown(self)
                return None

    def get_next_user(self):
        '''
        Получить игрока текущего события
        :return: True - игрок получен (старый или новый),
                    None - игрок не получен (тестер, установка неверной версии приложения, в списке пропуска)
        '''
        user_id1 = self.event_data[OS.get_aid(Report.os)]
        user_id2 = self.event_data[OS.get_id(Report.os)]

        # делаем текущего предыдущим (будет верно даже если следующий "не подойдет")
        if self.current_user:
            self.previous_user = self.current_user

        # если пользователь отличается от предыдущего
        if self.is_new_user(next_id1=user_id1, next_id2=user_id2):
            new_user = User(id_1=user_id1,
                            id_2=user_id2)

            # БЛОК ПРОВЕРОК ПОЛЬЗОВАТЕЛЯ
            # проверка версии приложения
            if self.min_app_version not in (None, "0", "0.0.0") and (
                            (not self.exact and new_user.installed_app_version < self.min_app_version) or (
                                    self.exact and new_user.installed_app_version != self.min_app_version) or (
                                    user_id1 in Report.user_ifa_skip_list or
                                    user_id2 in Report.user_ifv_skip_list)):
                print("skip vers", new_user.user_id, new_user.installed_app_version)
                Report.user_ifa_skip_list.add(user_id1)
                Report.user_ifv_skip_list.add(user_id2)
                return None
                # проверка на тестеров
            elif {user_id1, user_id2} & (test_devices_ios | test_devices_android):
                #print("skip test", new_user.user_id, new_user.installed_app_version)
                Report.testers.add(new_user.user_id)
                return None
                # проверка на установку
            elif Report.installs and not Report._in_installs(user_id1, user_id2):
                print("skip inst", new_user.user_id)
                Report.user_ifa_skip_list.add(user_id1)
                Report.user_ifv_skip_list.add(user_id2)
                new_user.skipped = True
                return None
                # проверка по странам
            elif self.countries and new_user.country not in self.countries:
                print("skip countries", self.countries, new_user.country)
                return None

            # если он прошел проверки на версию установленного приложения и на тестера, то становится
            # новым текущим пользователем
            else:
                if Report.installs:
                    new_user.install_date, \
                    new_user.publisher, \
                    new_user.source, \
                    new_user.installed_app_version, \
                    new_user.country = Report._get_install_data(user_id1, user_id2)
                else:
                    new_user.install_date = self.event_data["event_datetime"].date()
                    new_user.publisher = None
                    new_user.source = None
                    new_user.installed_app_version = self.event_data[
                        "app_version_name"] if "app_version_name" in self.event_data.keys() else None
                    new_user.country = self.event_data[
                        "country_iso_code"] if "country_iso_code" in self.event_data.keys() else None

                new_user.first_session = True

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
                if "country_iso_code" in self.event_data.keys() and \
                                self.previous_user.country != self.current_user.country:
                    return True
                if "app_version_name" in self.event_data.keys() and \
                                self.previous_user.installed_app_version > self.current_user.installed_app_version:
                    return True
            return self.current_user.user_id != self.previous_user.user_id
        # самый первый (заходит сюда лишь при создании первого пользователя)
        elif not self.current_user:
            return True
        else:
            return False

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
                if user_id2 != "" and user_id2 in install[OS.get_id(Report.os)] or \
                                        user_id1 != "" and user_id1 in install[OS.get_aid(Report.os)]:
                    return True
            return False
        else:
            return True

    @staticmethod
    def _get_install_data(user_id1, user_id2):
        """
        Получение данных о дате установки, паблишере и трекере
        :param user_id1: ads_id
        :param user_id2: device_id
        :return: (дата установки, паблишер, трекер)
        """
        for install in Report.installs:
            if user_id2 != "" and user_id2 in install[OS.get_id(Report.os)] or \
                                    user_id1 != "" and user_id1 in install[OS.get_aid(Report.os)]:
                publisher_name = install["publisher_name"] if install["publisher_name"] != "" else "Organic"
                tracker_name = install["tracker_name"] if install["tracker_name"] not in (
                "", "unknown") else OS.get_source(Report.os)
                return install["install_datetime"].date(), \
                       publisher_name, \
                       tracker_name, \
                       install["app_version_name"], \
                       install["country_iso_code"]
        return None, None, None, None, None

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
            user_id1_list.append(install[OS.get_aid(Report.os)])
            user_id2_list.append(install[OS.get_id(Report.os)])
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
        {0} in ("{1}") 
        and
        {2} in ("{3}")
        )
""".format(OS.get_aid(Report.os), '","'.join(map(str, user_id1_list)), OS.get_id(Report.os),
           '","'.join(map(str, user_id2_list)))
        new_sql += lines[last_line_index]
        file = open("sql.txt", "w")
        file.write(new_sql)
        return new_sql

    def get_timediff(self, measure="min"):
        '''
        Определение разницы во времени между текущим и предыдущим событием
        :param measure: мера min/sec/day (min по умолчанию)
        :return: разница во времени по умолчанию - между текущим и предыдущим событием
        '''
        return get_timediff(self.current_event.datetime, self.previous_event.datetime, measure=measure)

    def get_time_since_install(self, measure="day", user="current"):
        '''
        время с момента установки
        :param measure: мера min/sec/day (по умолчанию day)
        :param user: текущий или предыдущий пользователь
        :return: время с момента установки
        '''
        if user == "current":
            new_user = self.current_user
            new_datetime = self.current_event.datetime
        else:
            new_user = self.previous_user
            new_datetime = self.previous_event.datetime

        return get_timediff(new_datetime, new_user.install_date, measure=measure)

    def get_time_since_last_enter(self, measure="day", user="current"):
        '''
        время с момента установки
        :param measure: мера min/sec/day (по умолчанию day)
        :param user: текущий или предыдущий пользователь
        :return: время с момента последнего входа
        '''
        if user == "current":
            new_user = self.current_user
            new_datetime = self.current_event.datetime
        else:
            new_user = self.previous_user
            new_datetime = self.previous_event.datetime

        return get_timediff(new_datetime, new_user.entries[-1 * min(2, len(new_user.entries))], measure=measure)

    def skip_current_user(self):
        '''
        Пропуск последующих событий текущего игрока
        '''
        Report.user_ifa_skip_list.add(self.event_data[OS.get_aid(Report.os)])
        Report.user_ifv_skip_list.add(self.event_data[OS.get_id(Report.os)])
        self.current_user.skipped = True
