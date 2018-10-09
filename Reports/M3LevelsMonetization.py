from report_api.Utilities.Utils import time_count
from Utilities.Quests import get_level_names
from Utilities.Shop import *
import pandas as pd
from Classes.Events import *
from Data import Parse
from Classes.User import User
from report_api.Report import Report
from datetime import datetime

app = "sop"


@time_count
def new_report(start=1,
               quantity=200,
               os_list=["iOS"],
               period_start=None,
               period_end=None,
               min_version=None,
               max_version=None):
    # Приводим границы периода к виду datetime.date
    if isinstance(period_start, str):
        period_start = datetime.datetime.strptime(period_start, "%Y-%m-%d").date()
    if isinstance(period_end, str):
        period_end = datetime.datetime.strptime(period_end, "%Y-%m-%d").date()

    for os_str in os_list:
        Report.set_app_data(parser=Parse, event_class=Event, user_class=User, os=os_str, app=app,
                            user_status_check=False)
        Report.set_installs_data(additional_parameters=None,
                                 period_start=period_start,
                                 period_end=period_end,
                                 min_version=min_version,
                                 max_version=max_version,
                                 countries_list=[])

        Report.set_events_data(additional_parameters=None,
                               period_start=period_start,
                               period_end=str(datetime.now().date()),
                               min_version=min_version,
                               max_version=max_version,
                               countries_list=[],
                               events_list=[("Match3Events", "%BuyPremiumCoinM3%Success%")])

        levels = get_level_names(start, quantity)

        countries = {}
        while Report.get_next_event():

            country = Report.current_user.country
            if country not in countries.keys():
                countries[country] = pd.DataFrame(index=levels,
                                                  columns=["Sum", "100 quant", "100 money",
                                                           "550 quant", "550 money",
                                                           "1200 quant", "1200 money",
                                                           "2500 quant", "2500 money",
                                                           "5300 quant", "5300 money",
                                                           "11000 quant", "11000 money"])
                countries[country] = countries[country].fillna(0)

            if isinstance(Report.current_event, Match3BuyPremiumCoin):
                quant = Report.current_event.purchase[:-4] + " quant"
                money = Report.current_event.purchase[:-4] + " money"
                price = get_price(Report.current_event.purchase, "rub")

                if start <= int(Report.current_event.level_num) <= (start + quantity - 1):
                    countries[country].at[Report.current_event.level_num, "Sum"] += price
                    countries[country].at[Report.current_event.level_num, quant] += 1
                    countries[country].at[Report.current_event.level_num, money] += price
                else:
                    print("Есть монетизированные уровни дальше: ", Report.current_event.level_num)

        writer = pd.ExcelWriter(
            "Levels Money/Sales " + os_str + " " + str(start) + "-" + str(start + quantity - 1) + ".xlsx")
        for country in countries:
            countries[country].to_excel(writer, sheet_name=country)
        writer.save()
