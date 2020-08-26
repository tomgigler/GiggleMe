#!/usr/bin/env python
import discord
import time
import re

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        time.sleep(5)
        await message.delete()
        return
    if re.search('hello', message.content, re.IGNORECASE):
        await message.channel.send(f"{message.content} {time.strftime('%X')}")
    elif re.search('bye', message.content, re.IGNORECASE):
        await message.channel.send(f"{message.content} {time.strftime('%X')}")

client.run("NzQ3ODM3NTM2Nzc2NDg2OTUz.X0Ur-g.rKAZTJh8jmqbKzYKy95zfWKJh9M")
