#!/usr/bin/env python

timezones = {}

class TimeZone:
    def __init__(self, offset, name):
        self.offset = offset
        self.name = name

def display_timezones(mention):
    output = "**Available Time Zones**\n**=============================**\n"
    for tz in timezones:
        offset = f"{timezones[tz].offset}"
        if timezones[tz].offset > 0:
            offset = "+" + offset
        output += f"**{tz}**  -  {timezones[tz].name}  -  UTC {offset}\n"
    output += f"\nDon't see your time zone?  DM **{mention}** and ask me to add it!"

    return output
