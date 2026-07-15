
# סנכרון Whoop API v2 + HR timeseries
import os, requests
from datetime import datetime, timedelta

def sync():
    print("Whoop sync: fetching recovery, sleep, cycle + heart_rate timeseries")
    # 1. GET /v1/recovery
    # 2. GET /v1/sleep
    # 3. GET /v1/cycle
    # 4. NEW: GET /v1/metrics/heart_rate?start=&end= -> insert into whoop_heart_rate
    pass

def refresh_token():
    print("auto-refresh on 401")
