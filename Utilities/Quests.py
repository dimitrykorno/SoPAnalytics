# список локаций/квестов/уровней
loc_quest_level = {

    "loc00": {"q00": ["0001"],
              "q01": ["0002"],
              "q02": ["0003"],
              "q03": ["0004", "0005"],
              "q04": ["0006", "0007"],
              },

    "loc01": {"q00": ["0008"],
              "q01": ["0009"],
              "q02": ["0010", "0011"],
              "q03": ["0012", "0013", "0014"],
              "q04": ["0015"],
              "q05": ["0016", "0017"],
              "q06": ["0018", "0019", "0020"],
              "q07": ["0021", "0022", "0023"],
              "q08": ["0024", "0025", "0026"],
              "q09": ["0027"],
              "q10": ["0028", "0029", "0030"],
              "q11": ["0031", "0032"],
              "q12": ["0033", "0034", "0035"],
              "q13": ["0036"],
              "q14": ["0037", "0038", "0039"],
              },

    "loc02": {"q00": ["0040", "0041"],
              "q01": ["0042", "0043"],
              "q02": ["0044", "0045", "0046", "0047"],
              "q03": ["0048", "0049"],
              "q04": ["0050", "0051", "0052", "0053"],
              "q05": ["0054", "0055"],
              "q06": ["0056", "0057"],
              "q07": ["0058", "0059", "0060"],
              "q08": ["0061", "0062", "0063"],
              "q09": ["0064", "0065", "0066"],
              "q10": ["0067", "0068", "0069"],
              "q11": ["0070", "0071", "0072"],
              "q12": ["0073", "0074", "0075", "0076"],
              "q13": ["0077", "0078"],
              "q14": ["0079", "0080", "0081", "0082"],
              "q15": ["0083", "0084", "0085"],
              "q16": ["0086", "0087"],
              "q17": ["0088", "0089", "0090"],
              "q18": ["0091", "0092", "0093"],
              "q19": ["0094", "0095", "0096"],
              "q20": ["0097", "0098", "0099", "0100"],
              "q21": ["0101", "0102", "0103", "0104"],
              "q22": ["0105", "0106", "0107"],
              "q23": ["0108", "0109", "0110"]
              },
    "loc03": {"q00": ["0111", "0112", "0113"],
              "q01": ["0114", "0115"],
              "q02": ["0116", "0117", "0118"],
              "q03": ["0119", "0120", "0121", "0122"],
              "q04": ["0123", "0124"],
              "q05": ["0125", "0126", "0127", "0128"],
              "q06": ["0129", "0130", "0131"],
              "q07": ["0132", "0133", "0134"],
              "q08": ["0135", "0136"],
              "q09": ["0137", "0138", "0139"],
              "q10": ["0140", "0141", "0142"],
              "q11": ["0143", "0144", "0145", "0146"],
              "q12": ["0147", "0148", "0149"],
              "q13": ["0150", "0151", "0152"],
              "q14": ["0153", "0154", "0155"],
              "q15": ["0156", "0157"],
              "q16": ["0158", "0159", "0160", "0161"],
              "q17": ["0162", "0163", "0164"],
              "q18": ["0165", "0166", "0167"],
              "q19": ["0168", "0169", "0170"],
              "q20": ["0171", "0172"],
              "q21": ["0173", "0174", "0175"],
              "q22": ["0176", "0177", "0178", "0179"],
              "q23": ["0180", "0181", "0182"],
              "q24": ["0183", "0184", "0185", "0186"],
              "q25": ["0187", "0188"],
              "q26": ["0189", "0190", "0191", "0192"],
              "q27": ["0193", "0194"],
              "q28": ["0195", "0196", "0197", "0198"],
              "q29": ["0199", "0200"]
              },
    "fin00": {"q00": ["9001", "9002", "9003", "9004", "9005", "9006"],
              "q01": ["9007", "9008", "9009", "9010", "9011", "9012"],
              "q02": ["9013", "9014", "9015", "9016", "9017", "9018"],
              },

}
paywall_levels = [
    "0023", "0030", "0035", "0043", "0056", "0067", "0080", "0083", "0088", "0092", "0096", "0100", "0104", "0108",
    "0110", "0114", "0118", "0122", "0126", "0130", "0135", "0139", "0143", "0147", "0151", "0155", "0160", "0164",
    "0168", "0172", "0176", "0180", "0185"]

