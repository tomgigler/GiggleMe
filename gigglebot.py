#!/usr/bin/env python
import discord
import time
import re
import asyncio

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        await asyncio.sleep(10)
        await message.delete()
        return
    if re.search('hello', message.content, re.IGNORECASE):
        await asyncio.sleep(6)
        await message.channel.send(f"{message.content} {time.strftime('%X')}")
    elif re.search('bye', message.content, re.IGNORECASE):
        await message.channel.send(f"{message.content} {time.strftime('%X')}")

client.run("NzQ3ODM3NTM2Nzc2NDg2OTUz.X0Ur-g.rKAZTJh8jmqbKzYKy95zfWKJh9M")
