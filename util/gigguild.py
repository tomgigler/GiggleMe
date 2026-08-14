#!/usr/bin/env python
import gigdb

guilds = {}

class Guild:
    def __init__(self, id, guild_name, approval_channel_id=None, plan_level=None):
        self.id = id
        self.guild_name = guild_name
        self.approval_channel_id = approval_channel_id
        self.plan_level = plan_level
        self.save()

    def save(self):
        gigdb.save_guild(
            self.id,
            self.guild_name,
            self.approval_channel_id,
            self.plan_level
        )

    def set_approval_channel_id(self, approval_channel_id):
        self.approval_channel_id = approval_channel_id
        self.save()

    def set_plan_level(self, plan_level):
        self.plan_level = plan_level
        self.save()

def load_guilds():
    for row in gigdb.get_guilds():
        guilds[row[0]] = Guild(row[0], row[1], row[2], row[3])
