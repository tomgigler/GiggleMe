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
requests_to_cancel_all = {}

class DelayedMessage:
    def __init__(self, guild, delivery_channel, delivery_time, author, content, id=None):
        self.guild = guild
        self.delivery_channel = delivery_channel
        self.delivery_time = float(delivery_time)
        self.author = author
        self.content = content

        if id:
            self.id = id
        else:
            self.id = md5((self.delivery_channel.name + str(delivery_time) + self.author.name + self.content + ctime()).encode('utf-8')).hexdigest()[:8]

class ConfirmationRequest:
    def __init__(self, confirmation_message, member):
        self.confirmation_message = confirmation_message
        self.member = member

def insert_into_db(message):
    mydb = mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

    mycursor = mydb.cursor()
    sql = "INSERT INTO messages values (%s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, (message.id, message.guild.id, message.delivery_channel.id, message.delivery_time, message.author.id, message.content))
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

def update_db(message):
    mydb = mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

    mycursor = mydb.cursor()
    sql = "UPDATE messages SET guild_id = %s, delivery_channel_id = %s, delivery_time =  %s, author_id = %s, content = %s WHERE id = %s"
    mycursor.execute(sql, (message.guild.id, message.delivery_channel.id, message.delivery_time, message.author.id, message.content, message.id))
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

def delete_from_db(id):
    mydb = mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
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
            database=settings.database,
            charset='utf8mb4'
            )

    loop = asyncio.get_event_loop()
    mycursor = mydb.cursor()

    mycursor.execute("select * from messages")

    for msg in mycursor.fetchall():
        guild_id = msg[1]
        delivery_channel_id = msg[2]
        delivery_time = msg[3]
        author_id = msg[4]
        content = msg[5]

        guild = discord.utils.get(client.guilds, id=int(guild_id))
        delivery_channel = discord.utils.get(guild.text_channels, id=int(delivery_channel_id))
        author = client.get_user(int(author_id))

        newMessage =  DelayedMessage(guild, delivery_channel, float(delivery_time), author, content, msg[0])

        if int(guild_id) in delayed_messages:
            delayed_messages[int(guild_id)].append(newMessage)
        else:
            delayed_messages[int(guild_id)] = [newMessage]

        loop.create_task(schedule_delay_message(newMessage))

    mycursor.close()
    mydb.disconnect()

async def process_delay_message(message, delay, channel, content):

    # get channel if provided
    if channel:
        delivery_channel = discord.utils.get(message.guild.channels, name=channel)
        if not delivery_channel:
            await message.channel.send(embed=discord.Embed(description=f"Cannot find {channel} channel", color=0xff0000))
            return
    else:
        # default to current channel
        delivery_channel = message.channel

    try:
        # TODO:  for now, user needs manage_channels permissions in the target channel
        has_permission = message.author.permissions_in(delivery_channel).manage_channels
    except:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {delivery_channel.name}", color=0xff0000))
        return

    if not has_permission:
        await message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {delivery_channel.name}", color=0xff0000))
    else:
        if re.search(r'^-?\d+$', delay):
            if delay == '0':
                delivery_time = 0
            else:
                delivery_time = float(time()) + int(delay) * 60
        else:
            try:
                delivery_time = datetime.strptime(delay, '%Y-%m-%d %H:%M').timestamp()
            except:
                await message.channel.send(embed=discord.Embed(description=f"{delay} is not a valid DateTime", color=0xff0000))
                return

        #Make sure {roles} exist
        try:
            replace_mentions(content, message.guild.id)
        except Exception as e:
            await message.channel.send(embed=discord.Embed(description=f"{str(e)}", color=0xff0000))
            return

        # create new DelayedMessage
        newMessage =  DelayedMessage(message.guild, delivery_channel, float(delivery_time), message.author, content)
        insert_into_db(newMessage)
        if delivery_time == 0:
            await message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.name} channel in the {message.guild.name} server now", color=0x00ff00))
        else:
            embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.name} channel in the {message.guild.name} server {ctime(newMessage.delivery_time)} {localtime(newMessage.delivery_time).tm_zone}", color=0x00ff00)
            embed.add_field(name="Message ID", value=f"{newMessage.id}", inline=True)
            await message.channel.send(embed=embed)

        if message.guild.id in delayed_messages:
            delayed_messages[message.guild.id].append(newMessage)
        else:
            delayed_messages[message.guild.id] = [newMessage]

        await schedule_delay_message(newMessage)

def replace_mentions(content, guild_id):
        guild = discord.utils.get(client.guilds, id=int(guild_id))

        for mention in re.finditer(r'{([^}]+)}', content):
            if mention.group(1) == 'everyone':
                mention_replace = '@everyone'
            elif mention.group(1) == 'here':
                mention_replace = '@here'
            else:
                try:
                    mention_replace = discord.utils.get(guild.roles,name=mention.group(1)).mention
                except:
                    # TODO: try searching for user mention.group(1)
                    raise Exception(f"Cannot find role {mention.group(1)}")

            content = re.sub(f"{{{re.escape(mention.group(1))}}}", mention_replace, content)

        return content

