#!/usr/bin/env python
import discord
import re
import os
import asyncio
from settings import bot_token
import sys
from datetime import datetime

client = discord.Client()

async def process_temps(message):
    processed_values = []
    for temp in re.findall('[-]?[0-9]*\.?[0-9]+ ?[CFcf](?:\s+|$|\?|\.|,)', message.content):
        match = re.search('([-]?[0-9]*\.?[0-9]+) ?([CFcf])(?:\s+|$|\?|\.|,)', temp)
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

async def list_user_roles(message):
    youtube_roles = []
    youtube_channels = []
    server_roles = []
    user_roles = []
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    for channel in youtube_category.channels:
        youtube_channels.append(channel.name)
    for role in message.guild.roles:
        server_roles.append(role.name)
    for role in message.author.roles:
        user_roles.append(role.name)
    for name in youtube_channels:
        if name in server_roles and name in user_roles:
            if name not in youtube_roles:
                youtube_roles.append(name)
    if len(youtube_roles) > 0:
        await message.channel.send('\n'.join(youtube_roles))

async def add_user_role(message):
    add_role = re.search('~giggle youtube add (.*)', message.content, re.IGNORECASE).group(1)
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    if not discord.utils.get(youtube_category.channels, name=add_role):
        await message.channel.send(f"Cannot add {add_role} role")
        return
    if discord.utils.get(message.author.roles, name=add_role):
        await message.channel.send(f"You already have the {add_role} role")
        return
    else:
        role = discord.utils.get(message.guild.roles, name=add_role)
        await message.author.add_roles(role)
    await asyncio.sleep(1)
    if discord.utils.get(message.author.roles, name=add_role):
        await message.channel.send(f"Added {add_role} role")
    else:
        await message.channel.send(f"Failed to add {add_role} role")

async def remove_user_role(message):
    remove_role = re.search('~giggle youtube remove (.*)', message.content, re.IGNORECASE).group(1)
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    if not discord.utils.get(youtube_category.channels, name=remove_role):
        await message.channel.send(f"Cannot remove {remove_role} role")
        return
    if not discord.utils.get(message.author.roles, name=remove_role):
        await message.channel.send(f"You don't currently have the {remove_role} role")
        return
    else:
        role = discord.utils.get(message.guild.roles, name=remove_role)
        await message.author.remove_roles(role)
    await asyncio.sleep(1)
    if not discord.utils.get(message.author.roles, name=remove_role):
        await message.channel.send(f"Removed {remove_role} role")
    else:
        await message.channel.send(f"Failed to remove {remove_role} role")

async def list_roles(message):
    youtube_roles = []
    youtube_channels = []
    server_roles = []
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    for channel in youtube_category.channels:
        youtube_channels.append(channel.name)
    for role in message.guild.roles:
        server_roles.append(role.name)
    for name in youtube_channels:
        if name in server_roles:
            if name not in youtube_roles:
                youtube_roles.append(name)
    if len(youtube_roles) > 0:
        await message.channel.send('\n'.join(youtube_roles))

async def process_vol_message(message):
    server_roles = []
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    content_creators = []
    for channel in youtube_category.channels:
        content_creators.append(channel)
    try:
        if re.search(r'Successfully subscribed to (.*)', message.embeds[0].title):
            channel_name = re.search(r'Successfully subscribed to (.*)', message.embeds[0].title).group(1)
            name = channel_name.replace(' ', '-').lower()
            creator_role_found = False
            creator_channel_found = False
            for role in message.guild.roles:
                if role.name == channel_name:
                    creator_role_found = True
            for channel in message.guild.channels:
                if channel.name == channel_name:
                    creator_channel_found = True
            if not creator_channel_found:
                await message.guild.create_text_channel(name=name, category=youtube_category)
                await message.channel.send(f"I've created the {name} channel")
            if not creator_role_found:
                await message.guild.create_role(name=name)
                await message.channel.send(f"I've created the {name} role")
            await message.channel.send(f"New {channel_name} videos will be posted to the {name} channel and ping the {name} role")
            return
    except:
        await message.channel.send(f"I don't know how to handle {channel_name}'s content.  Please contact my creator to get {channel_name} added to my functionality")
        return

    for channel in message.guild.text_channels:
        if channel.name == 'voice-of-light-posts':
            vol_posts_channel = channel

    try:
        if(message.embeds[0].title == 'Youtube subscriptions'):
            return
    except:
        pass

    if vol_posts_channel == message.channel:
        try:
            creator_name = message.embeds[0].author.name
            channel_role_name = creator_name.replace(' ', '-').lower()

            creator_channel = discord.utils.get(message.guild.channels, name=channel_role_name)
            creator_role = discord.utils.get(message.guild.roles, name=channel_role_name)

            if creator_channel:
                if creator_role:
                    await creator_channel.send(creator_role.mention)
                else:
                    await vol_posts_channel.send(f"Cannot ping role {creator_name}")
                for embed in message.embeds:
                    await creator_channel.send(embed=embed)
            else:
                await vol_posts_channel.send(f"Cannot post to channel {creator_name}")
        except:
            pass

