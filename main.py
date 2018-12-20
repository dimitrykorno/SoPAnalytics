import matplotlib
matplotlib.use('Agg')
from report_api.Menu import Menu
from sop_analytics.Reports import M3LevelsFunnel, M3DetailedLevel, GlobalFunnel, UsersSessions, M3LevelBonuses, \
    LastEventHistogram, \
    DetailedFunnel, LifetimeHistogram, ProgressHistogram, DustDynamics, CumulativeROI, RetentionPatternHypothesis, \
    InAppSales, ElementByLevel, DAU, MAU,DustPurchases

mode = "console"
reports = [
    ("1. Отчёт по качеству уровней", M3LevelsFunnel.new_report),
    ("2. Детальный анализ уровня", M3DetailedLevel.new_report),
    ("3. Глобальные отвалы", GlobalFunnel.new_report),
    ("4. Детальные отвалы на уровне", DetailedFunnel.new_report),
    ("5. Использование бонусов", M3LevelBonuses.new_report),
    ("6. Печать сессий", UsersSessions.new_report),
    ("7. Гистограма последних событий", LastEventHistogram.new_report),
    ("8. Гистограма лайфтайма", LifetimeHistogram.new_report),
    ("9. Гистограма прогресса", ProgressHistogram.new_report),
    ("10.Динамика пыли", DustDynamics.new_report),
    ("11.Покупка пыли", DustPurchases.new_report),
    ("12.Накопительный ROI", CumulativeROI.new_report),
    ("13.Отчёт по продажам", InAppSales.new_report),
    ("14.Анализ взорванных элементов на уровне", ElementByLevel.new_report),
    ("15.DAU", DAU.new_report),
    ("16.MAU", MAU.new_report),
]

if __name__ == '__main__':
    #отчет для ручного исполнения
    reports.append(("n+1.Гипотезы по ретеншену", RetentionPatternHypothesis.new_report))
    Menu.menu_handsmode(reports)


#функции для бота
def get_menu():
    return Menu.get_menu(reports)

def get_reports_number():
    return len(reports)

def get_report_name(rep_num):
    return " ".join(reports[rep_num - 1][0].split(".")[1].split())

def get_settings_str(rep_num, defaults=None):
    return Menu.get_settings_str(reports, rep_num, defaults)


def get_defaults(rep_num):
    return Menu.get_defaults(reports, rep_num)


def parse_value(value, default, type):
    return Menu.parse_value(value, default, type)


def execute_report(user,rep_num, settings):
    return Menu.execute_report(reports, rep_num, settings,user)
