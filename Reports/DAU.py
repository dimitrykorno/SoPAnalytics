from report_api.CommonReports import DAU
from report_api.Utilities.Utils import time_count
import os


@time_count
def new_report(os_list=["iOS"],
               period_start="2018-10-01",
               period_end=None,
               min_version=None,
               max_version=None,
               countries_list=[]):
    dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)).replace("\\", "/")
    events_list = [("CityEvent", "%InitGameState%")]
    return DAU.new_report( app="sop",
                             folder_dest=dir + "/Results/DAU/",
                             events_list=events_list,
                             os_list=os_list,
                             period_start=period_start,
                             period_end=period_end,
                             min_version=min_version,
                             max_version=max_version,
                             countries_list=countries_list)
