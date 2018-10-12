def get_tutorial_name(tutorial_code):
    if tutorial_code in tutorials.keys():
        return tutorials[tutorial_code]
    else:
        print("Unknown tutorial:", tutorial_code)
        return


tutorials = {
    "Tutorial01": "Coins",
    "Tutorial02": "EnterName",
    "Tutorial03": "Puzzle",
    "Tutorial04": "GoddessHide",
    "Tutorial05": "Dust",
    "Tutorial06": "Decoration",
    "Tutorial07": "Prestige",
    "Tutorial08": "Watermill",
    "Tutorial09": "Digging",
    "Tutorial15": "Restavration"
}
