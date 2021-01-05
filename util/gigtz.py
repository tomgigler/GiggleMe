#!/usr/bin/env python
from datetime import datetime
from pytz import timezone
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
    tz = timezone(timezones[tz_id])
    try:
        dt = pacific_tz.localize(datetime.strptime(time_str, '%Y-%m-%d %H:%M'))
    except:
        dt = pacific_tz.localize(datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
    return dt.timestamp()

def display_localized_time(time, tz_id):
    tz = timezone(timezones[tz_id])
    dt = tz.localize(datetime.fromtimestamp(time))
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

def load_timezones():
    mydb = gigdb.db_connect()

    mycursor = mydb.cursor()

    mycursor.execute("select * from timezones")
    for tz in mycursor.fetchall():
        timezones[tz[0]] = TimeZone(tz[0], tz[1])

    mycursor.close()
    mydb.disconnect()

