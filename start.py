from report_api.Menu import menu
from Reports import M3LevelsFunnel, M3DetailedLevel, GlobalFunnel, UsersSessions, M3LevelBonuses, LastEventHistogram, \
    DetailedFunnel, LifetimeHistogram, ProgressHistogram, DustDynamics, CumulativeROI, RetentionPatternHypothesis, \
    InAppSales, ElementByLevel, DAU, MAU

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
        ("11.Накопительный ROI", CumulativeROI.new_report),
        ("12.Гипотезы по ретеншену", RetentionPatternHypothesis.new_report),
        ("13.Отчёт по продажам", InAppSales.new_report),
        ("14.Анализ взорванных элементов на уровне", ElementByLevel.new_report),
        ("15.DAU", DAU.new_report),
        ("16.MAU", MAU.new_report)
    ]

def show_menu():
    menu(reports)

def menu_to_bot():
    return [rep[0] for rep in reports]