
# סנכרון Garmin - בטוח, עם tokens/ לא ב-git
import os
from linker import align_to_idt

def sync():
    print("Garmin sync: fetching last activities, linking to whoop via linker.get_whoop_for_date")
    # garminconnect + garth logic here
