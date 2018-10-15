from Utilities.Quests import get_level_names
import pandas as pd
from Classes.Events import *
from report_api.OS import OS
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime
from report_api.Utilities.Utils import time_count, outliers_iqr

app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
@time_count
def levels_monetization(start=1,
                        quantity=200,
                        os_list=["iOS"],
                        period_start=None,
                        period_end=None,
                        min_version=None,
                        max_version=None,
                        countries_list=[]):

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

        if country not in countries.keys():
            countries[country] = {}

        if start <= int(level) <= (start + quantity - 1):
            if level not in countries[country].keys():
                countries[country][level] = dict.fromkeys(parameters, 0)
            countries[country][level]["Sum"] += price
            countries[country][level][quant] += 1
            countries[country][level][money] += price

    writer = pd.ExcelWriter("Sales " + str(start) + "-" + str(start + quantity - 1) + " " + os_str + ".xlsx")
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
    writer.save()
