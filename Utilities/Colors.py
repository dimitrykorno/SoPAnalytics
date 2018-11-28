from enum import Enum

colors_set = ("Color6_Blue", "Color6_Red", "Color6_Yellow", "Color6_Green", "Color6_Black", "Color6_White")


class Colors(Enum):
    Blue = 0,
    Red = 1,
    Yellow = 2,
    Green = 3,
    Black = 4,
    White = 5

    @staticmethod
    def get_color(color):
        color=color.lower()
        if color == "Color6_Blue".lower():
            return Colors.Blue
        elif color == "Color6_Red".lower():
            return Colors.Red
        elif color == "Color6_Yellow".lower():
            return Colors.Yellow
        elif color == "Color6_Green".lower():
            return Colors.Green
        elif color == "Color6_Black".lower():
            return Colors.Black
        elif color == "Color6_White".lower():
            return Colors.White
        else:
            # print("Unknown color", color)
            return
