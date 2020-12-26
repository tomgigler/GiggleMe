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

mydb = mysql.connector.connect(
        host="localhost",
        user=settings.db_user,
        password=settings.db_password,
        database=settings.database
        )

class DelayedMessage:
    def __init__(self, message, channel, deliveryChannel, deliveryTime):
        self.message = message
        self.channel = channel
        self.deliveryChannel = deliveryChannel
        self.deliveryTime = deliveryTime
        self.id = md5((message.author.name + message.content + channel.name + deliveryChannel.name + ctime()).encode('utf-8')).hexdigest()[:8]

def insert_into_db(message):
    mycursor = mydb.cursor()
    mycursor.execute(f"INSERT INTO messages values ('{message.id}', '{message.message.guild.id}', '{message.channel.id}', '{message.deliveryChannel.id}', '{message.deliveryTime}', '{message.message.author.id}', '{message.message.id}')")
    mydb.commit()

def delete_from_db(id):
    mycursor = mydb.cursor()
    mycursor.execute(f"DELETE FROM messages WHERE id='{id}'")
    mydb.commit()

async def load_from_db():
    loop = asyncio.get_event_loop()
    mycursor = mydb.cursor()

    mycursor.execute("select * from messages")

    for msg in mycursor.fetchall():
        guild = discord.utils.get(client.guilds, id=int(msg[1]))
        channel = discord.utils.get(guild.text_channels, id=int(msg[2]))
        message = await channel.fetch_message(int(msg[6]))
        delete_from_db(msg[0])
        loop.create_task(process_delay_message(message, msg[4]))

async def process_delay_message(message, deliveryTime=None):
    try:
        guild = message.guild
        # TODO: remove this.  guild_id is not used
        guild_id = guild.id
    except:
        return

    skipOutput = True if deliveryTime else False

    # get channel (deliveryChannel) from original message
    try:
        channel_name = re.search(r'channel=(.+)', message.content).group(1)
        channel = discord.utils.get(guild.channels, name=channel_name)
        if not channel:
            await message.channel.send(embed=discord.Embed(description=f"Cannot find {channel_name} channel", color=0xff0000))
            return
    except:
        channel = message.channel

    try:
        has_permission = message.author.permissions_in(channel).manage_channels
    except:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {channel.name}", color=0xff0000))
        return

    if not has_permission:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {channel.name}", color=0xff0000))
    else:
        if not re.search(r'~giggle \d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', message.content) and not re.search(r'^~giggle (\d+)[ \n]', message.content):
            if not skipOutput:
                await show_help(message.channel)
            return
        if re.search(r'~giggle \d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', message.content):
            match = re.search(r'^~giggle (\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2})[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
            if not deliveryTime:
                deliveryTime = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M').timestamp()
        else:
            match = re.search(r'^~giggle (\d+)[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
            if not deliveryTime:
                deliveryTime = float(time()) + int(match.group(1)) * 60
        msg = match.group(2)

        # Replace {everyone|here|<role>} with mention
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
                    await message.channel.send(embed=discord.Embed(description=f"Cannot find role {mention.group(1)}", color=0xff0000))
                    return
            msg = re.sub(f"{{{re.escape(mention.group(1))}}}", mention_replace, msg)

        # create new DelayedMessage
        newMessage =  DelayedMessage(message, message.channel, channel, float(deliveryTime))
        insert_into_db(newMessage)
        if not skipOutput:
            await message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {channel.name} channel in the {guild.name} server {ctime(newMessage.deliveryTime)} {localtime(newMessage.deliveryTime).tm_zone}", color=0x00ff00))
        try:
            print(f"{datetime.now()}: {message.author.name} has scheduled a message on {channel.name} in {guild.name} {ctime(newMessage.deliveryTime)} minutes")
        except:
            pass
        if message.guild.id in delayed_messages:
            delayed_messages[message.guild.id].append(newMessage)
        else:
            delayed_messages[message.guild.id] = [newMessage]

        # TODO: everything here except the final else could be moved into a schedule_delayed_message method
        delay = float(deliveryTime) - float(time())
        if float(delay) < 0:
            return
        await asyncio.sleep(int(delay))

        # after sleep, make sure message has not been canceled
        if message.guild.id in delayed_messages:
            if newMessage in delayed_messages[message.guild.id]:
                await channel.send(msg)
                delayed_messages[message.guild.id].remove(newMessage)
                if len(delayed_messages[message.guild.id]) < 1:
                    del delayed_messages[message.guild.id]
                try:
                    print(f"{datetime.now()}: {message.author.name}'s message on {channel.name} in {guild.name} has been delivered")
                except:
                    pass
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
        for msg in delayed_messages[guild_id]:
            embed.add_field(name="ID", value=f"{msg.id}", inline=True)
            embed.add_field(name="Author", value=f"{msg.message.author.name}", inline=True)
            embed.add_field(name="Channel", value=f"{msg.deliveryChannel}", inline=True)
            if round((msg.deliveryTime - time())/60, 1) < 0:
                embed.add_field(name="Delivery failed", value=f"{str(round((msg.deliveryTime - time())/60, 1) * -1)} minutes ago", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{ctime(msg.deliveryTime)} {localtime(msg.deliveryTime).tm_zone}", inline=False)
        await channel.send(embed=embed)
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def list_all_delay_messages(message):
    channel = message.channel
    if len(delayed_messages) > 0:
        embed=discord.Embed(title="Scheduled Messages ==================================")
        for guild_id in delayed_messages:
            delayed_messages[guild_id].sort(key=attrgetter('deliveryTime'))
            for msg in delayed_messages[guild_id]:
                embed.add_field(name="ID", value=f"{msg.id}", inline=True)
                embed.add_field(name="Author", value=f"{msg.message.author.name}", inline=True)
                embed.add_field(name="Server - Channel", value=f"{client.get_guild(guild_id)} - {msg.deliveryChannel}", inline=True)
                if round((msg.deliveryTime - time())/60, 1) < 0:
                    embed.add_field(name="Delivery failed", value=f"{str(round((msg.deliveryTime - time())/60, 1) * -1)} minutes ago", inline=False)
                else:
                    embed.add_field(name="Deliver", value=f"{ctime(msg.deliveryTime)} {localtime(msg.deliveryTime).tm_zone}", inline=False)
        await channel.send(embed=embed)
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_delay_message(message):
    message_found = False
    msg_num = re.search(r'^~giggle show (\S+)', message.content).group(1)
    for guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                content = f"**Author:**  {msg.message.author.name}\n"
                content += f"**Deliver to:**  {msg.deliveryChannel.name}\n"
                if round((msg.deliveryTime - time())/60, 1) < 0:
                    content += f"**Delivery failed:**  {str(round((msg.deliveryTime - time())/60, 1) * -1)} minutes ago\n"
                else:
                    content += f"**Deliver:**  {ctime(msg.deliveryTime)} {localtime(msg.deliveryTime).tm_zone}\n"
                content += re.search(r'^~giggle \d+[^\n]*[\n](.*)', msg.message.content, re.MULTILINE|re.DOTALL).group(1)
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
                try:
                    print(f"{datetime.now()}: {message.author.name} canceled message {msg_num}")
                except:
                    pass
                message_found = True
                delete_from_db(msg.id)
        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_help(channel):
    await channel.send(embed=discord.Embed(description="TODO: Show help"))

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
