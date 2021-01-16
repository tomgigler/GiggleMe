#!/usr/bin/env python
import discord
from hashlib import md5
from time import time
import gigdb
import giguser
import gigtz

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

    def get_show_output(self, msg_num, client, raw=False, show_id=False, guild_id=None):
        output = ""

        if show_id:
            output += f"> **ID:**  {self.id}\n"

        output += f"> **Author:**  {self.get_author(client).name}\n"
        output += f"> **Channel:**  {self.get_delivery_channel(client).name}\n"
        if self.delivery_time and self.delivery_time >= 0:
            output += f"> **Repeat:**  {self.repeat}\n"
        if self.repeat and self.last_repeat_message:
            try:
                output += f"> **Last Delivery:**  {self.get_delivery_channel(client).get_partial_message(self.last_repeat_message).jump_url}\n"
            except:
                pass

        if guild_id != self.guild_id:
            output += f"> **Deliver in:**  {self.get_guild(client).name}\n"
        if self.delivery_time and self.delivery_time >= 0:
            if round((self.delivery_time - time())/60, 1) < 0:
                output += f"> **Delivery failed:**  {str(round((self.delivery_time - time())/60, 1) * -1)} minutes ago\n"
            else:
                output += f"> **Deliver:**  {gigtz.display_localized_time(self.delivery_time, giguser.users[self.author_id].timezone, giguser.users[self.author_id].format_24)}\n"
        else:
            if self.delivery_time:
                output = "> **Proposal**\n" + output
            else:
                output = "> **Template**\n" + output
        output += f"> **Description:**  {self.description}\n"
        if self.delivery_time and self.delivery_time < 0:
            output += f"> **Current Votes:**  3\n"
        if raw:
            return output + "```\n" + self.content + "\n```"
        else:
            return output + self.content
