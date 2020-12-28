#!/usr/bin/env python
import discord
import re
import asyncio
import settings
from datetime import datetime
from time import time, ctime, localtime
from operator import attrgetter
from hashlib import md5
import mysql.connector

client = discord.Client()
delayed_messages = {}

class DelayedMessage:
    def __init__(self, deliveryChannel, deliveryTime, guild, author, channel, message):
        self.deliveryChannel = deliveryChannel
        self.deliveryTime = deliveryTime
        self.guild = guild
        self.author = author
        self.channel = channel
        self.message = message
        self.id = md5((self.author + self.message.content + self.deliveryChannel.name + ctime()).encode('utf-8')).hexdigest()[:8]

def insert_into_db(message):
    mydb = mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database
            )

    mycursor = mydb.cursor()
    mycursor.execute(f"INSERT INTO messages values ('{message.id}', '{message.guild.id}', '{message.channel.id}', '{message.deliveryChannel.id}', '{message.deliveryTime}', '{message.author}', '{message.message.id}')")
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

def delete_from_db(id):
    mydb = mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database
            )

    mycursor = mydb.cursor()
    mycursor.execute(f"DELETE FROM messages WHERE id='{id}'")
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

async def load_from_db():
    mydb = mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database
            )

    loop = asyncio.get_event_loop()
    mycursor = mydb.cursor()

    mycursor.execute("select * from messages")

    for msg in mycursor.fetchall():
        guildID = msg[1]
        channelID = msg[2]
        deliveryChannelID = msg[3]
        deliveryTime = msg[4]
        author = msg[5]
        messageID = msg[6]
        delete_from_db(msg[0])

        guild = discord.utils.get(client.guilds, id=int(guildID))
        deliveryChannel = discord.utils.get(guild.text_channels, id=int(deliveryChannelID))
        channel = discord.utils.get(guild.text_channels, id=int(channelID))
        message = await channel.fetch_message(int(messageID))

        newMessage =  DelayedMessage(deliveryChannel, float(deliveryTime), guild, author, channel, message)

        insert_into_db(newMessage)

        if int(guildID) in delayed_messages:
            delayed_messages[int(guildID)].append(newMessage)
        else:
            delayed_messages[int(guildID)] = [newMessage]

        loop.create_task(schedule_delay_message(newMessage))

    mycursor.close()
    mydb.disconnect()

