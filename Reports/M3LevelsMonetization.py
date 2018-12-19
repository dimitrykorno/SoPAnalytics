from sop_analytics.Utilities.Quests import get_level_names
import pandas as pd
from sop_analytics.Classes.Events import *
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
from report_api.Report import Report
from report_api.Utilities.Utils import time_count,check_folder,check_arguments,try_save_writer
import os
app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def new_report(start=1,
                        quantity=200,
                        os_list=["iOS"],
                        period_start=None,
                        period_end=None,
                        min_version=None,
                        max_version=None,
                        countries_list=[]):
    errors = check_arguments(locals())
    result_files = []
    folder_dest = "Results/Монетизация уровней/"
    if hasattr(new_report,'user'):
        folder_dest+=str(new_report.user)+"/"
    check_folder(folder_dest)

    if errors:
        return errors, result_files

    levels = get_level_names(start, quantity)
    for os_str in os_list:
        # БАЗА ДАННЫХ
        Report.set_app_data(parser=Parse, user_class=User, event_class=Event,
                            os=os_str, app=app, user_status_check=True)

        Report.set_installs_data(additional_parameters=[],
                                 period_start=period_start,
                                 period_end=period_end,
                                 min_version=min_version,
                                 max_version=max_version,
                                 countries_list=countries_list)
        Report.set_events_data(additional_parameters=[],
                               period_start=period_start,
                               period_end=None,
                               min_version=None,
                               max_version=None,
                               events_list=[("Match3Events", "%BuyPremiumCoinM3%Success%")])

        parameters = ["Sum", "100 quant", "Money",
                      "550 quant", "Money",
                      "1200 quant", "Money",
                      "2500 quant", "Money",
                      "5300 quant", "Money",
                      "11000 quant", "Money"]
        countries = {}

        while Report.get_next_event():

            country = Report.current_user.country
            level = Report.current_event.level_num
            quant = Report.current_event.purchase[:-4] + " quant"
            money = Report.current_event.purchase[:-4] + " money"
            price = Report.current_event.price

            if country not in countries:
                countries[country] = {}

            if start <= int(level) <= (start + quantity - 1):
                if level not in countries[country]:
                    countries[country][level] = dict.fromkeys(parameters, 0)
                countries[country][level]["Sum"] += price
                countries[country][level][quant] += 1
                countries[country][level][money] += price

        filename=folder_dest+"Sales per lvl" + str(start) + "-" + str(start + quantity - 1) + " " + os_str + ".xlsx"
        writer = pd.ExcelWriter(filename)
        for country in countries:
            df = pd.DataFrame(index=levels,
                              columns=["Sum", "100 quant", "100 money",
                                       "550 quant", "550 money",
                                       "1200 quant", "1200 money",
                                       "2500 quant", "2500 money",
                                       "5300 quant", "5300 money",
                                       "11000 quant", "11000 money"])
            df = df.fillna(0)
            for level in levels:
                for param in parameters:
                    df.at[level, param] = countries[country][level][param]

            countries[country].to_excel(excel_writer=writer,
                                        sheet_name=country,
                                        header=["Sum", "100 quant", "Money",
                                                "550 quant", "Money",
                                                "1200 quant", "Money",
                                                "2500 quant", "Money",
                                                "5300 quant", "Money",
                                                "11000 quant", "Money"])
        try_save_writer(writer,filename)
        result_files.append(os.path.abspath(filename))
    return errors,result_files
