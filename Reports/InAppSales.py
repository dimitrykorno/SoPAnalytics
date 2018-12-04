from report_api.CommonReports import InAppSales
from report_api.Utilities.Utils import time_count
from sop_analytics.Utilities import Shop
from sop_analytics.Data import Parse
from sop_analytics.Classes.User import User
import os

@time_count
def new_report(os_list=["iOS"],
               after_release_months_graphs=False,
               period_start="2018-08-19",
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)).replace("\\","/")
    events_list=[("Match3Events", "%BuyPremiumCoinM3%Success%")]
    InAppSales.new_report(shop=Shop,
                          parser=Parse,
                          user_class=User,
                          app="sop",
                          folder_dest=dir + "/Results/Продажи in-app'ов",
                          events_list=events_list,
                          os_list=os_list,
                          after_release_months_graphs=after_release_months_graphs,
                          period_start=period_start,
                          period_end=period_end,
                          min_version=min_version,
                          max_version=max_version,
                          countries_list=countries_list)
