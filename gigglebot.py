#!/usr/bin/env python
import discord
import re
import asyncio
from settings import bot_token
from datetime import datetime
from time import time
from operator import attrgetter
import help
from confirm import confirm_request, process_reaction
import gigtz
from gigdb import db_connect
from giguser import User, load_users, users
from delayed_message import DelayedMessage

client = discord.Client()
delayed_messages = {}

async def load_from_db(delayed_messages):
    mydb = db_connect()

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

        if message_id in delayed_messages:

            # TODO:  If guild_id changes in the database, we need to move the delayed_message in the dict
            # that may have an impact on the code dealing with delivery_time change below
            delayed_messages[message_id].guild_id = guild_id
            delayed_messages[message_id].delivery_channel_id = delivery_channel_id
            delayed_messages[message_id].author_id = author_id
            delayed_messages[message_id].content = content
            delayed_messages[message_id].description = description

            if delayed_messages[message_id].delivery_time != delivery_time:
                delayed_messages[message_id].delivery_time = delivery_time

                newMessage =  DelayedMessage(message_id, guild_id, delivery_channel_id, delivery_time, author_id, description, content)
                if g_id not in delayed_messages:
                    delayed_messages = {}
                delayed_messages[message_id] = newMessage
                loop.create_task(schedule_delay_message(newMessage))
        else:

            newMessage =  DelayedMessage(message_id, guild_id, delivery_channel_id, delivery_time, author_id, description, content)

            delayed_messages[message_id] = newMessage

            loop.create_task(schedule_delay_message(newMessage))

    mycursor.close()
    mydb.disconnect()

    gigtz.load_timezones()
    load_users()

async def process_delay_message(discord_message, delay, channel, description, content):

    # get channel if provided
    if channel:
        delivery_channel = discord.utils.get(discord_message.guild.channels, name=channel)
        if not delivery_channel:
            await discord_message.channel.send(embed=discord.Embed(description=f"Cannot find {channel} channel", color=0xff0000))
            return
    else:
        # default to current channel
        delivery_channel = discord_message.channel

    try:
        # TODO:  for now, user needs manage_channels permissions in the target channel
        has_permission = discord_message.author.permissions_in(delivery_channel).manage_channels
    except:
        await discord_message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {delivery_channel.name}", color=0xff0000))
        return

    if not has_permission:
        await discord_message.channel.send(embed=discord.Embed(description=f"You do not have permission to send delayed messages in {delivery_channel.name}", color=0xff0000))
    else:
        if re.search(r'^-?\d+$', delay):
            if delay == '0':
                delivery_time = 0
            else:
                delivery_time = time() + int(delay) * 60
        else:
            try:
                delivery_time = gigtz.local_time_str_to_utc(delay, users[discord_message.author.id].timezone)
            except:
                await discord_message.channel.send(embed=discord.Embed(description=f"{delay} is not a valid DateTime", color=0xff0000))
                return

        #Make sure {roles} exist
        try:
            replace_mentions(content, discord_message.guild.id)
        except Exception as e:
            await discord_message.channel.send(embed=discord.Embed(description=f"{str(e)}", color=0xff0000))
            return

        # create new DelayedMessage
        newMessage =  DelayedMessage(DelayedMessage.id_gen(discord_message.id), discord_message.guild.id, delivery_channel.id, delivery_time, discord_message.author.id, description, content)
        newMessage.insert_into_db()
        if delivery_time == 0:
            await discord_message.channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.name} channel in the {discord_message.guild.name} server now", color=0x00ff00))
        else:
            embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.name} channel in the {discord_message.guild.name} server {gigtz.display_localized_time(newMessage.delivery_time, users[discord_message.author.id].timezone)}", color=0x00ff00)
            embed.add_field(name="Message ID", value=f"{newMessage.id}", inline=True)
            await discord_message.channel.send(embed=embed)

        delayed_messages[newMessage.id] = newMessage

        users[discord_message.author.id].set_last_message(discord_message.author.id, newMessage.id)

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

