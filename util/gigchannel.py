#!/usr/bin/env python
from twitter import Api
import asyncio
import settings
import gigdb

channels = {}

class Channel:
    def __init__(self, id, guild_id, name, channel_type=1, token_key=None, token_secret=None, user_id=None, screen_name=None):
        self.id = id
        self.guild_id = guild_id
        self.name = name
        self.channel_type = channel_type
        self.token_key = token_key
        self.token_secret = token_secret
        self.user_id = user_id
        self.screen_name = screen_name
        self.mention = f"{self.name} : <https://www.twitter.com/{self.screen_name}>"
        self.save()

    def save(self):
        gigdb.save_channel(self.id, self.guild_id, self.name, self.channel_type, self.token_key, self.token_secret, self.user_id, self.screen_name)

    async def send(self, content):
        if self.channel_type == 2:
            api = Api(
                consumer_key=settings.twitter_consumer_key,
                consumer_secret=settings.twitter_consumer_secret,
                access_token_key=self.token_key,
                access_token_secret=self.token_secret)

            status = api.PostUpdate(content)

        return None

def load_channels():
    for row in gigdb.get_all("channels"):
        channels[row[0]] = Channel(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
