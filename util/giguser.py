#!/usr/bin/env python
import gigdb
import gigtz

users = {}
user_guilds = {}
vips = {}
guilds = {}

class Guild:
    def __init__(self, id, guild_name, proposal_channel_id=None, approval_channel_id=None, delivery_channel_id=None):
        self.id = id
        self.guild_name = guild_name
        self.proposal_channel_id = proposal_channel_id
        self.approval_channel_id = approval_channel_id
        self.delivery_channel_id = delivery_channel_id
        self.save()

    def save(self):
        gigdb.save_guild(self.id, self.guild_name, self.proposal_channel_id, self.approval_channel_id, self.delivery_channel_id)

    def set_proposal_channel_id(self, proposal_channel_id):
        self.proposal_channel_id = proposal_channel_id
        self.save()

    def set_approval_channel_id(self, approval_channel_id):
        self.approval_channel_id = approval_channel_id
        self.save()

    def set_delivery_channel_id(self, delivery_channel_id):
        self.delivery_channel_id = delivery_channel_id
        self.save()

class Vip:
    def __init__(self, vip_id, guild_id, template_id, grace_period = None, last_sent = None):
        self.vip_id = int(vip_id)
        self.guild_id = guild_id
        self.template_id = template_id
        self.grace_period = grace_period
        self.last_sent = last_sent

    def set_last_sent(self, last_sent):
        gigdb.update_vip_last_sent(last_sent, self.vip_id, self.guild_id)
        self.last_sent = last_sent

class User:
    def __init__(self, id, name, timezone, last_active, last_message_id, format_24):
        self.id = id
        self.name = name
        self.timezone = timezone
        self.last_active = last_active
        self.last_message_id = last_message_id
        self.format_24 = format_24

    def set_last_active(self, last_active):
        gigdb.set_user_last_active(last_active, self.id)
        self.last_active = last_active

    def set_last_message(self, message_id):
        gigdb.set_user_last_message(message_id, self.id)
        self.last_message_id = message_id

    def set_time_format(self, time_format):
        if time_format == "24":
            self.format_24 = 1
        else:
            self.format_24 = 0

        gigdb.set_user_format_24(self.format_24, self.id)

    def set_timezone(self, tz):
        for tz_id in gigtz.timezones:
            if gigtz.timezones[tz_id].name == tz:
                gigdb.set_user_timezone(tz_id, self.name, self.id)
                users[self.id].timezone = tz_id
                return (f"Your time zone has been set to {tz}", 0x00ff00)

        return (f"Time zone **{tz}** not found\nTo see a list of available time zones:\n`~giggle timezones`", 0xff0000)

def load_users():
    for user in gigdb.get_all("users"):
        users[user[0]] = User(user[0], user[1], user[2], user[3], user[4], user[5])

    for row in gigdb.get_all("user_guilds"):
        if row[0] in user_guilds.keys():
            user_guilds[row[0]].append(row[1])
        else:
            user_guilds[row[0]] = [ row[1] ]

    for row in gigdb.get_all("guilds"):
        guilds[row[0]] = Guild(row[0], row[1], row[2], row[3], row[4])

    for row in gigdb.get_all("vips"):
        vips[(row[0], row[1])] = Vip(row[0], row[1], row[2], row[3], row[4])

def save_user(user_id, name, guild_id, guild_name):
    gigdb.save_user(user_id, name)

    gigdb.save_user_guild(user_id, guild_id, guild_name)

    if user_id not in users.keys():
        users[user_id] = User(user_id, name, None, 0, None, None)

    if user_id in user_guilds.keys():
        user_guilds[user_id].append(guild_id)
    else:
        user_guilds[user_id] = [ guild_id ]

    if guild_id in guilds.keys():
        guilds[guild_id].guild_name = guild_name
        guilds[guild_id].save()
    else:
        guilds[guild_id] = Guild(guild_id, guild_name)

def save_vip(vip):
    gigdb.save_vip(vip.vip_id, vip.guild_id, vip.template_id, vip.grace_period, vip.last_sent)
    vips[(vip.vip_id, vip.guild_id)] = vip

def delete_vip(vip):
    gigdb.delete_vip(vip.vip_id, vip.guild_id)
    vips.pop((vip.vip_id, vip.guild_id), None)

