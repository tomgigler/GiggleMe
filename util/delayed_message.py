#!/usr/bin/env python
import discord
import asyncio
from hashlib import md5
from time import time
import gigdb
import giguser
import gigtz
from gigvotes import votes

class DelayedMessage:
    def __init__(self, id, guild_id, delivery_channel_id, author_id, content, description):
        if id is None:
            id = md5((str(time()).encode('utf-8'))).hexdigest()[:8]
        self.id = id
        self.guild_id = guild_id
        self.delivery_channel_id = delivery_channel_id
        self.author_id = author_id
        self.description = description
        self.content = content

    def get_guild(self, client):
        return discord.utils.get(client.guilds, id=self.guild_id)

    def get_delivery_channel(self, client):
        return discord.utils.get(self.get_guild(client).text_channels, id=self.delivery_channel_id)

    def get_author(self, client):
        return client.get_user(self.author_id)

    def delete_from_db(self):
        gigdb.delete_message(self.id)

    def get_show_header(self, client, show_id=False, guild_id=None, show_type=False):
        output = ""
        if show_type:
            output += f"> **{type(self).__name__}**\n"
        if show_id:
            output += f"> **ID:**  {self.id}\n"
        output += f"> **Author:**  {self.get_author(client).name}\n"
        output += f"> **Channel:**  {self.get_delivery_channel(client).mention}\n"
        if guild_id != self.guild_id:
            output += f"> **Guild:**  {self.get_guild(client).name}\n"
        return output

    def get_show_content(self, raw=False):
        if raw:
            return "```\n" + self.content + "\n```"
        else:
            return self.content

class Message(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, content, description, repeat_until):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        self.delivery_time = delivery_time
        self.repeat = repeat
        self.last_repeat_message = last_repeat_message
        self.repeat_until = repeat_until
        self.update_db()

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, self.delivery_time, self.author_id, self.repeat, self.last_repeat_message, self.content, self.description, self.repeat_until)

    async def get_show_output(self, client, raw=None, show_id=False, guild_id=None, show_content=False, timezone=None, format_24=False):
        output = self.get_show_header(client, show_id, guild_id, show_content)
        if self.delivery_time and self.delivery_time >= 0:
            if round((self.delivery_time - time())/60, 1) < 0:
                output += f"> **Delivery failed:**  {str(round((self.delivery_time - time())/60, 1) * -1)} minutes ago\n"
            else:
                output += f"> **Deliver:**  {gigtz.display_localized_time(self.delivery_time, timezone, format_24)}\n"
        if self.delivery_time and self.delivery_time >= 0:
            output += f"> **Repeat:**  {self.repeat}\n"
        if self.repeat and self.last_repeat_message:
            last_message = await self.get_delivery_channel(client).fetch_message(self.last_repeat_message)
            output += f"> **Last Delivery:**  {last_message.jump_url}\n"
        if self.repeat and self.repeat_until:
            output += f"> **Repeat Until:**  {gigtz.display_localized_time(self.repeat_until, timezone, format_24)}\n"
        output += f"> **Description:**  {self.description}\n"
        if show_content:
            output += self.get_show_content(raw)
        return output

class Template(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, author_id, content, description):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        self.update_db()

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, None, self.author_id, None, None, self.content, self.description, None)

    async def get_show_output(self, client, raw=None, show_id=False, guild_id=None, show_content=False):
        output = self.get_show_header(client, show_id, guild_id, show_content)
        output += f"> **Description:**  {self.description}\n"
        if show_content:
            output += self.get_show_content(raw)
        return output

class Proposal(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, author_id, approval_message_id, content, description, required_approvals):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        self.approval_message_id = approval_message_id
        self.required_approvals = required_approvals
        self.update_db()

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, -1, self.author_id, None, self.approval_message_id, self.content, self.description, None)

    async def get_show_output(self, client, raw=None, show_id=False, guild_id=None, show_content=False):
        output = self.get_show_header(client, show_id, guild_id, show_content)
        output += f"> **Description:**  {self.description}\n"
        output += f"> **Required Approvals:**  {votes.get_required_approvals(self.id)}\n"
        output += f"> **Current Approvals:**  {votes.vote_count(self.id)}\n"
        if show_content:
            output += self.get_show_content(raw)
        return output