async def schedule_delay_message(delayed_message):

    guild = delayed_message.guild(client)

    if delayed_message.delivery_time == 0:
        delay = 0
    else:
        delay = delayed_message.delivery_time - time()
    if delay < 0:
        return
    await asyncio.sleep(int(delay))

    # after sleep, make sure delayed_message has not been canceled
    if delayed_message.id in delayed_messages and delayed_messages[delayed_message.id] == delayed_message:

        # we have to replace mentions now because the content may have changed while we were sleeping
        content = delayed_message.content
        try:
            content = replace_mentions(content, guild.id)
        except:
            # At this point, we'll just leave {role} in the content
            pass
        await delayed_message.delivery_channel(client).send(content)
        delayed_messages.pop(delayed_message.id)
        delayed_message.delete_from_db()

async def list_delay_messages(channel, author_id):
    count = 0
    total = 0
    output = "> \n> **====================**\n>  **Scheduled Messages**\n> **====================**\n"
    sorted_messages = {k: v for k, v in sorted(delayed_messages.items(), key=lambda item: item[1].delivery_time)}

    for msg_id in sorted_messages:
        msg = delayed_messages[msg_id]
        if msg.guild_id == channel.guild.id:
            output += f"> \n> **ID:**  {msg.id}\n"
            output += f"> **Author:**  {msg.author(client).name}\n"
            output += f"> **Channel:**  {msg.delivery_channel(client).name}\n"
            if round((msg.delivery_time - time())/60, 1) < 0:
                output += f"> **Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
            else:
                output += f"> **Deliver:**  {gigtz.display_localized_time(msg.delivery_time, users[author_id].timezone)}\n"
            output += f"> **Description:**  {msg.description}\n"
            count += 1
            total += 1
            if count == 4:
                await channel.send(output)
                output = ""
                count = 0
    if count > 0:
        await channel.send(output)
    if total > 0:
        await channel.send("> \n> **====================**\n")
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def list_all_delay_messages(channel, author_id):
    if len(delayed_messages) > 0:
        output = "> \n> **====================**\n>  **Scheduled Messages**\n> **====================**\n"
        sorted_messages = {k: v for k, v in sorted(delayed_messages.items(), key=lambda item: item[1].delivery_time)}
        count = 0
        for msg_id in sorted_messages:
            msg = delayed_messages[msg_id]
            output += f"> \n> **ID:**  {msg.id}\n"
            output += f"> **Author:**  {msg.author(client).name}\n"
            output += f"> **Server:**  {msg.guild(client).name}\n"
            output += f"> **Channel:**  {msg.delivery_channel(client).name}\n"
            if round((msg.delivery_time - time())/60, 1) < 0:
                output += f"> **Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
            else:
                output += f"> **Deliver:**  {gigtz.display_localized_time(msg.delivery_time, users[author_id].timezone)}\n"
            output += f"> **Description:**  {msg.description}\n"
            count += 1
            if count == 4:
                await channel.send(output)
                output = ""
                count = 0
        if count != 0:
            await channel.send(output)
        await channel.send("> \n> **====================**\n")
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_user_timezone(channel, author_id):
    if author_id in users and users[author_id].timezone:
        output = f"Your time zone is currently set to:  **{users[author_id].timezone}**"
    else:
        output = "Your time zone is not set.  You are using the default time zone (UTC)"
    await channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def set_user_timezone(channel, author, tz):
    if tz in gigtz.timezones:
        mydb = db_connect()

        if author.id in users:
            sql = "UPDATE users SET timezone = %s, name = %s WHERE user = %s"
        else:
            sql = "INSERT INTO users ( timezone, name, user ) values ( %s, %s, %s )"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (tz, author.name, author.id))
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

        users[author.id].timezone = tz
        await channel.send(embed=discord.Embed(description=f"Your time zone has been set to {tz}", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description=f"Time zone **{tz}** not found\nTo see a list of available time zones:\n`~giggle timezones`", color=0xff0000))