async def process_delay_message(message):

    # get channel (deliveryChannel) from original message
    try:
        channel_name = re.search(r'channel=(.+)', message.content).group(1)
        channel = discord.utils.get(message.guild.channels, name=channel_name)
        if not channel:
            await message.channel.send(embed=discord.Embed(description=f"Cannot find {channel_name} channel", color=0xff0000))
            return
    except:
        # default to current channel
        channel = message.channel

    try:
        # TODO:  for now, user needs manage_channels permissions in the target channel
        has_permission = message.author.permissions_in(channel).manage_channels
    except:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {channel.name}", color=0xff0000))
        return

    if not has_permission:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {channel.name}", color=0xff0000))
    else:
        if not re.search(r'~giggle \d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', message.content) and not re.search(r'^~giggle (\d+)[ \n]', message.content):
            await show_help(message.channel)
            return
        if re.search(r'~giggle \d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', message.content):
            match = re.search(r'^~giggle (\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2})[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
            deliveryTime = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M').timestamp()
        else:
            match = re.search(r'^~giggle (\d+)[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
            if match.group(1) == '0':
                deliveryTime = 0
            else:
                deliveryTime = float(time()) + int(match.group(1)) * 60
        msg = match.group(2)

        #Make sure {roles} exist
        for mention in re.finditer(r'{([^}]+)}', msg):
            if mention.group(1) != 'everyone' and mention.group(1) != 'here':
                try:
                    mention_replace = discord.utils.get(message.guild.roles,name=mention.group(1))
                except:
                    # TODO: try searching for user mention.group(1)
                    await message.channel.send(embed=discord.Embed(description=f"Cannot find role {mention.group(1)}", color=0xff0000))
                    return

                if not mention_replace:
                    await message.channel.send(embed=discord.Embed(description=f"Cannot find role {mention.group(1)}", color=0xff0000))

        # create new DelayedMessage
        newMessage =  DelayedMessage(channel, float(deliveryTime), message.guild, message.author.name, message.channel, message)
        insert_into_db(newMessage)
        if deliveryTime == 0:
            await message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {channel.name} channel in the {message.guild.name} server now", color=0x00ff00))
        else:
            await message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {channel.name} channel in the {message.guild.name} server {ctime(newMessage.deliveryTime)} {localtime(newMessage.deliveryTime).tm_zone}", color=0x00ff00))

        if message.guild.id in delayed_messages:
            delayed_messages[message.guild.id].append(newMessage)
        else:
            delayed_messages[message.guild.id] = [newMessage]

        await schedule_delay_message(newMessage)

async def schedule_delay_message(newMessage):

    guild = newMessage.guild

    match = re.search(r'^~giggle \d+[^\n]*[\n](.*)', newMessage.message.content, re.MULTILINE|re.DOTALL)
    msg = match.group(1)
    for mention in re.finditer(r'{([^}]+)}', msg):
        if mention.group(1) == 'everyone':
            mention_replace = '@everyone'
        elif mention.group(1) == 'here':
            mention_replace = '@here'
        else:
            try:
                mention_replace = discord.utils.get(guild.roles,name=mention.group(1)).mention
            except:
                # TODO: try searching for user mention.group(1)
                # await message.channel.send(embed=discord.Embed(description=f"Cannot find role {mention.group(1)}", color=0xff0000))
                # return

                # At this point, we'll just leave {role} in the message
                pass
        msg = re.sub(f"{{{re.escape(mention.group(1))}}}", mention_replace, msg)

    if newMessage.deliveryTime == 0:
        delay = 0
    else:
        delay = float(newMessage.deliveryTime) - float(time())
    if float(delay) < 0:
        return
    await asyncio.sleep(int(delay))

    # after sleep, make sure message has not been canceled
    if guild.id in delayed_messages:
        if newMessage in delayed_messages[guild.id]:
            await newMessage.deliveryChannel.send(msg)
            delayed_messages[guild.id].remove(newMessage)
            if len(delayed_messages[guild.id]) < 1:
                del delayed_messages[guild.id]
            delete_from_db(newMessage.id)

async def list_delay_messages(message):
    try:
        guild_id = message.guild.id
    except:
        return
    channel = message.channel
    if guild_id in delayed_messages and len(delayed_messages[guild_id]) > 0:
        embed=discord.Embed(title="Scheduled Messages ==================================")
        delayed_messages[guild_id].sort(key=attrgetter('deliveryTime'))
        count = 0
        for msg in delayed_messages[guild_id]:
            embed.add_field(name="ID", value=f"{msg.id}", inline=True)
            embed.add_field(name="Author", value=f"{msg.author}", inline=True)
            embed.add_field(name="Channel", value=f"{msg.deliveryChannel.name}", inline=True)
            if round((msg.deliveryTime - time())/60, 1) < 0:
                embed.add_field(name="Delivery failed", value=f"{str(round((msg.deliveryTime - time())/60, 1) * -1)} minutes ago", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{ctime(msg.deliveryTime)} {localtime(msg.deliveryTime).tm_zone}", inline=False)
            count += 1
            if count == 6:
                await channel.send(embed=embed)
                embed=discord.Embed(title="Scheduled Messages (continued) ======================")
                count = 0
        if count != 0:
            await channel.send(embed=embed)
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def list_all_delay_messages(message):
    channel = message.channel
    if len(delayed_messages) > 0:
        embed=discord.Embed(title="Scheduled Messages ==================================")
        count = 0
        for guild_id in delayed_messages:
            delayed_messages[guild_id].sort(key=attrgetter('deliveryTime'))
            for msg in delayed_messages[guild_id]:
                embed.add_field(name="ID", value=f"{msg.id}", inline=True)
                embed.add_field(name="Author", value=f"{msg.author}", inline=True)
                embed.add_field(name="Server - Channel", value=f"{client.get_guild(guild_id)} - {msg.deliveryChannel.name}", inline=True)
                if round((msg.deliveryTime - time())/60, 1) < 0:
                    embed.add_field(name="Delivery failed", value=f"{str(round((msg.deliveryTime - time())/60, 1) * -1)} minutes ago", inline=False)
                else:
                    embed.add_field(name="Deliver", value=f"{ctime(msg.deliveryTime)} {localtime(msg.deliveryTime).tm_zone}", inline=False)
                count += 1
                if count == 6:
                    await channel.send(embed=embed)
                    embed=discord.Embed(title="Scheduled Messages (continued) ======================")
                    count = 0
        if count != 0:
            await channel.send(embed=embed)
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_delay_message(message):
    message_found = False
    msg_num = re.search(r'^~giggle show (\S+)', message.content).group(1)
    for guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                content = f"**Author:**  {msg.author}\n"
                content += f"**Deliver to:**  {msg.deliveryChannel.name}\n"
                if round((msg.deliveryTime - time())/60, 1) < 0:
                    content += f"**Delivery failed:**  {str(round((msg.deliveryTime - time())/60, 1) * -1)} minutes ago\n"
                else:
                    content += f"**Deliver:**  {ctime(msg.deliveryTime)} {localtime(msg.deliveryTime).tm_zone}\n"
                match = re.search(r'^~giggle \d+[^\n]*[\n](.*)', msg.message.content, re.MULTILINE|re.DOTALL)
                content += match.group(1)
                await message.channel.send(content)
                message_found = True
    if not message_found:
        await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

async def cancel_delay_message(message):
    try:
        guild_id = message.guild.id
    except:
        return

    msg_num = re.search(r'^~giggle cancel +(\S+)|^~giggle delete +(\S+)|^~giggle remove +(\S+)|^~giggle clear +(\S+)', message.content).group(1)
    message_found = False
    if guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                delayed_messages[guild_id].remove(msg)
                if len(delayed_messages[guild_id]) < 1:
                    del delayed_messages[guild_id]
                await message.channel.send(embed=discord.Embed(description="Message canceled", color=0x00ff00))
                message_found = True
                delete_from_db(msg.id)
        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_help(channel):
    helpOutput = """To schedule <message> to be delivered to <channel> in <minutes>:

    `~giggle <minutes> channel=<channel>`
    `<message>`

    To schedule <message> to be delivered to <channel> at <date-time>:

    `~giggle <date-time> channel=<channel>`
    `<message>`

    The format for <date-time> is YYYY-MM-DD HH:MM
    All times are UTC

    The following commands may be used to manage scheduled messages:

    `~giggle list`
    Display a list of currently scheduled messages

    `~giggle show <message-id>`
    Show the contens of the message identified by <message-id>

    `~giggle cancel <message-id>`
    Cancel message identified by <message-id>

    `~giggle help`
    Show this help"""
    await channel.send(embed=discord.Embed(description=helpOutput))

@client.event
async def on_message(message):
    try:
        if not message.author.guild_permissions.mute_members and message.author.id != 669370838478225448:
            return
    except:
        return

    if message.author == client.user:
        return

    if re.search(r'^~giggle listall', message.content) and message.author.id == 669370838478225448:
        await list_all_delay_messages(message)
        return

    if re.search(r'^~giggle list', message.content):
        await list_delay_messages(message)
        return

    if re.search(r'^~giggle show \S+', message.content):
        await show_delay_message(message)
        return

    if re.search(r'^~giggle cancel +\S+|^~giggle delete +\S+|^~giggle remove +\S+|^~giggle clear +\S+', message.content):
        await cancel_delay_message(message)
        return

    if re.search(r'^~giggle \d+.*\n.', message.content):
        await process_delay_message(message)
        return

    if re.search(r'^~giggle resume', message.content) and message.author.id == 669370838478225448:
        await load_from_db()
        return

    if re.search(r'^~giggle', message.content):
        await show_help(message.channel)
        return

@client.event
async def on_guild_join(guild):
    user = await client.get_user(669370838478225448)
    await client.send_message(user, f"GiggleMe bot joined {guild.name}")

client.run(settings.bot_token)
