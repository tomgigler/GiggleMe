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
timezones = {}
users = {}

def giggleDB():
    return mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

class DelayedMessage:
    def __init__(self, id, guild_id, delivery_channel_id, delivery_time, author_id, description, content):
        self.id = id
        self.guild_id = guild_id
        self.delivery_channel_id = delivery_channel_id
        self.delivery_time = delivery_time
        self.author_id = author_id
        self.description = description
        self.content = content

    def guild(self):
        return discord.utils.get(client.guilds, id=self.guild_id)

    def delivery_channel(self):
        guild = discord.utils.get(client.guilds, id=self.guild_id)
        return discord.utils.get(guild.text_channels, id=self.delivery_channel_id)

    def author(self):
        return client.get_user(self.author_id)

    @staticmethod
    def id_gen(id):
        return md5((str(id)).encode('utf-8')).hexdigest()[:8]

class ConfirmationRequest:
    def __init__(self, confirmation_message, member):
        self.confirmation_message = confirmation_message
        self.member = member

class TimeZone:
    def __init__(self, offset, name):
        self.offset = offset
        self.name = name

class User:
    def __init__(self, name, timezone, last_message_id=None):
        self.name = name
        self.timezone = timezone
        self.last_message_id = last_message_id
        
    def set_last_message(self, user_id, message_id):
        mydb = giggleDB()

        sql = "UPDATE users SET last_message_id = %s WHERE user = %s"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (message_id, user_id))
        self.last_message_id = message_id
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def save(self, user_id):
        mydb = giggleDB()

        sql = "INSERT into users values ( %s, %s, %s, %s )"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (user_id, self.name, self.timezone, self.last_message_id))
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

def local_time_to_utc(user_id, time):
    if users[user_id].timezone:
        return time - 3600 * timezones[users[user_id].timezone].offset
    else:
        return time

def display_localized_time(user_id, time):
    if user_id in users and users[user_id].timezone:
        return f"{ctime(time + 3600 * timezones[users[user_id].timezone].offset)} {users[user_id].timezone}"
    else:
        return f"{ctime(time)} {localtime(time).tm_zone}"

def insert_into_db(message):
    mydb = giggleDB()

    mycursor = mydb.cursor()
    sql = "INSERT INTO messages values (%s, %s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, (message.id, message.guild_id, message.delivery_channel_id, message.delivery_time, message.author_id, message.content, message.description))
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

def update_db(message):
    mydb = giggleDB()

    mycursor = mydb.cursor()
    sql = "UPDATE messages SET guild_id = %s, delivery_channel_id = %s, delivery_time =  %s, author_id = %s, content = %s, description = %s WHERE id = %s"
    mycursor.execute(sql, (message.guild_id, message.delivery_channel_id, message.delivery_time, message.author_id, message.content, message.description, message.id))
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

def delete_from_db(id):
    mydb = giggleDB()

    mycursor = mydb.cursor()
    mycursor.execute(f"DELETE FROM messages WHERE id='{id}'")
    mydb.commit()
    mycursor.close()
    mydb.disconnect()

