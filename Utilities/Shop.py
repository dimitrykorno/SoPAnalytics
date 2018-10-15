def get_price(coins, money="rub"):
    if coins == "100gold":
        if money == "rub":
            return 75
    elif coins == "550gold":
        if money == "rub":
            return 459
    elif coins == "1200gold":
        if money == "rub":
            return 999
    elif coins == "2500gold":
        if money == "rub":
            return 1890
    elif coins == "5300gold":
        if money == "rub":
            return 3790
    elif coins == "11000gold":
        if money == "rub":
            return 7490
    else:
        print("Unknown object:", coins)
