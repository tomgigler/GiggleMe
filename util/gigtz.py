#!/usr/bin/env python
from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta
from time import time
import gigdb

timezones = {}

class TimeZone:
    def __init__(self, id, name):
        self.id = id
        self.name = name

def display_timezones(mention):
    output = "**Available Time Zones**\n**=============================**\n"
    for tz in timezones:
        output += f"{timezones[tz].name}\n"
    output += f"\nDon't see your time zone?  DM **{mention}** and ask me to add it!"
    return output

def local_time_str_to_utc(time_str, tz_id):
    tz = timezone(timezones[tz_id].name)
    try:
        dt = tz.localize(datetime.strptime(time_str, '%Y-%m-%d %H:%M'))
    except:
        dt = tz.localize(datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
    return dt.timestamp()

def display_localized_time(time, tz_id):
    tz = timezone(timezones[tz_id].name)
    return datetime.fromtimestamp(time).astimezone(tz).strftime('%-I:%M:%S %p %a %b %d, %Y %Z')

def load_timezones():
    mydb = gigdb.db_connect()

    mycursor = mydb.cursor()

    mycursor.execute("select * from timezones order by name")
    for tz in mycursor.fetchall():
        timezones[tz[0]] = TimeZone(tz[0], tz[1])

    mycursor.close()
    mydb.disconnect()

def add_hours(time, num, tz_id):
    tz = timezone(timezones[tz_id].name)
    from_dt = datetime.fromtimestamp(time)
    to_dt = datetime.fromtimestamp(time) + relativedelta(hours=+num)
    time = to_dt.timestamp()
    if not from_dt.astimezone(tz).dst() and to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=-1)
    elif from_dt.astimezone(tz).dst() and not to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=+1)
    else:
        to_dt = datetime.fromtimestamp(time)
    return to_dt.timestamp()

def add_day(time, tz_id):
    tz = timezone(timezones[tz_id].name)
    from_dt = datetime.fromtimestamp(time)
    to_dt = datetime.fromtimestamp(time) + relativedelta(days=+1)
    time = to_dt.timestamp()
    if not from_dt.astimezone(tz).dst() and to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=-1)
    elif from_dt.astimezone(tz).dst() and not to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=+1)
    else:
        to_dt = datetime.fromtimestamp(time)
    return to_dt.timestamp()

def add_week(time, tz_id):
    tz = timezone(timezones[tz_id].name)
    from_dt = datetime.fromtimestamp(time)
    to_dt = datetime.fromtimestamp(time) + relativedelta(weeks=+1)
    time = to_dt.timestamp()
    if not from_dt.astimezone(tz).dst() and to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=-1)
    elif from_dt.astimezone(tz).dst() and not to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=+1)
    else:
        to_dt = datetime.fromtimestamp(time)
    return to_dt.timestamp()

def add_month(time, tz_id):
    tz = timezone(timezones[tz_id].name)
    from_dt = datetime.fromtimestamp(time)
    to_dt = datetime.fromtimestamp(time) + relativedelta(months=+1)
    time = to_dt.timestamp()
    if not from_dt.astimezone(tz).dst() and to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=-1)
    elif from_dt.astimezone(tz).dst() and not to_dt.astimezone(tz).dst():
        to_dt = datetime.fromtimestamp(time) + relativedelta(hours=+1)
    else:
        to_dt = datetime.fromtimestamp(time)
    return to_dt.timestamp()

def get_current_year(tz_id):
    tz = timezone(timezones[tz_id].name)
    return datetime.fromtimestamp(time()).astimezone(tz).strftime('%Y')
