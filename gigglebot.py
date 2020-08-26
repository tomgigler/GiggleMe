#!/usr/bin/env python
import discord
import re

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if re.search('hello', message.content, re.IGNORECASE):
        await message.channel.send(client.user)

client.run("NzQ3ODM3NTM2Nzc2NDg2OTUz.X0Ur-g.sXBtS9DzLFq3oKWkfDsNs6tNCF0")
