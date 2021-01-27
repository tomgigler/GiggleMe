#!/usr/bin/env python
import gigdb

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

def load_guilds():
    for row in gigdb.get_all("guilds"):
        guilds[row[0]] = Guild(row[0], row[1], row[2], row[3], row[4])
