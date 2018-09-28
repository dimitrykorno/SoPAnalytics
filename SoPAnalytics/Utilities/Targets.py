from enum import Enum

targets_set = (
    "Ballon", "Box_Level1", "Carpet_Level1", "Box_Level2", "Box_Level3", "Carpet_Level2", "Stone", "Unicorn", "Weight",
    "LightStar", "Chain_Level1", "Granite_Level1", "Granite_Level2", "Ice_Level1", "Ice_Level2")


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
