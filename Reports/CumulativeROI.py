from report_api.CommonReports import CumulativeROI
from report_api.Utilities.Utils import time_count
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
import os


@time_count
def new_report(os_list=["iOS"],
               days_since_install=250,
               period_start="2018-06-14",
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)).replace("\\", "/")
    events_list = [("CityEvent", ["%BuyPremiumCoin%Success%", "%InitGameState%"]),
                   ("Match3Events", "%BuyPremiumCoin%Success%")]
    CumulativeROI.new_report(parser=Parse,
                             user_class=User,
                             app="sop",
                             folder_dest=dir + "/Results/Отчёт по трафику/",
                             events_list=events_list,
                             os_list=os_list,
                             days_since_install=days_since_install,
                             period_start=period_start,
                             period_end=period_end,
                             min_version=min_version,
                             max_version=max_version,
                             countries_list=countries_list)