async def load_from_db():
    mydb = giggleDB()

    message_id_list = list()
    for guild_id in delayed_messages:
        for message_id in delayed_messages[guild_id]:
            message_id_list.append(message_id)
    loop = asyncio.get_event_loop()
    mycursor = mydb.cursor()

    mycursor.execute("select * from messages")

    for msg in mycursor.fetchall():
        message_id = msg[0]
        guild_id = msg[1]
        delivery_channel_id = msg[2]
        delivery_time = msg[3]
        author_id = msg[4]
        content = msg[5]
        description = msg[6]

        if message_id not in message_id_list:

            newMessage =  DelayedMessage(message_id, guild_id, delivery_channel_id, delivery_time, author_id, description, content)

            if guild_id not in delayed_messages:
                delayed_messages[guild_id] = {}
            delayed_messages[guild_id][message_id] = newMessage

            loop.create_task(schedule_delay_message(newMessage))

        else:
            for g_id in delayed_messages:
                if message_id in delayed_messages[g_id]:
                    # TODO:  If guild_id changes in the database, we need to move the message in the dict
                    # that may have an impact on the code dealing with delivery_time change below
                    delayed_messages[g_id][message_id].guild_id = guild_id
                    delayed_messages[g_id][message_id].delivery_channel_id = delivery_channel_id
                    delayed_messages[g_id][message_id].author_id = author_id
                    delayed_messages[g_id][message_id].content = content
                    delayed_messages[g_id][message_id].description = description

                    if delayed_messages[g_id][message_id].delivery_time != delivery_time:
                        delayed_messages[g_id][message_id].delivery_time = delivery_time

                        newMessage =  DelayedMessage(message_id, guild_id, delivery_channel_id, delivery_time, author_id, description, content)
                        if g_id not in delayed_messages:
                            delayed_messages[g_id] = {}
                        delayed_messages[g_id][message_id] = newMessage
                        loop.create_task(schedule_delay_message(newMessage))

    mycursor.close()
    mydb.disconnect()

    load_timezones_and_users()

def load_timezones_and_users():
    mydb = giggleDB()

    mycursor = mydb.cursor()

    mycursor.execute("select * from timezones")
    for tz in mycursor.fetchall():
        timezones[tz[0]] = TimeZone(tz[1], tz[2])

    mycursor.execute("select * from users")
    for user in mycursor.fetchall():
        users[user[0]] = User(user[1], user[2], user[3])

    mycursor.close()
    mydb.disconnect()

async def process_delay_message(message, delay, channel, description, content):

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
                delivery_time = time() + int(delay) * 60
        else:
            try:
                delivery_time = local_time_to_utc(message.author.id, datetime.strptime(delay, '%Y-%m-%d %H:%M').timestamp())
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
        newMessage =  DelayedMessage(DelayedMessage.id_gen(message.id), message.guild.id, delivery_channel.id, delivery_time, message.author.id, description, content)
        insert_into_db(newMessage)
        if delivery_time == 0:
            await message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.name} channel in the {message.guild.name} server now", color=0x00ff00))
        else:
            embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.name} channel in the {message.guild.name} server {display_localized_time(message.author.id, newMessage.delivery_time)}", color=0x00ff00)
            embed.add_field(name="Message ID", value=f"{newMessage.id}", inline=True)
            await message.channel.send(embed=embed)

        if message.guild.id not in delayed_messages:
            delayed_messages[message.guild.id] = {}
        delayed_messages[message.guild.id][newMessage.id] = newMessage

        if message.author.id not in users:
            users[message.author.id] = User(message.author.name, None)
            users[message.author.id].save(message.author.id)

        users[message.author.id].set_last_message(message.author.id, newMessage.id)
        
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

    guild = message.guild()

    if message.delivery_time == 0:
        delay = 0
    else:
        delay = message.delivery_time - time()
    if delay < 0:
        return
    await asyncio.sleep(int(delay))

    # after sleep, make sure message has not been canceled
    if guild.id in delayed_messages:
        if message.id in delayed_messages[guild.id] and delayed_messages[guild.id][message.id] == message:

            # we have to replace mentions now because the content may have changed while we were sleeping
            content = message.content
            try:
                content = replace_mentions(content, guild.id)
            except:
                # At this point, we'll just leave {role} in the message
                pass
            await message.delivery_channel().send(content)
            delayed_messages[guild.id].pop(message.id)
            if len(delayed_messages[guild.id]) < 1:
                del delayed_messages[guild.id]
            delete_from_db(message.id)

