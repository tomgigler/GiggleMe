#!/usr/bin/env python
import discord
import time
import re
import os
import asyncio

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if re.search('hello', message.content, re.IGNORECASE):
        await asyncio.sleep(6)
        await message.channel.send(f"{message.content} {time.strftime('%X')}")
    elif re.search('bye', message.content, re.IGNORECASE):
        await message.channel.send(f"{message.content} {time.strftime('%X')}")
    elif message.content == 'channels':
        for channel in message.guild.channels:
            await message.channel.send(str(channel))
    elif message.content == 'delete':
        async for message in message.channel.history(limit=200):
            await message.delete()

client.run(os.getenv('BOT_TOKEN'))
