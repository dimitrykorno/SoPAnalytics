from Reports import M3LevelsFunnel, M3DetailedLevel, GlobalFunnel, UsersSessions, M3LevelBonuses, LastEventHistogram, \
    DetailedFunnel, LifetimeHistogram, ProgressHistogram, DustDynamics, AccumulativeROI, RetentionPatternHypothesis, \
    M3LevelsMonetization
import inspect

reports = {
    "1. Отчёт по качеству уровней": M3LevelsFunnel.new_report,
    "2. Подробный отчёт по уровню": M3DetailedLevel.new_report,
    "3. Глобальные отвалы": GlobalFunnel.new_report,
    "4. Порядок уровней в квесте перед отвалом": DetailedFunnel.new_report,
    "5. Использование бонусов по уровням": M3LevelBonuses.new_report,
    "6. Печать сессий": UsersSessions.new_report,
    "7. Гистограма последних событий": LastEventHistogram.new_report,
    "8. Гистограма лайфтайма": LifetimeHistogram.new_report,
    "9. Гистограма прогресса": ProgressHistogram.new_report,
    "10.Динамика пыли": DustDynamics.new_report,
    "11.Отчёт по трафику. Накопительный ROI": AccumulativeROI.new_report,
    "12.Гипотезы по ретеншену": RetentionPatternHypothesis.new_report,
    "13.Монетизация уровней": M3LevelsMonetization.new_report
}


def menu():
    while True:
        for rep in reports.keys():
            print(rep)
        print("Отчёт: ", end="")
        chosen_report = "999999"

        while not chosen_report.isdigit() or int(chosen_report) > len(reports.keys()) or int(chosen_report) == 0:
            chosen_report = input()

        settings = get_settings(list(reports.values())[int(chosen_report) - 1])
        # try:
        list(reports.values())[int(chosen_report) - 1](*settings)
        # except Exception as error:
        # print(error)
        # print(error.args)
        # continue


def get_settings(f):
    sig = inspect.signature(f)
    args = list(sig.parameters.keys())
    defaults = []
    types = []
    for arg in args:
        defaults.append(sig.parameters[arg].default)
        types.append(sig.parameters[arg].default.__class__)
    while True:
        string = ""
        for arg, default, i in zip(args, defaults, range(len(args))):
            full_default = default
            string += str(i) + ". " + str(arg) + ": " + str(
                full_default) + "\n"  # + str(types[i]) +str(full_default.__class__) + \

        string += str(len(args)) + ". Отчёт.\n"
        string += "Выбор: "

        input_args = input(string)
        while not input_args.isdigit() or int(input_args) > len(args):
            input_args = input()
        if int(input_args) == len(args):
            return defaults
        new_value = input(args[int(input_args)] + ": ")
        if types[int(input_args)] is int:
            new_value = int(new_value)
        elif types[int(input_args)] is bool:
            if new_value in ("True", "true", "1", "екгу", "Екгу"):
                new_value = True
            else:
                new_value = False
        if new_value in ("none", "None", "null"):
            new_value = None

        elif types[int(input_args)] is list:
            new_value = new_value.replace(" ", "").split(",")
        defaults[int(input_args)] = new_value