async def list_delay_messages(message):
    if message.guild.id in delayed_messages and len(delayed_messages[message.guild.id]) > 0:
        output = "> \n> **====================**\n>  **Scheduled Messages**\n> **====================**\n"
        sorted_messages = {k: v for k, v in sorted(delayed_messages[message.guild.id].items(), key=lambda item: item[1].delivery_time)}

        for msg_id in sorted_messages:
            msg = delayed_messages[message.guild.id][msg_id]
            output += f"> \n> **ID:**  {msg.id}\n"
            output += f"> **Author:**  {msg.author().name}\n"
            output += f"> **Channel:**  {msg.delivery_channel().name}\n"
            if round((msg.delivery_time - time())/60, 1) < 0:
                output += f"> **Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
            else:
                output += f"> **Deliver:**  {display_localized_time(message.author.id, msg.delivery_time)}\n"
            output += f"> **Description:**  {msg.description}\n"
        await message.channel.send(output + "> \n> **====================**\n")
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def list_all_delay_messages(message):
    if len(delayed_messages) > 0:
        output = "> \n> **====================**\n>  **Scheduled Messages**\n> **====================**\n"
        count = 0
        for guild_id in delayed_messages:
            for msg_id in delayed_messages[guild_id]:
                msg = delayed_messages[guild_id][msg_id]
                output += f"> \n> **ID:**  {msg.id}\n"
                output += f"> **Author:**  {msg.author().name}\n"
                output += f"> **Server:**  {msg.guild().name}\n"
                output += f"> **Channel:**  {msg.delivery_channel().name}\n"
                if round((msg.delivery_time - time())/60, 1) < 0:
                    output += f"> **Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
                else:
                    output += f"> **Deliver:**  {display_localized_time(message.author.id, msg.delivery_time)}\n"
        await message.channel.send(output + "> \n> **====================**\n")
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def display_timezones(message):
    output = "**Available Time Zones**\n**=============================**\n"
    for tz in timezones:
        offset = f"{timezones[tz].offset}"
        if timezones[tz].offset > 0:
            offset = "+" + offset
        output += f"**{tz}**  -  {timezones[tz].name}  -  UTC {offset}\n"
    output += f"\nDon't see your time zone?  DM **{client.user.mention}** and ask me to add it!"
    await message.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def show_user_timezone(message):
    if message.author.id in users and users[message.author.id].timezone:
        output = f"Your time zone is currently set to:  **{users[message.author.id].timezone}**"
    else:
        output = "Your time zone is not set.  You are using the default time zone (UTC)"
    await message.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def set_user_timezone(message, tz):
    if tz in timezones:
        mydb = giggleDB()

        if message.author.id in users:
            sql = "UPDATE users SET timezone = %s, name = %s WHERE user = %s"
        else:
            sql = "INSERT INTO users ( timezone, name, user ) values ( %s, %s, %s )"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (tz, message.author.name, message.author.id))
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

        if message.author.id not in users:
            users[message.author.id] = User(message.author.name, tz)
        users[message.author.id].timezone = tz
        await message.channel.send(embed=discord.Embed(description=f"Your time zone has been set to {tz}", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description=f"Time zone **{tz}** not found\nTo see a list of available time zones:\n`~giggle timezones`", color=0xff0000))

async def show_delay_message(message, msg_num):
    message_found = False
    content = ""
    if msg_num == 'last':
        if message.author.id in users:
            msg_num = users[message.author.id].last_message_id
            content += f"**ID:**  {msg_num}\n"
    for guild_id in delayed_messages:
        for msg_id in delayed_messages[guild_id]:
            if msg_id == msg_num:
                msg = delayed_messages[guild_id][msg_id]
                content += f"**Author:**  {msg.author().name}\n"
                content += f"**Deliver to:**  {msg.delivery_channel().name}\n"
                if round((msg.delivery_time - time())/60, 1) < 0:
                    content += f"**Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
                else:
                    content += f"**Deliver:**  {display_localized_time(message.author.id, msg.delivery_time)}\n"
                content += f"**Description:**  {msg.description}\n"
                content += msg.content
                await message.channel.send(content)
                message_found = True
    if not message_found:
        await message.channel.send(embed=discord.Embed(description=f"Message {msg_num} not found", color=0x00ff00))

