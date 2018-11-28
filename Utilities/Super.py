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
        super_token=super_token.lower()
        if super_token == "Super_SmallLightning_h".lower():
            return Supers.SmallLightning_h
        elif super_token == "Super_SmallLightning_v".lower():
            return Supers.SmallLightning_v
        elif super_token == "Super_FireSpark".lower():
            return Supers.FireSpark
        elif super_token == "Super_FireRing".lower():
            return Supers.FireRing
        elif super_token == "Super_BigLightning_h".lower():
            return Supers.BigLightning_h
        elif super_token == "Super_BigLightning_v".lower():
            return Supers.BigLightning_v
        elif super_token == "Super_SphereOfFire".lower():
            return Supers.SphereOfFire
        elif super_token == "Super_TwoStarBonus".lower():
            return Supers.TwoStarBonus
        elif super_token == "StarBonus".lower():
            return Supers.StarBonus
        else:
            # print("Unknown super token", super_token)
            return
