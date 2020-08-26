#!/usr/bin/env python
import discord
import time
import re
import os
import asyncio
import sys

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if re.search('^[-]?[0-9][0-9]?[0-9]?[CF]$', message.content):
        match = re.search('([-]?[0-9][0-9]?[0-9]?)([CF])', message.content)
        temp = float(match.group(1))
        scale = match.group(2)
        newtemp = temp * 1.8 + 32 if scale == 'C' else (temp - 32)/1.8
        newscale = 'F' if scale == 'C' else 'C'
        await message.channel.send(f"{temp}{scale} = {round(newtemp, 1)}{newscale}")
    if re.search('hello', message.content, re.IGNORECASE):
        await asyncio.sleep(6)
        await message.channel.send(f"{message.content} {time.strftime('%X')}")
    elif re.search('bye', message.content, re.IGNORECASE):
        await message.channel.send(f"{message.content} {time.strftime('%X')}")
    elif message.content == 'channels':
        for channel in message.guild.channels:
            await message.channel.send(f"{str(channel)}: {channel.type}")
    elif message.content == 'delete':
        async for message in message.channel.history(limit=200):
            await message.delete()

client.run(os.getenv('BOT_TOKEN'))