async def send_delay_message(message, msg_num):
    if message.guild.id in delayed_messages:
        if msg_num in delayed_messages[message.guild.id]:
            msg = delayed_messages[message.guild.id][msg_num]
            msg.delivery_time = 0

            await schedule_delay_message(msg)

            await message.channel.send(embed=discord.Embed(description="Message sent", color=0x00ff00))
        else:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def edit_delay_message(message, message_id, delay, channel, description, content):
    if not delay and not channel and not description and not content:
        await message.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`~giggle help`"))
        return

    if delay:
        if re.search(r'^-?\d+$', delay):
            if delay == '0':
                delivery_time = 0
            else:
                delivery_time = time() + int(delay) * 60
        else:
            try:
                delivery_time = local_time_to_utc(message.author.id, datetime.strptime(delay, '%Y-%m-%d %H:%M').timestamp())
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

    if message.guild.id in delayed_messages:
        if message_id in delayed_messages[message.guild.id]:
            msg = delayed_messages[message.guild.id][message_id]
            embed = discord.Embed(description="Message edited", color=0x00ff00)
            if channel:
                msg.delivery_channel_id = delivery_channel.id
                embed.add_field(name="Channel", value=f"{delivery_channel.name}", inline=False)
            if description:
                msg.description = description
                embed.add_field(name="Description", value=f"{description}", inline=False)
            if content:
                msg.content = content
            if delay:
                loop = asyncio.get_event_loop()
                newMessage =  DelayedMessage(msg.id, msg.guild_id, msg.delivery_channel_id, delivery_time, msg.author_id, msg.description, msg.content)
                if message.guild.id not in delayed_messages:
                    delayed_messages[message.guild.id] = {}
                delayed_messages[message.guild.id][msg.id] = newMessage
                if delivery_time == 0:
                    embed.add_field(name="Deliver", value="Now", inline=False)
                else:
                    embed.add_field(name="Deliver", value=f"{display_localized_time(message.author.id, newMessage.delivery_time)}", inline=False)
                loop.create_task(schedule_delay_message(newMessage))
                update_db(newMessage)
            else:
                update_db(msg)

            if message.author.id not in users:
                users[message.author.id] = User(message.author.name, None)
                users[message.author.id].save(message.author.id)

            users[message.author.id].set_last_message(message.author.id, newMessage.id)
        
            await message.channel.send(embed=embed)

        else:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def cancel_all_delay_message_request(message):

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

    requests_to_cancel_all.pop(confirmation_message.id, None)