async def process_delay_message(message):
    try:
        server_id = int(re.search(r'server=(\d+)', message.content).group(1))
    except:
        server_id = message.guild.id

    guild = discord.utils.get(client.guilds, id=server_id)
    channel_name = re.search(r'channel=(.+)', message.content).group(1)
    channel = discord.utils.get(guild.channels, name=channel_name)

    try:
        is_admin = message.author.permissions_in(channel).administrator
    except:
        await message.channel.send('Admin permission are required to send delayed messages')
        return
    if is_admin:
        match = re.search(r'^~giggle delay (\d+)[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
        delay = match.group(1)
        msg = match.group(2)
        msg = f"Here's a message from {message.author.mention}:\n" + msg
        await message.channel.send(f"Your message will be delivered to the {channel.name} channel in the {guild.name} server in {delay} minutes")
        print(f"{datetime.now()}: {message.author.name} has scheduled a message on {channel.name} in {guild.name} in {delay} minutes")
        await asyncio.sleep(int(delay)*60)
        await channel.send(msg)
        print(f"{datetime.now()}: {message.author.name}'s message on {channel.name} in {guild.name} has been delivered")
    else:
        await message.channel.send('Admin permission are required to send delayed messages')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == 'kill' and message.author.id == 669370838478225448:
        await message.channel.send(f"Killing {client.user.name}")
        sys.exit()

    if re.search(r'^~giggle delay \d+', message.content):
        await process_delay_message(message)
        return

    if message.author.id == 460410391290314752:
        await process_vol_message(message)

    if re.search(r'^~giggle youtube$', message.content, re.IGNORECASE):
        await message.channel.send("""Start your message with "~giggle youtube" followed by one of the commands below:
            roles:
                Show youtube roles currently assigned to you
            add <role>:
                Assign <role> to yourself
            remove <role>:
                Remove <role> from yourself
            list:
                Show available youtube roles on this server""")

    elif re.search(r'^~giggle youtube roles$', message.content, re.IGNORECASE):
        await list_user_roles(message)

    elif re.search(r'^~giggle youtube add \S', message.content, re.IGNORECASE):
        await add_user_role(message)

    elif re.search(r'^~giggle youtube remove \S', message.content, re.IGNORECASE):
        await remove_user_role(message)

    elif re.search(r'^~giggle youtube list$', message.content, re.IGNORECASE):
        await list_roles(message)

    elif re.search(r'^~giggle.*[-]?[0-9]*\.?[0-9]+ ?[CFcf](?:\s+|$|\?|\.|,)', message.content, re.IGNORECASE):
        await process_temps(message)

    if client.user.mentioned_in(message):
        await message.channel.send(f"Hi {message.author.name}!  I convert temperatures.  Just put \"~giggle\" at the beginning of your message")
        vol_posts_channel = None
        for channel in message.guild.text_channels:
            if channel.name == 'voice-of-light-posts':
                vol_posts_channel = channel
        if vol_posts_channel:
            await message.channel.send(f"I also do YouTube announcements on this server.  Type \"~giggle youtube\" for details")


client.run(bot_token)
