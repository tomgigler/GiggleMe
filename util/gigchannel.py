#!/usr/bin/env python
import gigdb

channels = {}

class Channel:
    def __init__(self, id, guild_id, name, channel_type=0, token_key=None, token_secret=None):
        self.id = id
        self.guild_id = guild_id
        self.name = name
        self.channel_type = channel_type
        self.token_key = token_key
        self.token_secret = token_secret
        self.save()

    def save(self):
        gigdb.save_channel(self.id, self.guild_id, self.name, self.channel_type, self.token_key, self.token_secret)

def load_channels():
    for row in gigdb.get_all("channels"):
        channels[row[0]] = Channel(row[0], row[1], row[2], row[3], row[4], row[5])