async def cancel_all_delay_message(confirmation_request):
    if confirmation_request:
        guild_id = confirmation_request.confirmation_message.guild.id
        message_count = 0
        if guild_id in delayed_messages:
            messages_to_remove = []
            for msg_id in delayed_messages[guild_id]:
                messages_to_remove.append(delayed_messages[guild_id][msg_id])
            for msg in messages_to_remove:
                if msg.author_id == confirmation_request.member.id:
                    delayed_messages[guild_id].pop(msg.id)
                    if len(delayed_messages[guild_id]) < 1:
                        del delayed_messages[guild_id]
                    message_count += 1
                    delete_from_db(msg.id)
    if message_count > 0:
        await confirmation_request.confirmation_message.channel.send(embed=discord.Embed(description=f"Canceled {message_count} messages", color=0x00ff00))
    else:
        await confirmation_request.confirmation_message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def cancel_delay_message(message, msg_num):
    message_found = False
    if message.guild.id in delayed_messages:
        if msg_num in delayed_messages[message.guild.id]:
            delayed_messages[message.guild.id].pop(msg_num)
            if len(delayed_messages[message.guild.id]) < 1:
                del delayed_messages[message.guild.id]
            await message.channel.send(embed=discord.Embed(description="Message canceled", color=0x00ff00))
            delete_from_db(msg_num)
        else:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_help(channel):
    helpOutput = """To schedule <message> to be delivered to <channel> at <time>:

    `~giggle <time> channel=<channel> desc="<brief description>"`
    `<message>`

    <time> may be either a number of minutes from now
    or a DateTime of the format YYYY-MM-DD HH:MM
    All times are UTC

    desc is an optional description of the message
    If included, it must come after channel

    The following commands may be used to manage scheduled messages:

    `~giggle list`
    Display a list of currently scheduled messages

    `~giggle show <message-id>`
    Show the contents of the message identified by <message-id>
    Note:  `last` may be used as <message-id> to reference your most recently scheduled message

    `~giggle send <message-id>`
    Send message identified by <message-id>
    immediately and remove it from the queue

    `~giggle edit <message-id> <date-time> channel=<channel> desc="<desc>"`
    `<message>`
    Edit message identified by <message-id>.
    <date-time> may be either a date as specified above or a number of minutes from now.
    If not specified, the current delivery time will be used.
    channel=<channel> is optional.  If not specified, the current delivery channel will be used.
    desc="<desc>" is optional.  If both channel and desc are included, desc must come after channel
    <message> is optional.  If specified, it will replace the body of the current message.

    `~giggle cancel <message-id>`
    Cancel message identified by <message-id>

    `~giggle cancel all`
    Cancel all delayed messages scheduled by you.  You will be prompted for confirmation

    `~giggle timezone <time zone>`
    Set your time zone to <time zone>

    `~giggle timezone`
    Display your current time zone

    `~giggle timezones`
    Display a list of available time zones

    `~giggle help`
    Show this help"""
    await channel.send(embed=discord.Embed(description=helpOutput))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if isinstance(message.channel, discord.channel.DMChannel):
        user = client.get_user(669370838478225448)
        await user.send(f"{message.author.mention} said {message.content}")

    try:
        if not message.author.guild_permissions.mute_members and message.author.id != 669370838478225448:
            return
    except:
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

    match = re.search(r'^~giggle +edit +(\S+)(( +)(\d{4}-\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}|-?\d+))?(( +channel=)(\S+))?(( +desc=")([^"]+)")? *((\n)(.*))?$', message.content, re.MULTILINE|re.DOTALL)
    if match:
        await edit_delay_message(message, match.group(1), match.group(4), match.group(7), match.group(10), match.group(13))
        return

    match = re.search(r'^~giggle +(\d{4}-\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}|-?\d+)(( +channel=)(\S+))?(( +desc=")([^"]+)")? *((\n)(.+))$', message.content, re.MULTILINE|re.DOTALL)
    if match:
        await process_delay_message(message, match.group(1), match.group(4), match.group(7), match.group(10))
        return

    if re.search(r'^~giggle +resume *$', message.content) and message.author.id == 669370838478225448:
        await client.change_presence(activity=discord.Game('with thegigler'))
        await load_from_db()
        await list_all_delay_messages(message)
        return

    if re.search(r'^~giggle +help *$', message.content):
        await show_help(message.channel)
        return

    match = re.search(r'^~giggle +timezone( +([A-Z][A-Z][A-Z]))? *$', message.content)
    if match:
        if match[2]:
            await set_user_timezone(message, match[2])
        else:
            await show_user_timezone(message)
        return

    if re.search(r'^~giggle +timezones *$', message.content):
        await display_timezones(message)
        return

    if re.search(r'^~giggle', message.content):
        await message.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`~giggle help`"))
        return

@client.event
async def on_reaction_add(reaction, user):
    found = False
    if reaction.message.id in requests_to_cancel_all:
        if(user == requests_to_cancel_all[reaction.message.id].member):
            found = True
            if reaction.emoji == '✅':
                await cancel_all_delay_message(requests_to_cancel_all.pop(reaction.message.id, None))
            else:
                confirmation_message = requests_to_cancel_all.pop(reaction.message.id, None)

    if found:
        try:
            await reaction.message.remove_reaction('✅', client.user)
            await reaction.message.remove_reaction('❌', client.user)
        except:
            pass

@client.event
async def on_guild_join(guild):
    user = client.get_user(669370838478225448)
    await user.send(f"{client.user.name} bot joined {guild.name}")

load_timezones_and_users()

client.run(settings.bot_token)
