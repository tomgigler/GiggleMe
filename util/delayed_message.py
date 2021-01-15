#!/usr/bin/env python
import discord
from hashlib import md5
import gigdb

class DelayedMessage:
    def __init__(self, id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, description, content):
        self.id = id
        self.guild_id = guild_id
        self.delivery_channel_id = delivery_channel_id
        self.delivery_time = delivery_time
        self.author_id = author_id
        self.repeat = repeat
        self.last_repeat_message = last_repeat_message
        self.description = description
        self.content = content

    def guild(self, client):
        return discord.utils.get(client.guilds, id=self.guild_id)

    def delivery_channel(self, client):
        guild = discord.utils.get(client.guilds, id=self.guild_id)
        return discord.utils.get(self.guild(client).text_channels, id=self.delivery_channel_id)

    def author(self, client):
        return client.get_user(self.author_id)

    @staticmethod
    def id_gen(id):
        return md5((str(id)).encode('utf-8')).hexdigest()[:8]

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, self.delivery_time, self.author_id, self.repeat, self.last_repeat_message, self.content, self.description)

    def delete_from_db(self):
        gigdb.delete_message(self.id)
