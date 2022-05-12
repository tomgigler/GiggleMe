#!/usr/bin/env python
import discord
import asyncio
from hashlib import md5
from time import time
import gigdb
import giguser
import gigtz
import gigchannel
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
        channel = None
        try:
            channel = discord.utils.get(self.get_guild(client).text_channels, id=self.delivery_channel_id)
        except:
            pass
        if not channel:
            gigchannel.load_channels()
            if self.delivery_channel_id is not None:
                channel = gigchannel.channels[self.delivery_channel_id]
        return channel

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
        if self.get_delivery_channel(client) is not None:
            output += f"> **Channel:**  {self.get_delivery_channel(client).mention}\n"
        if guild_id != self.guild_id:
            output += f"> **Guild:**  {self.get_guild(client).name}\n"
        return output

    def get_show_content(self, raw=False, timezone=None):
        if raw == "raw+":
            return self.content + "\n```"
        elif raw:
            return "```\n" + self.content + "\n```"
        else:
            return self.content

class Message(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, content, description, repeat_until, special_handling, update_db=True):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        self.delivery_time = delivery_time
        self.repeat = repeat
        self.last_repeat_message = last_repeat_message
        self.repeat_until = repeat_until
        self.special_handling = special_handling
        if update_db:
            self.update_db()

    def get_delivery_channel(self, client):
        channel = None
        try:
            channel = discord.utils.get(self.get_guild(client).text_channels, id=self.delivery_channel_id)
            if not channel and self.special_handling > 1:
                channel = discord.utils.get(self.get_guild(client).channels, id=self.delivery_channel_id)
        except:
            pass
        if not channel:
            gigchannel.load_channels()
            channel = gigchannel.channels[self.delivery_channel_id]
        return channel

    def get_show_content(self, raw=False, timezone=None):
        command = ""
        if raw == "raw+":
            command = f"~giggle {gigtz.command_localized_time(self.delivery_time, timezone)}"
            command += f" channel={self.delivery_channel_id}"
            if self.repeat:
                command += f" repeat={self.repeat}"
            if self.repeat_until:
                command += f" duration={int((self.repeat_until-self.delivery_time)/60)}"
            if self.special_handling == 1:
                command += f" pin=true"
            if self.special_handling == 2:
                command += f" set-topic=true"
            if self.special_handling == 3:
                command += f" set-channel-name=true"
            if self.description:
                command += f" desc=\"{self.description}\""
            return "```\n" + command + "\n" + super().get_show_content(raw, timezone)
        else:
            return super().get_show_content(raw, timezone)

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, self.delivery_time, self.author_id, self.repeat, self.last_repeat_message, self.content, self.description, self.repeat_until, self.special_handling)

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
        if self.special_handling == 1:
            output += "> **Pin Message:**  True\n"
        if self.special_handling == 2:
            output += "> **Set Topic:**  True\n"
        if self.special_handling == 3:
            output += "> **Set Channel Name:**  True\n"
        return output

class Template(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, author_id, content, description, update_db=True):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        if update_db:
            self.update_db()

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, None, self.author_id, None, None, self.content, self.description, None, None)

    async def get_show_output(self, client, raw=None, show_id=False, guild_id=None, show_content=False, timezone=None, format_24=False):
        output = self.get_show_header(client, show_id, guild_id, show_content)
        output += f"> **Description:**  {self.description}\n"
        return output

class Proposal(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, author_id, approval_message_id, content, description, required_approvals, update_db=True):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        self.approval_message_id = approval_message_id
        self.required_approvals = required_approvals
        if update_db:
            self.update_db()

    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, -1, self.author_id, None, self.approval_message_id, self.content, self.description, None, None)

    async def get_show_output(self, client, raw=None, show_id=False, guild_id=None, show_content=False, timezone=None, format_24=False):
        output = self.get_show_header(client, show_id, guild_id, show_content)
        output += f"> **Description:**  {self.description}\n"
        output += f"> **Required Approvals:**  {votes.get_required_approvals(self.id)}\n"
        output += f"> **Current Approvals:**  {votes.vote_count(self.id)}\n"
        return output

class AutoReply(DelayedMessage):
    def __init__(self, id, guild_id, delivery_channel_id, author_id, trigger, content, description, special_handling, update_db=True):
        super().__init__(id, guild_id, delivery_channel_id, author_id, content, description)
        self.trigger = trigger
        self.special_handling = special_handling
        if update_db:
            self.update_db()

    def update_db(self):
        # We'll use a deliver_time of -2 to indicate AutoReply
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, -2, self.author_id, self.trigger, None, self.content, self.description, None, self.special_handling)

    async def get_show_output(self, client, raw=None, show_id=False, guild_id=None, show_content=False, timezone=None, format_24=False):
        output = self.get_show_header(client, show_id, guild_id, show_content)
        output += f"> **Trigger**  {self.trigger}\n"
        output += f"> **Description:**  {self.description}\n"
        if self.special_handling is not None and self.special_handling & 1:
            output += f"> **Wildcard:**  true\n"
        if self.special_handling is not None and self.special_handling & 2:
            output += f"> **Delete:**  true\n"
        if self.special_handling is not None and self.special_handling & 4:
            output += f"> **Report:**  true\n"
        return output