async def schedule_delay_message(message):

    guild = message.guild

    if message.delivery_time == 0:
        delay = 0
    else:
        delay = float(message.delivery_time) - float(time())
    if float(delay) < 0:
        return
    await asyncio.sleep(int(delay))

    # after sleep, make sure message has not been canceled
    if guild.id in delayed_messages:
        if message in delayed_messages[guild.id]:

            # we have to replace mentions now because the content may have changed while we were sleeping
            content = message.content
            try:
                content = replace_mentions(content, guild.id)
            except:
                # At this point, we'll just leave {role} in the message
                pass
            await message.delivery_channel.send(content)
            delayed_messages[guild.id].remove(message)
            if len(delayed_messages[guild.id]) < 1:
                del delayed_messages[guild.id]
            delete_from_db(message.id)

async def list_delay_messages(message):
    try:
        guild_id = message.guild.id
    except:
        return

    if guild_id in delayed_messages and len(delayed_messages[guild_id]) > 0:
        embed=discord.Embed(title="Scheduled Messages ==================================")
        delayed_messages[guild_id].sort(key=attrgetter('delivery_time'))
        count = 0
        for msg in delayed_messages[guild_id]:
            embed.add_field(name="ID", value=f"{msg.id}", inline=True)
            embed.add_field(name="Author", value=f"{msg.author.name}", inline=True)
            embed.add_field(name="Channel", value=f"{msg.delivery_channel.name}", inline=True)
            if round((msg.delivery_time - time())/60, 1) < 0:
                embed.add_field(name="Delivery failed", value=f"{str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{ctime(msg.delivery_time)} {localtime(msg.delivery_time).tm_zone}", inline=False)
            count += 1
            if count == 6:
                await message.channel.send(embed=embed)
                embed=discord.Embed(title="Scheduled Messages (continued) ======================")
                count = 0
        if count != 0:
            await message.channel.send(embed=embed)
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def list_all_delay_messages(message):
    if len(delayed_messages) > 0:
        embed=discord.Embed(title="Scheduled Messages ==================================")
        count = 0
        for guild_id in delayed_messages:
            delayed_messages[guild_id].sort(key=attrgetter('delivery_time'))
            for msg in delayed_messages[guild_id]:
                embed.add_field(name="ID", value=f"{msg.id}", inline=True)
                embed.add_field(name="Author", value=f"{msg.author.name}", inline=True)
                embed.add_field(name="Server - Channel", value=f"{client.get_guild(guild_id)} - {msg.delivery_channel.name}", inline=True)
                if round((msg.delivery_time - time())/60, 1) < 0:
                    embed.add_field(name="Delivery failed", value=f"{str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago", inline=False)
                else:
                    embed.add_field(name="Deliver", value=f"{ctime(msg.delivery_time)} {localtime(msg.delivery_time).tm_zone}", inline=False)
                count += 1
                if count == 6:
                    await message.channel.send(embed=embed)
                    embed=discord.Embed(title="Scheduled Messages (continued) ======================")
                    count = 0
        if count != 0:
            await message.channel.send(embed=embed)
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_delay_message(message, msg_num):
    message_found = False
    for guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                content = f"**Author:**  {msg.author.name}\n"
                content += f"**Deliver to:**  {msg.delivery_channel.name}\n"
                if round((msg.delivery_time - time())/60, 1) < 0:
                    content += f"**Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
                else:
                    content += f"**Deliver:**  {ctime(msg.delivery_time)} {localtime(msg.delivery_time).tm_zone}\n"
                content += msg.content
                await message.channel.send(content)
                message_found = True
    if not message_found:
        await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

