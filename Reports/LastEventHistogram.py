from report_api.CommonReports import LastEventHistogram
from report_api.Utilities.Utils import time_count
from sop_analytics.Data import Parse
import os


@time_count
def new_report(os_list=["iOS","Android"],
               app_version='7.0',
               users_limit=10000):
    dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)).replace("\\", "/")
    return LastEventHistogram.new_report(
        parser=Parse,
        app="sop",
        folder_dest=dir + "/Results/Гистограма последнего действия/",
        os_list=os_list,
        app_version=app_version,
        users_limit=users_limit)
