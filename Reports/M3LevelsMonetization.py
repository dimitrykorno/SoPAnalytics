from Data import Data, Parse
from Utilities.Utils import *
from Utilities.Shop import *
import pandas as pd


def levels_monetization(start, quantity):
    sql = """
    SELECT ios_ifv, event_name, event_json, country_iso_code, event_datetime
    FROM sop_events.events_ios
    WHERE event_name = "Match3Events" and event_json like "%BuyPremiumCoinM3%Success%"
    order by ios_ifv, event_datetime
    """
    events, db = Data.get_data(sql=sql)

    levels = get_level_names(start, quantity)
    countries = {}

    event_data = events.fetch_row(maxrows=1, how=1)[0]
    while event_data:
        buy_event = Parse.parse_event(
            event_name=event_data["event_name"],
            event_json=event_data["event_json"]
        )

        country = event_data["country_iso_code"]
        if country not in countries.keys():
            countries[country] = create_df(levels)
        df = countries[country]

        if buy_event:
            quant = buy_event.purchase[:-4] + " quant"
            money = buy_event.purchase[:-4] + " money"
            price = get_price(buy_event.purchase, "rub")

            if start <= int(buy_event.level_num) <= (start + quantity - 1):
                print(event_data["ios_ifv"], event_data["event_datetime"], buy_event.level_num, country,
                      buy_event.purchase)
                df.loc[buy_event.level_num]["Sum"] += price
                df.loc[buy_event.level_num][quant] += 1
                df.loc[buy_event.level_num][money] += price
            else:
                print("Есть монетизированные уровни дальше",start+quantity-1)

        event_data = events.fetch_row(maxrows=1, how=1)
        if event_data:
            event_data = event_data[0]
        else:
            db.close()

   # print(countries["RU"].to_string())

    writer = pd.ExcelWriter("Sales " + str(start) + "-" + str(start + quantity - 1) + ".xlsx")
    for country in countries:
        countries[country].to_excel(excel_writer=writer,
                    sheet_name=country,
                    header=["Sum", "100 quant", "Money",
                             "550 quant", "Money",
                             "1200 quant", "Money",
                             "2500 quant", "Money",
                             "5300 quant", "Money",
                             "11000 quant", "Money"])
    writer.save()


def create_df(levels):
    df = pd.DataFrame(index=levels,
                      columns=["Sum", "100 quant", "100 money",
                               "550 quant", "550 money",
                               "1200 quant", "1200 money",
                               "2500 quant", "2500 money",
                               "5300 quant", "5300 money",
                               "11000 quant", "11000 money"])
    df = df.fillna(0)
    return df