async def send_delay_message(message, msg_num):
    try:
        guild_id = message.guild.id
    except:
        return

    message_found = False
    if guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                msg.delivery_time = 0

                await schedule_delay_message(msg)

                await message.channel.send(embed=discord.Embed(description="Message sent", color=0x00ff00))
                message_found = True
        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def edit_delay_message(message, message_id, delay, channel, content):
    try:
        guild_id = message.guild.id
    except:
        return

    if not delay and not channel and not message:
        await show_help(message.channel)
        return

    if delay:
        if re.search(r'^-?\d+$', delay):
            if delay == '0':
                delivery_time = 0
            else:
                delivery_time = float(time()) + int(delay) * 60
        else:
            try:
                delivery_time = datetime.strptime(delay, '%Y-%m-%d %H:%M').timestamp()
            except:
                await message.channel.send(embed=discord.Embed(description=f"{delay} is not a valid DateTime", color=0xff0000))
                return

    if channel:
        try:
            delivery_channel = discord.utils.get(message.guild.channels, name=channel)
            if not delivery_channel:
                raise Exception()
        except:
            await message.channel.send(embed=discord.Embed(description=f"Cannot find {channel} channel", color=0xff0000))
            return

    if content:
        #Make sure {roles} exist
        try:
            replace_mentions(content, message.guild.id)
        except Exception as e:
            await message.channel.send(embed=discord.Embed(description=f"{str(e)}", color=0xff0000))
            return

    message_found = False

    if guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == message_id:
                embed = discord.Embed(description="Message edited", color=0x00ff00)
                if channel:
                    msg.delivery_channel = delivery_channel
                    embed.add_field(name="Channel", value=f"{msg.delivery_channel.name}", inline=False)
                if content:
                    msg.content = content
                if delay:
                    newMessage =  DelayedMessage(msg.guild, msg.delivery_channel, float(delivery_time), msg.author, msg.content, msg.id)
                    if message.guild.id in delayed_messages:
                        delayed_messages[message.guild.id].append(newMessage)
                    else:
                        delayed_messages[message.guild.id] = [newMessage]
                    delayed_messages[guild_id].remove(msg)
                    if delivery_time == 0:
                        embed.add_field(name="Deliver", value="Now", inline=False)
                    else:
                        embed.add_field(name="Deliver", value=f"{ctime(newMessage.delivery_time)} {localtime(newMessage.delivery_time).tm_zone}", inline=False)
                    msg = newMessage

                update_db(msg)

                message_found = True
                await message.channel.send(embed=embed)

                if delay:
                    await schedule_delay_message(msg)

        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def cancel_all_delay_message_request(message):
    try:
        guild_id = message.guild.id
    except:
        return

    # Confirm cancel all messages
    confirmation_message = await message.channel.send(embed=discord.Embed(description="Cancel all messages?\n\n✅ Yes\n\n❌ No", color=0x0000ff))
    await confirmation_message.add_reaction('✅')
    await confirmation_message.add_reaction('❌')

    confirmation_request = ConfirmationRequest(confirmation_message, message.author)
    requests_to_cancel_all[confirmation_message.id] = confirmation_request

    await asyncio.sleep(int(10))

    try:
        await confirmation_message.remove_reaction('✅', client.user)
        await confirmation_message.remove_reaction('❌', client.user)
    except:
        pass

    requests_to_cancel_all.pop(confirmation_message.id)

async def cancel_all_delay_message(confirmation_request):
    await confirmation_request.confirmation_message.channel.send(embed=discord.Embed(description="TODO:  Implement cancel_all_delay_message", color=0x00ff00))

async def cancel_delay_message(message, msg_num):
    try:
        guild_id = message.guild.id
    except:
        return

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
    Show the contents of the message identified by <message-id>

    `~giggle send <message-id>`
    Send message identified by <message-id>
    immediately and remove it from the queue

    `~giggle edit <message-id> <date-time> channel=<channel>`
    `<message>`
    Edit message identified by <message-id>.
    <date-time> may be either a date as specified above or a number of minutes from now.
    If not specified, the current delivery time will be used.
    channel=<channel> is optional.  If not specified, the current delivery channel will be used.
    <message> is optional.  If specified, it will replace the body of the current message.

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

    if re.search(r'^~giggle +listall *$', message.content) and message.author.id == 669370838478225448:
        await list_all_delay_messages(message)
        return

    if re.search(r'^~giggle +list *$', message.content):
        await list_delay_messages(message)
        return

    match = re.search(r'^~giggle +show +(\S+) *$', message.content)
    if match:
        await show_delay_message(message, match.group(1))
        return

    match = re.search(r'^~giggle +(cancel|delete|remove|clear) +all *$', message.content)
    if match:
        await cancel_all_delay_message_request(message)
        return

    match = re.search(r'^~giggle +(cancel|delete|remove|clear) +(\S+) *$', message.content)
    if match:
        await cancel_delay_message(message, match.group(2))
        return

    match = re.search(r'^~giggle +send +(\S+) *$', message.content)
    if match:
        await send_delay_message(message, match.group(1))
        return

    match = re.search(r'^~giggle +edit +(\S+)(( +)(\d{4}-\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}|-?\d+))?(( +channel=)(\S+))? *((\n)(.*))?$', message.content, re.MULTILINE|re.DOTALL)
    if match:
        await edit_delay_message(message, match.group(1), match.group(4), match.group(7), match.group(10))
        return

    match = re.search(r'^~giggle +(\d{4}-\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}|-?\d+)(( +channel=)(\S+))? *((\n)(.+))$', message.content, re.MULTILINE|re.DOTALL)
    if match:
        await process_delay_message(message, match.group(1), match.group(4), match.group(7))
        return

    if re.search(r'^~giggle +resume *$', message.content) and message.author.id == 669370838478225448:
        await load_from_db()
        await list_all_delay_messages(message)
        return

    if re.search(r'^~giggle', message.content):
        await show_help(message.channel)
        return

@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in requests_to_cancel_all:
        users = await reaction.users().flatten()
        if(reaction.emoji == '✅' and user in users):
            cancel_all_delay_message(requests_to_cancel_all.pop(reaction.message.id))
    return

@client.event
async def on_guild_join(guild):
    user = client.get_user(669370838478225448)
    await user.send(f"{client.user.name} bot joined {guild.name}")

client.run(settings.bot_token)
