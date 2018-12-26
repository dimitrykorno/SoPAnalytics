from datetime import datetime, timedelta
import pandas as pd
import os
from report_api.Classes.QueryHandler import QueryHandler
from report_api.Data import Data
from report_api.OS import OS
from report_api.Utilities.Utils import check_folder, draw_plot, try_save_writer, check_arguments, test_devices_ios, \
    test_devices_android


app = "sop"


# noinspection PyDefaultArgument,PyDefaultArgument
def new_report(
        os_list=["iOS", "Android"],
        period_start="2018-11-15",
        period_end=None,
        min_version=None,
        max_version=None,
        countries_list=[]
):
    """
    Расчет накопительного ARPU и ROI по паблишерам и трекинговым ссылкам(источникам)

    :param os_list:
    :param min_version:
    :param max_version:
    :param countries_list:
    :param period_start: начало периода
    :param period_end: конец периода
    :param days_since_install: рассчитное кол-во дней после установки

    :return:
    """
    errors = check_arguments(locals())
    result_files = []
    folder_dest = "Results/Покупка пыли/"
    check_folder(folder_dest)
    if hasattr(new_report, 'user'):
        folder_dest += str(new_report.user) + "/"
    check_folder(folder_dest)

    if errors:
        return errors, result_files

    if not period_start:
        period_start = "2018-06-15"
    # Приводим границы периода к виду datetime.date
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()
    if period_end:
        if isinstance(period_end, str):
            period_end = datetime.strptime(period_end, "%Y-%m-%d").date()
    else:
        period_end = datetime.now().date()
    period_range = [str(period_start + timedelta(days=i)) for i in range((period_end - period_start).days)]

    base_title_NoDust = " NoDustWindow " + str(period_start) + "-" + str(period_end)
    base_title_BuyDust = " BuyDust " + str(period_start) + "-" + str(period_end)

    for os_str in os_list:
        for event in ["BuyNoDustWindow", "BuyDust"]:
            # составляем строку с условиями выборки для SQL запроса
            title = os_str + " " + event + str(period_start) + "-" + str(period_end)
            where_line = QueryHandler.where_line(period_start=period_start, period_end=period_end,
                                                 min_app_version=min_version, max_app_version=max_version,
                                                 os_str=os_str)
            aid = OS.get_aid(os_str)
            u_id = OS.get_id(os_str)
            if os_str.lower() == "ios":
                testers = "','".join(test_devices_ios)
            else:
                testers = ",".join(test_devices_android)

            sql = """
                SELECT date(event_datetime) as date , COUNT(*) as {2}
                {0}
                {1} 
                and event_json like "%{2}%success%"
                and {3} not in ('{5}')
                and {4} not in ('{5}')
                group by date(event_datetime)
                order by date(event_datetime)
                """.format(QueryHandler.get_db_name(os_str.lower(), app), where_line, event,
                           aid, u_id, testers)
            print(sql)
            result, db = Data.get_data(sql, app, by_row=False, name="Рассчет покупки пыли из окна " + event + ".")
            db.close()
            if result:
                y = [0] * len(period_range)
                for r in result:
                    y[period_range.index(str(r["date"]))] = r[event]

                pl = draw_plot(range(len(period_range)), {event: y}, x_ticks_labels=period_range, show=True,
                               folder=folder_dest,
                               title=title, calculate_sum=True, plot_type="bar")
                df = pd.DataFrame(index=period_range, columns=["NoDustWindow purchases"])
                df["NoDustWindow purchases"] = y
                filename = folder_dest + title + ".xlsx"
                writer = pd.ExcelWriter(filename)
                df.to_excel(writer)
                try_save_writer(writer, filename)
                result_files.append(os.path.abspath(filename))
                result_files += pl
            else:
                errors += os_str + " не найдены покупки из окна 'нет пыли'\n"

    return errors, result_files
