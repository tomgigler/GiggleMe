#!/usr/bin/env python
import discord
import re
import os
import asyncio

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if re.search('[-]?[0-9]+ ?[CFcf]', message.content):
        processed_values = []
        for temp in re.findall('[-]?[0-9]+ ?[CFcf]', message.content):
            match = re.search('([-]?[0-9]+) ?([CFcf])', temp)
            value = float(match.group(1))
            scale = match.group(2)
            if scale == 'c':
                scale = 'C'
            if scale == 'f':
                scale = 'F'
            newvalue = value * 1.8 + 32 if scale == 'C' else (value - 32)/1.8
            newscale = 'F' if scale == 'C' else 'C'
            if f"{value}{scale}" not in processed_values:
                await message.channel.send(f"{value} {scale} = {round(newvalue, 1)} {newscale}")
                processed_values.append(f"{value}{scale}")
                processed_values.append(f"{newvalue}{newscale}")

client.run(os.getenv('BOT_TOKEN'))
