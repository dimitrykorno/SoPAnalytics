from Data import Data, Parse
import pandas as pd
from Classes.Events import *
import datetime


def time_between():
    sql = """
    SELECT ios_ifv, event_name, event_json, event_datetime
    FROM sop_events.events_ios
    WHERE event_name = "CityEvent" and (event_json like "%UpdateBuilding%" or event_json like "%Button%Play%")
    AND app_version_name>="4.6"
    order by ios_ifv, event_datetime
    """
    events, db = Data.get_data(sql=sql)
    event_data = events.fetch_row(maxrows=1, how=1)[0]
    previus_user = event_data["ios_ifv"]
    previus_event = None

    build_tavern = None
    start_game = None

    df_char = pd.DataFrame(index=list(range(201)), columns=["Events"])
    df_play = pd.DataFrame(index=list(range(201)), columns=["Events"])
    df_char = df_char.fillna(0)
    df_play = df_play.fillna(0)

    users=1
    users_builded_tavern=0
    users_played_after_tavern=0

    while event_data:
        current_event = Parse.parse_event(
            event_name=event_data["event_name"],
            event_json=event_data["event_json"]
        )
        current_user = event_data["ios_ifv"]

        # если новый пользователь, сливаем данные старого в таблицу и обнуляем личные данные
        if current_user != previus_user:
            users+=1
            if start_game and build_tavern:
                time_between_events = start_game.date_time.timestamp() - build_tavern.date_time.timestamp()
                if time_between_events <= 200:
                    if start_game.action == "play":
                        df_play.loc[time_between_events, "Events"] += 1
                    elif start_game.action == "char":
                        df_char.loc[time_between_events, "Events"] += 1
                else:
                    print("Time spike:", time_between_events)

            build_tavern = None
            start_game = None

        # сначала всегда строительство, а потом игра. считаем только первые вхождения у пользователя
        if not build_tavern and \
                        current_event.__class__ is CityEventsUpdateBuilding and \
                        current_event.building == "b_tavern" and \
                        current_event.level == 1:
            build_tavern = current_event
            setattr(build_tavern, "date_time", event_data["event_datetime"])
            users_builded_tavern+=1
            #print(build_tavern.to_string(), build_tavern.date_time)

        elif (build_tavern and not start_game) and \
                        current_event.__class__ is CityEventsButtonPlay and \
                        current_event.quest == "loc00q02":
            start_game = current_event
            setattr(start_game,"date_time",event_data["event_datetime"])
            users_played_after_tavern+=1
            #print(start_game.to_string(), start_game.date_time, "\n")

        previus_user = current_user
        event_data = events.fetch_row(maxrows=1, how=1)
        if event_data:
            event_data = event_data[0]
        else:
            users += 1
            if start_game and build_tavern:
                time_between_events = start_game.date_time.timestamp() - build_tavern.date_time.timestamp()
                if time_between_events <= 200:
                    if start_game.action == "play":
                        df_play.loc[time_between_events, "Events"] += 1
                    elif start_game.action == "char":
                        df_char.loc[time_between_events, "Events"] += 1
                else:
                    print("Time spike:", time_between_events)
            db.close()

    writer = pd.ExcelWriter("Time between.xlsx")
    df_play.to_excel(excel_writer=writer,sheet_name="Play button")
    df_char.to_excel(excel_writer=writer, sheet_name="Character")
    writer.save()


    print("Users:",users)
    print("Users, who builded tavern:",users_builded_tavern)
    print("Users, who played after tavern:",users_played_after_tavern)


