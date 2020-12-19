#!/usr/bin/env python
import discord
import re
import os
import asyncio
from settings import bot_token
import sys
from datetime import datetime
from time import time, ctime
from operator import attrgetter
from hashlib import md5

client = discord.Client()
delayed_messages = {}

class DelayedMessage:
    def __init__(self, message, channel, delay):
        self.message = message
        self.channel = channel
        self.deliveryTime = time() + int(delay) * 60
        self.id = md5((message.author.name + message.content + channel.name + str(self.deliveryTime)).encode('utf-8')).hexdigest()[:8]

async def process_delay_message(message):
    try:
        guild = message.guild
        guild_id = guild.id
    except:
        return

    try:
        channel_name = re.search(r'channel=(.+)', message.content).group(1)
        channel = discord.utils.get(guild.channels, name=channel_name)
    except:
        channel = message.channel

    try:
        has_permission = message.author.permissions_in(channel).manage_channels
    except:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {channel.name}", color=0x00ff00))
        return
    if has_permission:
        match = re.search(r'^~giggle (\d+)[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
        delay = match.group(1)
        msg = match.group(2)
        msg = re.sub(r'{}', r'@', msg)
        await message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {channel.name} channel in the {guild.name} server in {delay} minutes", color=0x00ff00))
        print(f"{datetime.now()}: {message.author.name} has scheduled a message on {channel.name} in {guild.name} in {delay} minutes")
        newMessage = DelayedMessage(message, channel, delay)
        if message.guild.id in delayed_messages:
            delayed_messages[message.guild.id].append(newMessage)
        else:
            delayed_messages[message.guild.id] = [newMessage]
        await asyncio.sleep(int(delay)*60)
        if message.guild.id in delayed_messages:
            if newMessage in delayed_messages[message.guild.id]:
                await channel.send(msg)
                delayed_messages[message.guild.id].remove(newMessage)
                if len(delayed_messages[message.guild.id]) < 1:
                    del delayed_messages[message.guild.id]
                print(f"{datetime.now()}: {message.author.name}'s message on {channel.name} in {guild.name} has been delivered")
    else:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {channel.name}", color=0x00ff00))

async def list_delay_messages(message):
    try:
        guild_id = message.guild.id
    except:
        return
    channel = message.channel
    if guild_id in delayed_messages and len(delayed_messages[guild_id]) > 0:
        embed=discord.Embed(title="Scheduled Messages ==================================")
        delayed_messages[guild_id].sort(key=attrgetter('deliveryTime'))
        for msg in delayed_messages[guild_id]:
            embed.add_field(name="ID", value=f"{msg.id}", inline=True)
            embed.add_field(name="Author", value=f"{msg.message.author.name}", inline=True)
            embed.add_field(name="Channel", value=f"{msg.channel}", inline=True)
            embed.add_field(name="Delivering in", value=f"{str(round((msg.deliveryTime - time())/60, 1))} minutes", inline=False)
        await channel.send(embed=embed)
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_delay_message(message):
    try:
        guild_id = message.guild.id
    except:
        return
    message_found = False
    msg_num = re.search(r'^~giggle show (\S+)', message.content).group(1)
    if guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                content = f"{msg.message.author.name} scheduled:\n"
                content += re.search(r'^~giggle \d+[^\n]*[\n](.*)', msg.message.content, re.MULTILINE|re.DOTALL).group(1)
                await message.channel.send(content)
                message_found = True
        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def cancel_delay_message(message):
    try:
        guild_id = message.guild.id
    except:
        return

    msg_num = re.search(r'^~giggle cancel (\S+)', message.content).group(1)
    message_found = False
    if guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                delayed_messages[guild_id].remove(msg)
                if len(delayed_messages[guild_id]) < 1:
                    del delayed_messages[guild_id]
                await message.channel.send(embed=discord.Embed(description="Message canceled", color=0x00ff00))
                print(f"{datetime.now()}: {message.author.name} canceled message {msg_num}")
                message_found = True
        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == 'kill' and message.author.id == 669370838478225448:
        await message.channel.send(embed=discord.Embed(description=f"Killing {client.user.name}", color=0x00ff00))
        sys.exit()

    if re.search(r'^~giggle list', message.content):
        await list_delay_messages(message)
        return

    if re.search(r'^~giggle show \S+', message.content):
        await show_delay_message(message)
        return

    if re.search(r'^~giggle cancel \S+', message.content):
        await cancel_delay_message(message)
        return

    if re.search(r'^~giggle \d+', message.content):
        await process_delay_message(message)
        return

client.run(bot_token)
