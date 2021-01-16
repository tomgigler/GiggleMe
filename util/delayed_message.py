#!/usr/bin/env python
import discord
from hashlib import md5
from time import time
import gigdb

class DelayedMessage:
    def __init__(self, id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, content, description):
        if id is None:
            id = md5((str(time()).encode('utf-8'))).hexdigest()[:8]
        self.id = id
        self.guild_id = guild_id
        self.delivery_channel_id = delivery_channel_id
        self.delivery_time = delivery_time
        self.author_id = author_id
        self.repeat = repeat
        self.last_repeat_message = last_repeat_message
        self.description = description
        self.content = content
        self.update_db()

    def get_guild(self, client):
        return discord.utils.get(client.guilds, id=self.guild_id)

    def get_delivery_channel(self, client):
        return discord.utils.get(self.get_guild(client).text_channels, id=self.delivery_channel_id)

    def get_author(self, client):
        return client.get_user(self.author_id)

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, self.delivery_time, self.author_id, self.repeat, self.last_repeat_message, self.content, self.description)

    def delete_from_db(self):
        gigdb.delete_message(self.id)
