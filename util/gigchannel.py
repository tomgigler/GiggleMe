#!/usr/bin/env python
import gigdb

channels = {}

class Channel:
    def __init__(self, id, guild_id, name):
        self.id = id
        self.guild_id = guild_id
        self.name = name
        self.save()

    def save(self):
        gigdb.save_channel(self.id, self.guild_id, self.name)

def load_channels():
    for row in gigdb.get_all("channels"):
        channels[row[0]] = Channel(row[0], row[1], row[2])
