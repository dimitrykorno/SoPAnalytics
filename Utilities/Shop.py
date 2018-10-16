def get_price(coins, money="rub"):
    if coins == "100gold":
        if money == "rub":
            return 75
        else:
            return 0.99
    elif coins == "550gold":
        if money == "rub":
            return 459
        else:
            return 5.99
    elif coins == "1200gold":
        if money == "rub":
            return 999
        else:
            return 12.99
    elif coins == "2500gold":
        if money == "rub":
            return 1890
        else:
            return 24.99
    elif coins == "5300gold":
        if money == "rub":
            return 3790
        else:
            return 59.99
    elif coins == "11000gold":
        if money == "rub":
            return 7490
        else:
            return 99.99
    else:
        print("Unknown object:", coins)


def get_categories(in_app):
    return "Coins", None, None
