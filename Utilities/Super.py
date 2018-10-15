from enum import Enum

supers_set = (
    "Super_SmallLightning_h", "Super_SmallLightning_v", "Super_FireSpark", "Super_FireRing", "Super_BigLightning_h",
    "Super_BigLightning_v", "Super_SphereOfFire", "Super_TwoStarBonus", "StarBonus")


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
            # print("Unknown super token", super_token)
            return