original_tutorial_order = ["Take loc00q01", "Complete loc00q01", "Start  Tutorial15", "Finish Tutorial15",
                           "Take loc00q03", "Complete loc00q03", "Start  Tutorial01", "Finish Tutorial01",
                           "Take loc00q04", "Complete loc00q04", "Start  Tutorial02", "Finish Tutorial02",
                           "Take loc01q00", "Complete loc01q00", "Start  Tutorial03", "Finish Tutorial03",
                           "Start  Tutorial04", "Finish Tutorial04",
                           "Take loc01q03", "Complete loc01q03", "Start  Tutorial05", "Finish Tutorial05",
                           "Start  Tutorial06", "Finish Tutorial06",
                           "Start  Tutorial07", "Finish Tutorial07",
                           "Take loc01q10", "Complete loc01q10", "Start  Tutorial08", "Finish Tutorial08",
                           "Take loc01q14", "Complete loc01q14", "Start  Tutorial09", "Finish Tutorial09"]


def get_locquest(level_num):
    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            if level_num in loc_quest_level[loc][quest]:
                return loc + quest
    print("Уровня нет в списке:", level_num)


def get_last_loc_quest(level_or_quest):
    """
    Возвращает номер последнего квеста.
    Если передан номер уровня - номер текущего квеста.
    Если передан номер квеста - номер предыдущего квеста.
    :param level_or_quest: номер уровня или квеста
    :return: номер последнего квеста
    """
    previous_quest = "loc00q00"
    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            if level_or_quest == loc + quest:
                return previous_quest
            for level in loc_quest_level[loc][quest]:
                if level == level_or_quest:
                    return loc + quest
            previous_quest = loc + quest


def get_completed_locquests(finished_levels):
    result_list = []
    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            passed = True
            for level in loc_quest_level[loc][quest]:
                if level not in finished_levels:
                    passed = False
            if passed:
                result_list.append(loc + quest)
    return result_list


def get_levels_list(locquest=True, fail=False, tutorial=True, tutorial_order=original_tutorial_order, level=True):
    print("tutor list", tutorial_order)
    result_list = []
    if tutorial:
        index = 0
        while "Tutorial" in tutorial_order[index]:
            result_list.append(tutorial_order[index])
            index += 1

    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            if locquest:
                result_list.append("Start  " + loc + quest)
            if tutorial:
                if "Take " + loc + quest in tutorial_order:
                    index = tutorial_order.index("Take " + loc + quest)
                    while index + 1 < len(tutorial_order) and "Tutorial" in tutorial_order[index + 1]:
                        result_list.append(tutorial_order[index + 1])
                        index += 1

            for lvl in loc_quest_level[loc][quest]:
                if level:
                    result_list.append("Start  " + lvl)
                if fail:
                    result_list.append("Fail   " + lvl)
                if level:
                    result_list.append("Finish " + lvl)

            if locquest:
                result_list.append("Finish " + loc + quest)

            if tutorial:
                if "Complete " + loc + quest in tutorial_order:
                    index = tutorial_order.index("Complete " + loc + quest)
                    while index + 1 < len(tutorial_order) and "Tutorial" in tutorial_order[index + 1]:
                        result_list.append(tutorial_order[index + 1])
                        index += 1

    return result_list


def get_levels():
    list = []
    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            for level in loc_quest_level[loc][quest]:
                list.append(level)
    return list


def get_locquests_list():
    list = []
    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            list.append(loc + quest)
    return list


def get_level_names(start, quantity):
    return list((str(x).rjust(4, '0') for x in range(start, start + quantity)))


def get_next_level(level_num):
    return str(int(level_num) + 1).rjust(4, '0')


def get_next_locquest(locquest):
    get_next = False
    for loc in loc_quest_level.keys():
        for quest in loc_quest_level[loc].keys():
            if get_next:
                return loc + quest
            if loc + quest == locquest:
                get_next = True
