from report_api.Pattern import Pattern
from Classes.Events import *


class PatternBuyDecoration(Pattern):
    """
    Заготовленный шаблон для покупки декорации
    """

    # noinspection PyDefaultArgument
    def __init__(self, completed_once=False, min_completions=0, max_completions=None,
                 pattern_parameters=[None], same_day_pattern=True, same_session_pattern=False):
        super().__init__(completed_once=completed_once,
                         min_completions=min_completions,
                         max_completions=max_completions,
                         pattern_parameters=pattern_parameters,
                         same_day_pattern=same_day_pattern,
                         same_session_pattern=same_session_pattern)

        self.pattern = [CityEventsBuyDecoration]
        if completed_once:
            self.name = "2)Построили одну декорацию"
        elif max_completions == 0:
            self.name = "3)Построили ноль декораций"
        else:
            self.name = "1)Построили неск декораций"
        Pattern.filename = "BuyDecoration"


class PatternBuyHealth(Pattern):
    """
    Заготовленный шаблон для покупки декорации
    """

    # noinspection PyDefaultArgument
    def __init__(self, completed_once=False, min_completions=0, max_completions=None,
                 pattern_parameters=[None], same_day_pattern=True, same_session_pattern=False):
        super().__init__(completed_once=completed_once,
                         min_completions=min_completions,
                         max_completions=max_completions,
                         pattern_parameters=pattern_parameters,
                         same_day_pattern=same_day_pattern,
                         same_session_pattern=same_session_pattern)

        self.pattern = [CityEventsBuyHealth]
        self.parameters += [None] * (len(self.pattern) - len(self.parameters))
        if completed_once:
            self.name = "2)Купили жизни один раз"
        elif max_completions == 0:
            self.name = "3)Не покупали жизни"
        else:
            self.name = "1)Купили жизни неск раз"
        Pattern.filename = "BuyHealth"


class PatternWinRow(Pattern):
    """
    Заготовленный шаблон для покупки декорации
    """

    # noinspection PyDefaultArgument
    def __init__(self, completed_once=False, min_completions=0, max_completions=None,
                 pattern_parameters=[None], same_day_pattern=True, same_session_pattern=True):
        super().__init__(completed_once=completed_once,
                         min_completions=min_completions,
                         max_completions=max_completions,
                         pattern_parameters=pattern_parameters,
                         same_day_pattern=same_day_pattern,
                         same_session_pattern=same_session_pattern)

        self.pattern = [Match3CompleteTargets, Match3CompleteTargets, Match3CompleteTargets, Match3CompleteTargets]
        self.parameters += [None] * (len(self.pattern) - len(self.parameters))
        self.breakers = [Match3FailGame]
        self.breakers_parameters = [None]
        if completed_once:
            self.name = "2)Одна серия побед"
        elif max_completions == 0:
            self.name = "3)Без серий побед "
        else:
            self.name = "1)Неск серий побед"
        Pattern.filename = "WinRow"