async def show_delayed_message(channel, author_id, msg_num, raw):
    content = ""
    if msg_num == 'last':
        if author_id in users:
            msg_num = users[author_id].last_message_id
            content += f"**ID:**  {msg_num}\n"
    if msg_num in delayed_messages:
        msg = delayed_messages[msg_num]
        content += f"**Author:**  {msg.author(client).name}\n"
        content += f"**Deliver to:**  {msg.delivery_channel(client).name}\n"
        if channel.guild.id != msg.guild_id:
            content += f"**Deliver in:**  {channel.guild.name}\n"
        if round((msg.delivery_time - time())/60, 1) < 0:
            content += f"**Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
        else:
            content += f"**Deliver:**  {gigtz.display_localized_time(msg.delivery_time, users[author_id].timezone)}\n"
        content += f"**Description:**  {msg.description}\n"
        content += msg.content
        await channel.send(content)
        if raw:
            await channel.send("```\n" + msg.content + "\n```")
        else:
            await channel.send(msg.content)
        message_found = True
    else:
        await channel.send(embed=discord.Embed(description=f"Message {msg_num} not found", color=0x00ff00))

async def send_delay_message(params):
    channel = params['channel']
    author = params['author']
    msg_num = params['msg_num']

    if msg_num == 'last' and author.id in users and users[author.id].last_message_id:
        msg_num = users[author.id].last_message_id
        await confirm_request(channel, author, f"Send message {msg_num} now?", 15, send_delay_message, {'channel': channel, 'author': author, 'msg_num': msg_num}, client)
        return

    if msg_num in delayed_messages:
        msg = delayed_messages[msg_num]
        msg.delivery_time = 0

        await schedule_delay_message(msg)

        await channel.send(embed=discord.Embed(description="Message sent", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

async def edit_delay_message(params):
    discord_message = params['discord_message']
    message_id = params['message_id']
    delay = params['delay']
    channel = params['channel']
    description = params['description']
    content = params['content']
    author = params['author']

    if not delay and not channel and not description and not content:
        await discord_message.channel.send(embed=discord.Embed(description="You must modify at least one of time, channel, description, or content"))
        return

    if message_id == 'last' and author.id in users and users[author.id].last_message_id:
        message_id = users[author.id].last_message_id
        await confirm_request(discord_message.channel, author, f"Edit message {message_id}?", 10, edit_delay_message,
            {'discord_message': discord_message, 'message_id': message_id, 'delay': delay, 'channel': channel, 'description': description, 'content': content, 'author': author}, client)
        return

    if delay:
        if re.search(r'^-?\d+$', delay):
            if delay == '0':
                delivery_time = 0
            else:
                delivery_time = time() + int(delay) * 60
        else:
            try:
                delivery_time = gigtz.local_time_str_to_utc(delay, users[discord_message.author.id].timezone)
            except:
                await discord_message.channel.send(embed=discord.Embed(description=f"{delay} is not a valid DateTime", color=0xff0000))
                return

    if channel:
        try:
            delivery_channel = discord.utils.get(discord_message.guild.channels, name=channel)
            if not delivery_channel:
                raise Exception()
        except:
            await discord_message.channel.send(embed=discord.Embed(description=f"Cannot find {channel} channel", color=0xff0000))
            return

    if content:
        #Make sure {roles} exist
        try:
            replace_mentions(content, discord_message.guild.id)
        except Exception as e:
            await discord_message.channel.send(embed=discord.Embed(description=f"{str(e)}", color=0xff0000))
            return

    if message_id in delayed_messages:
        msg = delayed_messages[message_id]
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
            delayed_messages[msg.id] = newMessage
            if delivery_time == 0:
                embed.add_field(name="Deliver", value="Now", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{gigtz.display_localized_time(newMessage.delivery_time, users[discord_message.author.id].timezone)}", inline=False)
            loop.create_task(schedule_delay_message(newMessage))
            newMessage.update_db()
        else:
            msg.update_db()

        await discord_message.channel.send(embed=embed)

    else:
        await discord_message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

async def cancel_all_delay_message(params):
    member = params['member']
    channel = params['channel']
    
    message_count = 0
    messages_to_remove = []
    for msg_id in delayed_messages:
        messages_to_remove.append(delayed_messages[msg_id])
    for msg in messages_to_remove:
        if msg.author_id == member.id  and msg.delivery_channel_id == channel.id:
            delayed_messages.pop(msg.id)
            message_count += 1
            msg.delete_from_db()
    if message_count > 0:
        await channel.send(embed=discord.Embed(description=f"Canceled {message_count} messages", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def cancel_delayed_message(params):
    channel = params['channel']
    author = params['author']
    msg_num = params['msg_num']
    if msg_num == 'all':
        await confirm_request(channel, author, "Cancel all messages?", 10, cancel_all_delay_message, {'member': author, 'channel': channel}, client)
        return

    if msg_num == 'last' and author.id in users and users[author.id].last_message_id:
        msg_num = users[author.id].last_message_id
        await confirm_request(channel, author, f"Cancel message {msg_num}?", 15, cancel_delayed_message, {'channel': channel, 'author': author, 'msg_num': msg_num}, client)
        return

    message_found = False
    if msg_num in delayed_messages:
        delayed_messages.pop(msg_num).delete_from_db()
        await channel.send(embed=discord.Embed(description="Message canceled", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if isinstance(msg.channel, discord.channel.DMChannel):
        user = client.get_user(669370838478225448)
        await user.send(f"{msg.author.mention} said {msg.content}")

    try:
        if not msg.author.guild_permissions.mute_members and msg.author.id != 669370838478225448:
            return
    except:
        return

    if msg.author.id not in users:
        users[msg.author.id] = User(msg.author.name, None)
        users[msg.author.id].save(msg.author.id)

    if re.search(r'^~giggle +listall *$', msg.content) and msg.author.id == 669370838478225448:
        await list_all_delay_messages(msg.channel, msg.author.id)
        return

    if re.search(r'^~giggle +list *$', msg.content):
        await list_delay_messages(msg.channel, msg.author.id)
        return

    match = re.search(r'^~giggle +show( +(raw))?( +(\S+)) *$', msg.content)
    if match:
        await show_delayed_message(msg.channel, msg.author.id, match.group(4), match.group(2))
        return

    match = re.search(r'^~giggle +(cancel|delete|remove|clear) +(\S+) *$', msg.content)
    if match:
        await cancel_delayed_message({'channel': msg.channel, 'author': msg.author, 'msg_num': match.group(2)})
        return

    match = re.search(r'^~giggle +send +(\S+) *$', msg.content)
    if match:
        await send_delay_message({'channel': msg.channel, 'author': msg.author, 'msg_num': match.group(1)})
        return

    match = re.search(r'^~giggle +edit +(\S+)(( +)(\d{4}-\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?|-?\d+))?(( +channel=)(\S+))?(( +desc=")([^"]+)")? *((\n)(.*))?$', msg.content, re.MULTILINE|re.DOTALL)
    if match:
        await edit_delay_message({'discord_message': msg, 'message_id': match.group(1), 'delay': match.group(4),
            'channel': match.group(8), 'description': match.group(11), 'content': match.group(14), 'author': msg.author})
        return

    match = re.search(r'^~giggle +(\d{4}-\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?|-?\d+)(( +channel=)(\S+))?(( +desc=")([^"]+)")? *((\n)(.+))$', msg.content, re.MULTILINE|re.DOTALL)
    if match:
        await process_delay_message(msg, match.group(1), match.group(5), match.group(8), match.group(11))
        return

    if re.search(r'^~giggle +resume *$', msg.content) and msg.author.id == 669370838478225448:
        await client.change_presence(activity=discord.Game('with thegigler'))
        await load_from_db(delayed_messages)
        await list_all_delay_messages(msg.channel, msg.author.id)
        return

    match = re.search(r'^~giggle +help( +(\S+))? *$', msg.content)
    if match:
        await msg.channel.send(embed=discord.Embed(description=help.show_help(match.group(2))))
        return

    match = re.search(r'^~giggle +timezone( +([A-Z][A-Z][A-Z]))? *$', msg.content)
    if match:
        if match[2]:
            await set_user_timezone(msg.channel, msg.author, match[2])
        else:
            await show_user_timezone(msg.channel, msg.author.id)
        return

    if re.search(r'^~giggle +timezones *$', msg.content):
        await msg.channel.send(embed=discord.Embed(description=gigtz.display_timezones(client.user.mention), color=0x00ff00))
        return

    if re.search(r'^~giggle', msg.content):
        await msg.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`~giggle help`"))
        return

@client.event
async def on_reaction_add(reaction, user):
    await process_reaction(reaction, user, client)

@client.event
async def on_guild_join(guild):
    user = client.get_user(669370838478225448)
    await user.send(f"{client.user.name} bot joined {guild.name}")

gigtz.load_timezones()
load_users()

client.run(bot_token)
