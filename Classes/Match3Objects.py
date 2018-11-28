class Target:
    __slots__ = {'target_count', 'target', 'overflow_target_cunt'}

    def __init__(self, target_count, target, overflow_target_count):
        self.target_count = target_count
        self.target = target
        self.overflow_target_cunt = overflow_target_count

    def to_string(self):
        info = "Target: " + str(self.target) + ", Count: " + str(self.target_count) + ", Overflow count: " + str(
            self.overflow_target_cunt)
        return info


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


class Elements:
    def __init__(self, colors_count, super_count, targets_count, others_count):
        self.colors_count = colors_count
        self.super_count = super_count
        self.targets_count = targets_count
        self.others_count = others_count

    def get_element_count(self,element):
        for group in (self.colors_count,self.super_count,self.targets_count,self.others_count):
            if element in group:
               return group[element]
        return 0

    def to_string(self):

        info = "Targets: "
        for key, value in self.targets_count.items():
            info += str(key) + ": " + str(value) + " "

        info += "\n                    Supers: "
        for key, value in self.super_count.items():
            info += str(key) + ": " + str(value) + " "

        info += "\n                    Colors: "
        for key, value in self.colors_count.items():
            info += str(key) + ": " + str(value) + " "

        return info
