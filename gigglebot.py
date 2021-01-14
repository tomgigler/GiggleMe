#!/usr/bin/env python
import discord
import re
import asyncio
from settings import bot_token
from datetime import datetime
from time import time
from operator import attrgetter
from traceback import format_exc
import help
from confirm import confirm_request, process_reaction
import gigtz
from gigdb import db_connect
import giguser
from delayed_message import DelayedMessage
from gigparse import parse_args, GigParseException
import gigvotes

client = discord.Client()
delayed_messages = {}
votes = gigvotes.GigVote()

def load_from_db(delayed_messages):
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
        repeat = msg[5]
        last_repeat_message = msg[6]
        content = msg[7]
        description = msg[8]

        if message_id in delayed_messages:

            # TODO:  If guild_id changes in the database, we need to move the delayed_message in the dict
            # that may have an impact on the code dealing with delivery_time change below
            delayed_messages[message_id].guild_id = guild_id
            delayed_messages[message_id].delivery_channel_id = delivery_channel_id
            delayed_messages[message_id].author_id = author_id
            delayed_messages[message_id].repeat = repeat
            delayed_messages[message_id].last_repeat_message = last_repeat_message
            delayed_messages[message_id].content = content
            delayed_messages[message_id].description = description

            if delayed_messages[message_id].delivery_time != delivery_time:
                delayed_messages[message_id].delivery_time = delivery_time

                newMessage =  DelayedMessage(message_id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, description, content)
                delayed_messages[message_id] = newMessage
                if delivery_time and delivery_time >= 0:
                    loop.create_task(schedule_delay_message(newMessage))
        else:

            newMessage =  DelayedMessage(message_id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, description, content)

            delayed_messages[message_id] = newMessage
            if delivery_time and delivery_time >= 0:
                loop.create_task(schedule_delay_message(newMessage))

        if delayed_messages[message_id].delivery_time and delayed_messages[message_id].delivery_time < 0:
            votes.load_proposal_votes(message_id)

    mycursor.close()
    mydb.disconnect()

    gigtz.load_timezones()
    giguser.load_users()

async def process_delay_message(params):
    guild = params.pop('guild', None)
    request_channel = params.pop('request_channel', None)
    request_message_id = params.pop('request_message_id', None)
    author_id = params.pop('author_id', None)
    delay = params.pop('delay', None)
    content = params.pop('content', None)
    channel = params.pop('channel', None)
    repeat = params.pop('repeat', None)
    description = params.pop('desc', None)
    from_template = params.pop('from_template', None)
    propose_in_channel_name = params.pop('propose_in_channel', None)
    required_approvals = params.pop('required_approvals', None)

    if params:
        if request_channel:
            await request_channel.send(embed=discord.Embed(description=f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help`", color=0xff0000))
        return

    if not content and not from_template:
        if request_channel:
            await request_channel.send(embed=discord.Embed(description=f"Message body required if not creating a message from a template\n\nTo see help type:\n\n`~giggle help`", color=0xff0000))
        return
    elif content and from_template:
        if request_channel:
            await request_channel.send(embed=discord.Embed(description=f"Message body not allowed when creating a message from a template\n\nTo see help type:\n\n`~giggle help`", color=0xff0000))
        return

    if from_template:
        if from_template not in delayed_messages:
            if request_channel:
                await request_channel.send(embed=discord.Embed(description=f"Cannot find template {from_template}", color=0xff0000))
            return
        content = delayed_messages[from_template].content
        if not channel:
            channel = delayed_messages[from_template].delivery_channel(client).name
        if not description:
            description = delayed_messages[from_template].description

    # validate repeat string
    if repeat:
        if not re.match('(minutes:\d+|hours:\d+|daily|weekly|monthly)(;skip_if=\d+)?$', repeat):
            if request_channel:
                await request_channel.send(embed=discord.Embed(description=f"Invalid repeat string `{repeat}`", color=0xff0000))
            return

    # get channel
    if channel:
        delivery_channel = discord.utils.get(guild.channels, name=channel)
        if not delivery_channel:
            try:
                delivery_channel = discord.utils.get(guild.channels, id=int(channel))
            except:
                pass
        if not delivery_channel:
            if request_channel:
                await request_channel.send(embed=discord.Embed(description=f"Cannot find {channel} channel", color=0xff0000))
            return
    else:
        # default to current channel
        delivery_channel = request_channel

    # get propose_in_channel
    if propose_in_channel_name:
        if delay == 'proposal':
            delivery_time = -1
            propose_in_channel = discord.utils.get(guild.channels, name=propose_in_channel_name)
            if not propose_in_channel:
                try:
                    propose_in_channel = discord.utils.get(guild.channels, id=int(propose_in_channel))
                except:
                    pass
            if not propose_in_channel:
                if request_channel:
                    await request_channel.send(embed=discord.Embed(description=f"Cannot find {propose_in_channel_name} channel", color=0xff0000))
                return
        else:
            await request_channel.send(embed=discord.Embed(description=f"Invalid command.  Parameter **propose_in_channel** may only be used with proposals\n\nTo see help type:\n\n`~giggle help proposal`", color=0xff0000))
            return
    elif delay == 'proposal':
        await request_channel.send(embed=discord.Embed(description=f"Parameter **propose_in_channel** is required with proposals\n\nTo see help type:\n\n`~giggle help proposal`", color=0xff0000))
        return

    # get required_approvals
    if required_approvals:
        if delay == 'proposal':
            if not re.match(r'\d+$', required_approvals) or int(required_approvals) == 0:
                await request_channel.send(embed=discord.Embed(description=f"Invalid value for **required_approvals**.  Must be a positive integer greater than 0\n\nTo see help type:\n\n`~giggle help proposal`", color=0xff0000))
                return
        else:
            await request_channel.send(embed=discord.Embed(description=f"Invalid command.  Parameter **required_approvals** may only be used with proposals\n\nTo see help type:\n\n`~giggle help proposal`", color=0xff0000))
            return
    else:
        required_approvals = '2'

    if delay == 'proposal':
        pass

    elif delay == 'template':
        delivery_time = None
        if repeat is not None:
            if request_channel:
                await request_channel.send(embed=discord.Embed(description="The repeat option may not be used when creating a template", color=0xff0000))
            return

    elif re.match(r'-?\d+$', delay):
        if delay == '0':
            delivery_time = 0
        else:
            delivery_time = time() + int(delay) * 60

    else:
        try:
            delivery_time = gigtz.local_time_str_to_utc(delay, giguser.users[author_id].timezone)
        except:
            try:
                delivery_time = gigtz.local_time_str_to_utc(f"{gigtz.get_current_year(giguser.users[author_id].timezone)}-{delay}", giguser.users[author_id].timezone)
            except:
                if request_channel:
                    await request_channel.send(embed=discord.Embed(description=f"{delay} is not a valid DateTime", color=0xff0000))
                return

    #Make sure {roles} exist
    try:
        replace_mentions(content, guild.id)
    except Exception as e:
        if request_channel:
            await request_channel.send(embed=discord.Embed(description=f"{str(e)}", color=0xff0000))
        return

    # create new DelayedMessage
    newMessage =  DelayedMessage(DelayedMessage.id_gen(request_message_id), guild.id, delivery_channel.id, delivery_time, author_id, repeat, None, description, content)
    newMessage.insert_into_db()

    delayed_messages[newMessage.id] = newMessage

    if not delivery_time >= 0:
        if request_channel:
            if delay == 'template':
                embed=discord.Embed(description=f"Your template has been created", color=0x00ff00)
                embed.add_field(name="Template ID", value=f"{newMessage.id}", inline=True)
                await request_channel.send(embed=embed)
            else:
                await propose_message(newMessage, propose_in_channel, request_channel, required_approvals)
        return
    elif delivery_time == 0:
        if request_channel:
            await request_channel.send(embed=discord.Embed(description=f"Your message will be delivered to the **{delivery_channel.name}** channel now", color=0x00ff00))
    elif request_channel:
        embed=discord.Embed(description=f"Your message will be delivered to the **{delivery_channel.name}** channel at {gigtz.display_localized_time(newMessage.delivery_time, giguser.users[author_id].timezone, giguser.users[author_id].format_24)}", color=0x00ff00)
        embed.add_field(name="Message ID", value=f"{newMessage.id}", inline=True)
        await request_channel.send(embed=embed)

    if author_id:
        giguser.users[author_id].set_last_message(newMessage.id)

    await schedule_delay_message(newMessage)

async def propose_message(msg, propose_in_channel, request_channel, required_approvals):
    votes.vote(msg.id, client.user.id, int(required_approvals))
    output = "> **A MESSAGE HAS BEEN PROPOSED**\n"
    output += f"> **Author:** {msg.author(client).name}\n"
    output += f"> **Channel:** {msg.delivery_channel(client).name}\n"
    output += "> **Current approvals:** 0\n"
    output += f"> **Required approvals:** {votes.get_required_approvals(msg.id, client.user.id)}\n"
    output += msg.content
    proposal_message = await propose_in_channel.send(output)
    await proposal_message.add_reaction('☑️')
    delayed_messages[msg.id].last_repeat_message = proposal_message.id
    delayed_messages[msg.id].update_db()
    embed=discord.Embed(description=f"Your message has been proposed in the **{propose_in_channel}** channel\n\nIt will be delivered to the **{msg.delivery_channel(client).name}** channel when it is approved", color=0x00ff00)
    embed.add_field(name="Proposal ID", value=f"{msg.id}", inline=True)
    await request_channel.send(embed=embed)

async def process_proposal_reaction(payload, msg_id, vote):
    if payload.user_id == client.user.id:
        return
    msg = delayed_messages[msg_id]
    votes.vote(msg_id, payload.user_id, vote)
    required_approvals = votes.get_required_approvals(msg_id, client.user.id)
    total_approvals = votes.vote_count(msg_id)
    output = f"> **Author:** {msg.author(client).name}\n"
    output += f"> **Channel:** {msg.delivery_channel(client).name}\n"

    if total_approvals < required_approvals:
        output = "> **A MESSAGE HAS BEEN PROPOSED**\n" + output
        output += f"> **Current approvals:** {total_approvals}\n"
        output += f"> **Required approvals:** {required_approvals}\n"
    else:
        output = "> **MESSAGE APPROVED AND SENT**\n" + output
        output += f"> **Sent:** {gigtz.display_localized_time(time(), giguser.users[msg.author_id].timezone, giguser.users[msg.author_id].format_24)}\n"
        output += f"> **Total approvals:** {required_approvals}\n"
        msg.last_repeat_message = None
        msg.delivery_time = 0
        msg.update_db()
        await schedule_delay_message(msg)

    output += msg.content
    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    await message.edit(content=output)

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

async def schedule_delay_message(msg):

    if msg.delivery_time == 0:
        delay = 0
        if msg.repeat:
            msg.delivery_time = time()
    else:
        delay = msg.delivery_time - time()
    if delay < 0:
        return
    await asyncio.sleep(int(delay))

    guild = msg.guild(client)

    # after sleep, make sure msg has not been canceled
    if msg.id in delayed_messages and delayed_messages[msg.id] == msg:

        # we have to replace mentions now because the content may have changed while we were sleeping
        content = msg.content
        try:
            content = replace_mentions(content, guild.id)
        except:
            # At this point, we'll just leave {role} in the content
            pass

        # If this is a repeating message, check for the previous delivery
        skip_delivery = False
        if msg.repeat is not None and msg.last_repeat_message is not None:
            match = re.match(r'(minutes:\d+|hours:\d+|daily|weekly|monthly);skip_if=(\d+)', msg.repeat)
            if match:
                skip_if = int(match.group(2))
            else:
                skip_if = 1
            async for old_message in msg.delivery_channel(client).history(limit=skip_if):
                if old_message.id == msg.last_repeat_message:
                    skip_delivery = True

            if skip_if != 0 and msg.last_repeat_message == msg.delivery_channel(client).last_message_id:
                try:
                    old_message = await msg.delivery_channel(client).fetch_message(msg.last_repeat_message)
                    await old_message.delete()
                    skip_delivery = False
                except:
                    pass

        sent_message = None
        if not skip_delivery:
            sent_message = await msg.delivery_channel(client).send(content)
        if msg.repeat is not None:
            match = re.match(r'(minutes:(\d+)|hours:(\d+)|daily|weekly|monthly)', msg.repeat)
            if match:
                if match.group(2):
                    msg.delivery_time = gigtz.add_minutes(msg.delivery_time, int(match.group(2)), giguser.users[msg.author_id].timezone)
                elif match.group(3):
                    msg.delivery_time = gigtz.add_hours(msg.delivery_time, int(match.group(3)), giguser.users[msg.author_id].timezone)
                elif match.group(1) == 'daily':
                    msg.delivery_time = gigtz.add_day(msg.delivery_time, giguser.users[msg.author_id].timezone)
                elif match.group(1) == 'weekly':
                    msg.delivery_time = gigtz.add_week(msg.delivery_time, giguser.users[msg.author_id].timezone)
                elif match.group(1) == 'monthly':
                    msg.delivery_time = gigtz.add_month(msg.delivery_time, giguser.users[msg.author_id].timezone)
                if sent_message:
                    msg.last_repeat_message = sent_message.id
                msg.update_db()
                loop = asyncio.get_event_loop()
                loop.create_task(schedule_delay_message(msg))
        else:
            delayed_messages.pop(msg.id)
            msg.delete_from_db()

async def list_delay_messages(channel, author_id, next_or_all, tmps_repeats=None):
    count = 0
    total = 0
    templates = False
    proposals = False
    max_count = None
    if next_or_all:
        match = re.match(r'next( +(\d+))?', next_or_all)
        if match:
            if match.group(2):
                max_count = int(match.group(2))
            else:
                max_count = 1
        else:
            max_count = None
    if max_count == 0:
        await channel.send(embed=discord.Embed(description="Value for next must be greater than 0", color=0xff0000))
        return

    if tmps_repeats == 'templates' or tmps_repeats == 'template' or tmps_repeats == 'tmp':
        templates = True
    if tmps_repeats == 'proposals' or tmps_repeats == 'proposal' or tmps_repeats == 'p':
        proposals = True
    if templates or proposals:
        if max_count:
            await channel.send(embed=discord.Embed(description="**next** not valid with Templates and Proposals", color=0xff0000))
            return
    if templates:
        output = "> \n> **=========================**\n>  **Templates**\n> **=========================**\n"
    elif proposals:
        output = "> \n> **=========================**\n>  **Proposals**\n> **=========================**\n"
    elif tmps_repeats == 'repeats' or tmps_repeats == 'repeat':
        output = "> \n> **====================**\n>  **Repeating Messages**\n> **====================**\n"
    else:
        output = "> \n> **====================**\n>  **Scheduled Messages**\n> **====================**\n"

    sorted_messages = {}
    for msg_id in delayed_messages:
        if templates:
            if delayed_messages[msg_id].delivery_time is None:
                sorted_messages[msg_id] = delayed_messages[msg_id]
        elif proposals:
            if delayed_messages[msg_id].delivery_time and delayed_messages[msg_id].delivery_time < 0:
                sorted_messages[msg_id] = delayed_messages[msg_id]
        elif delayed_messages[msg_id].delivery_time and delayed_messages[msg_id].delivery_time >= 0:
            if tmps_repeats == 'repeats' or tmps_repeats == 'repeat':
                if delayed_messages[msg_id].repeat is not None:
                    sorted_messages[msg_id] = delayed_messages[msg_id]
            else:
                sorted_messages[msg_id] = delayed_messages[msg_id]

    if not templates or proposals:
        sorted_messages = {k: v for k, v in sorted(sorted_messages.items(), key=lambda item: item[1].delivery_time)}

    for msg_id in sorted_messages:
        msg = sorted_messages[msg_id]
        if msg.guild_id == channel.guild.id or next_or_all == "all" and author_id == 669370838478225448:
            output += f"> \n> **ID:**  {msg.id}\n"
            output += f"> **Author:**  {msg.author(client).name}\n"
            output += f"> **Channel:**  {msg.delivery_channel(client).name}\n"
            if not templates and not  proposals:
                output += f"> **Repeat:**  {msg.repeat}\n"
                if msg.repeat and msg.last_repeat_message:
                    try:
                        old_message = await msg.delivery_channel(client).fetch_message(msg.last_repeat_message)
                        output += f"> **Last Delivery:**  {old_message.jump_url}\n"
                    except:
                        pass

                if round((msg.delivery_time - time())/60, 1) < 0:
                    output += f"> **Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
                else:
                    output += f"> **Deliver:**  {gigtz.display_localized_time(msg.delivery_time, giguser.users[author_id].timezone, giguser.users[author_id].format_24)}\n"
            output += f"> **Description:**  {msg.description}\n"
            if proposals:
                output += "> **Current Votes:**  3\n"
            count += 1
            total += 1
            if count == 4:
                await channel.send(output)
                output = ""
                count = 0
            if total == max_count:
                break
    if total > 0:
        await channel.send(output + "> \n> **====================**\n")
    else:
        if templates:
            await channel.send(embed=discord.Embed(description="No templates found", color=0x00ff00))
        elif proposals:
            await channel.send(embed=discord.Embed(description="No proposals found", color=0x00ff00))
        else:
            await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_user_timezone(channel, author_id):
    output = f"Your time zone is currently set to:  **{gigtz.timezones[giguser.users[author_id].timezone].name}**\n\nUse `~giggle timezone <timezone>` to set your time zone\n\nTo see a list of available time zones type `~giggle timezones`"
    await channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def set_user_timezone(channel, author, tz):
    for tz_id in gigtz.timezones:
        if gigtz.timezones[tz_id].name == tz:
            mydb = db_connect()

            sql = "UPDATE users SET timezone = %s, name = %s WHERE user = %s"

            mycursor = mydb.cursor()
            mycursor.execute(sql, (tz_id, author.name, author.id))
            mydb.commit()
            mycursor.close()
            mydb.disconnect()

            giguser.users[author.id].timezone = tz_id
            await channel.send(embed=discord.Embed(description=f"Your time zone has been set to {tz}", color=0x00ff00))
            return
    else:
        await channel.send(embed=discord.Embed(description=f"Time zone **{tz}** not found\nTo see a list of available time zones:\n`~giggle timezones`", color=0xff0000))

async def show_delayed_message(channel, author_id, msg_num, raw):
    content = ""
    if msg_num == 'last':
        if author_id in giguser.users:
            msg_num = giguser.users[author_id].last_message_id
            content += f"> **ID:**  {msg_num}\n"
    if msg_num == 'next':
        messages = {}
        for msg_id in delayed_messages:
            if delayed_messages[msg_id].delivery_time is not None and delayed_messages[msg_id].guild_id == channel.guild.id:
                messages[msg_id] = delayed_messages[msg_id]
        if messages:
            msg_num = min(messages.values(), key=lambda x: x.delivery_time).id
            content += f"> **ID:**  {msg_num}\n"

    if msg_num in delayed_messages:
        msg = delayed_messages[msg_num]
        content += f"> **Author:**  {msg.author(client).name}\n"
        content += f"> **Channel:**  {msg.delivery_channel(client).name}\n"
        if msg.delivery_time and msg.delivery_time >= 0:
            content += f"> **Repeat:**  {msg.repeat}\n"
        if msg.repeat and msg.last_repeat_message:
            try:
                old_message = await msg.delivery_channel(client).fetch_message(msg.last_repeat_message)
                content += f"> **Last Delivery:**  {old_message.jump_url}\n"
            except:
                pass

        if channel.guild.id != msg.guild_id:
            content += f"> **Deliver in:**  {msg.guild(client).name}\n"
        if msg.delivery_time and msg.delivery_time >= 0:
            if round((msg.delivery_time - time())/60, 1) < 0:
                content += f"> **Delivery failed:**  {str(round((msg.delivery_time - time())/60, 1) * -1)} minutes ago\n"
            else:
                content += f"> **Deliver:**  {gigtz.display_localized_time(msg.delivery_time, giguser.users[author_id].timezone, giguser.users[author_id].format_24)}\n"
        else:
            if msg.delivery_time:
                content = "> **Proposal**\n" + content
            else:
                content = "> **Template**\n" + content
        content += f"> **Description:**  {msg.description}\n"
        if msg.delivery_time < 0:
            content += f"> **Current Votes:**  3\n"
        if raw:
            await channel.send(content + "```\n" + msg.content + "\n```")
        else:
            await channel.send(content + msg.content)
        message_found = True
    else:
        await channel.send(embed=discord.Embed(description=f"Message {msg_num} not found", color=0xff0000))

async def send_delay_message(params):
    channel = params['channel']
    author = params['author']
    msg_num = params['msg_num']

    if msg_num == 'last':
        message_id = giguser.users[author.id].last_message_id
    else:
        message_id = msg_num

    if message_id in delayed_messages:
        if msg_num == 'last':
            await confirm_request(channel, author, f"Send message {message_id} now?", 15, send_delay_message, {'channel': channel, 'author': author, 'msg_num': message_id}, client)
            return

        msg = delayed_messages[message_id]
        if msg.delivery_time is None:
            await channel.send(embed=discord.Embed(description=f"{message_id} is a template and cannot be sent", color=0xff0000))
            return
        else:
            msg.delivery_time = 0
 
        await schedule_delay_message(msg)

        await channel.send(embed=discord.Embed(description="Message sent", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

async def edit_delay_message(params):
    discord_message = params.pop('discord_message', None)
    message_id = params.pop('message_id', None)
    delay = params.pop('delay', None)
    channel = params.pop('channel', None)
    repeat = params.pop('repeat', None)
    description = params.pop('desc', None)
    content = params.pop('content', None)

    if params:
        await discord_message.channel.send(embed=discord.Embed(description=f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help edit`", color=0xff0000))
        return
    
    # validate repeat string
    if repeat:
        if not re.match('(minutes:\d+|hours:\d+|daily|weekly|monthly)(;skip_if=\d+)?$', repeat):
            await discord_message.channel.send(embed=discord.Embed(description=f"Invalid repeat string `{repeat}`", color=0xff0000))
            return

    need_to_confirm = False
    type = "Message"

    if not delay and not channel and not repeat and not description and not content:
        await discord_message.channel.send(embed=discord.Embed(description="You must modify at least one of scheduled time, channel, repeat, description, or content"))
        return

    if message_id == 'last':
        message_id = giguser.users[discord_message.author.id].last_message_id
        need_to_confirm = True

    if message_id in delayed_messages:

        msg = delayed_messages[message_id]
        if msg.delivery_time == None:
            type = "Template"
            if repeat is not None:
                await discord_message.channel.send(embed=discord.Embed(description="The repeat option may not be used when editing a template", color=0xff0000))
                return

        if delay:
            if msg.delivery_time == None:
                await discord_message.channel.send(embed=discord.Embed(description="Cannot set a delivery time for a template", color=0xff0000))
                return
                
            if re.match(r'-?\d+$', delay):
                if delay == '0':
                    delivery_time = 0
                else:
                    delivery_time = time() + int(delay) * 60
            else:
                try:
                    delivery_time = gigtz.local_time_str_to_utc(delay, giguser.users[discord_message.author.id].timezone)
                except:
                    try:
                        delivery_time = gigtz.local_time_str_to_utc(f"{gigtz.get_current_year(giguser.users[discord_message.author.id].timezone)}-{delay}", giguser.users[discord_message.author.id].timezone)
                    except:
                        await discord_message.channel.send(embed=discord.Embed(description=f"{delay} is not a valid DateTime", color=0xff0000))
                        return

        # Confirm channel exists
        if channel:
            delivery_channel = discord.utils.get(discord_message.guild.channels, name=channel)
            if not delivery_channel:
                delivery_channel = discord.utils.get(discord_message.guild.channels, id=int(channel))
            if not delivery_channel:
                await discord_message.channel.send(embed=discord.Embed(description=f"Cannot find {channel} channel", color=0xff0000))
                return

        if content:
            #Make sure {roles} exist
            try:
                replace_mentions(content, discord_message.guild.id)
            except Exception as e:
                await discord_message.channel.send(embed=discord.Embed(description=f"{str(e)}", color=0xff0000))
                return

        if need_to_confirm:
            await confirm_request(discord_message.channel, discord_message.author, f"Edit message {message_id}?", 10, edit_delay_message,
                    {'discord_message': discord_message, 'message_id': message_id, 'delay': delay, 'channel': channel, 'repeat': repeat, 'desc': description, 'content': content}, client)
            return

        embed = discord.Embed(description=f"{type} edited", color=0x00ff00)
        if channel:
            msg.delivery_channel_id = delivery_channel.id
            embed.add_field(name="Channel", value=f"{delivery_channel.name}", inline=False)
        if repeat:
            if repeat == 'none' or repeat == 'None':
                repeat = None
            msg.repeat = repeat
            embed.add_field(name="Repeat", value=f"{repeat}", inline=False)
        if description:
            msg.description = description
            embed.add_field(name="Description", value=f"{description}", inline=False)
        if content:
            msg.content = content
        if delay:
            loop = asyncio.get_event_loop()
            newMessage = DelayedMessage(msg.id, msg.guild_id, msg.delivery_channel_id, delivery_time, msg.author_id, msg.repeat, msg.last_repeat_message, msg.description, msg.content)
            delayed_messages[msg.id] = newMessage
            if delivery_time == 0:
                embed.add_field(name="Deliver", value="Now", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{gigtz.display_localized_time(newMessage.delivery_time, giguser.users[discord_message.author.id].timezone, giguser.users[discord_message.author.id].format_24)}", inline=False)
            loop.create_task(schedule_delay_message(newMessage))
            newMessage.update_db()
        else:
            msg.update_db()

        await discord_message.channel.send(embed=embed)

    else:
        await discord_message.channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

async def cancel_all_delay_message(params):
    member = params['member']
    channel = params['channel']
    
    message_count = 0
    messages_to_remove = []
    for msg_id in delayed_messages:
        if delayed_messages[msg_id].delivery_time is not None and delayed_messages[msg_id].delivery_time >= 0:
            messages_to_remove.append(delayed_messages[msg_id])
    for msg in messages_to_remove:
        if msg.author_id == member.id:
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
    confirmed = params['confirmed']

    need_to_confirm = False
    
    if msg_num == 'all':
        await confirm_request(channel, author, "Cancel all messages authored by you?", 10, cancel_all_delay_message, {'member': author, 'channel': channel}, client)
        return

    if msg_num == 'last':
        need_to_confirm = True
        msg_num = giguser.users[author.id].last_message_id

    if msg_num in delayed_messages:
        if need_to_confirm:
            await confirm_request(channel, author, f"Cancel message {msg_num}?", 15, cancel_delayed_message, {'channel': channel, 'author': author, 'msg_num': msg_num, 'confirmed': True}, client)
            return

        if delayed_messages[msg_num].delivery_time is None:
            if not confirmed:
                await confirm_request(channel, author, f"Delete template {msg_num}?", 15, cancel_delayed_message, {'channel': channel, 'author': author, 'msg_num': msg_num, 'confirmed': True}, client)
                return
            else:
                await channel.send(embed=discord.Embed(description="Template deleted", color=0x00ff00))
        elif delayed_messages[msg_num].delivery_time < 0:
            if not confirmed:
                await confirm_request(channel, author, f"Delete proposal {msg_num}?", 15, cancel_delayed_message, {'channel': channel, 'author': author, 'msg_num': msg_num, 'confirmed': True}, client)
                return
            else:
                await channel.send(embed=discord.Embed(description="Proposal deleted", color=0x00ff00))
                votes.remove_proposal(msg_num)
        else:
            await channel.send(embed=discord.Embed(description="Message canceled", color=0x00ff00))

        delayed_messages.pop(msg_num).delete_from_db()
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

async def add_vip(msg, vip_id, template_id, grace_period):
    if not client.get_user(int(vip_id)):
        await msg.channel.send(embed=discord.Embed(description=f"Cannot find user {vip_id}", color=0xff0000))
        return
    if template_id not in delayed_messages.keys():
        await msg.channel.send(embed=discord.Embed(description=f"Cannot find template {template_id}", color=0xff0000))
        return
    if delayed_messages[template_id].delivery_time:
        await msg.channel.send(embed=discord.Embed(description=f"{template_id} is not a template", color=0xff0000))
        return
    giguser.save_vip(giguser.Vip(vip_id, msg.guild.id, template_id, grace_period))
    await msg.channel.send(embed=discord.Embed(description="Updated Vip", color=0x00ff00))

async def remove_vip(msg, vip_id):
    if (int(vip_id), msg.guild.id) not in giguser.vips:
        await msg.channel.send(embed=discord.Embed(description=f"{vip_id} not in vips list", color=0xff0000))
    giguser.delete_vip(giguser.vips[int(vip_id), msg.guild.id])
    await msg.channel.send(embed=discord.Embed(description="Removed Vip", color=0x00ff00))

async def list_vips(msg, list_all):
    output = ""
    for vip in giguser.vips:
        if giguser.vips[vip].guild_id == msg.guild.id or list_all and msg.author.id == 669370838478225448:
            output += "**" + client.get_user(giguser.vips[vip].vip_id).name + "**"
            output += " **-** "
            output += "**" + giguser.vips[vip].template_id + "**"
            output += " **-** "
            if giguser.vips[vip].grace_period:
                output += "**" + str(giguser.vips[vip].grace_period) + "**"
            else:
                output += "**None**"
            if list_all:
                output += " **-** "
                output += "**" + client.get_guild(giguser.vips[vip].guild_id).name + "**"
            output += "\n"
    if output:
        output = "**Vip** - **Template** - **Grace Period**\n===================================\n" + output
    else:
        output = "No VIPs found"
    await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if isinstance(msg.channel, discord.channel.DMChannel):
        user = client.get_user(669370838478225448)
        await user.send(f"{msg.author.mention} said {msg.content}")

    if re.match(r'~(giggle|g |g$)', msg.content):
        if msg.author.id in giguser.user_guilds.keys() and msg.guild.id in giguser.user_guilds[msg.author.id]:
            try:
                if time() - giguser.users[msg.author.id].last_active > 3600 and msg.author.id != 669370838478225448:
                    await client.get_user(669370838478225448).send(f"{msg.author.mention} is interacting with {client.user.name} bot in the {msg.guild.name} server")
                    giguser.users[msg.author.id].set_last_active(time())

                match = re.match(r'~g(iggle)? +(list|ls)( +((all)|(next( +\d+)?)))?( +(templates?|tmp|repeats?|p(roposals?)?))? *$', msg.content)
                if match:
                    await list_delay_messages(msg.channel, msg.author.id, match.group(4), match.group(9))
                    return

                match = re.match(r'~g(iggle)? +show( +(raw))?( +(\S+)|next) *$', msg.content)
                if match:
                    await show_delayed_message(msg.channel, msg.author.id, match.group(5), match.group(3))
                    return

                match = re.match(r'~g(iggle)? +(cancel|delete|remove|clear|rm) +(\S+) *$', msg.content)
                if match:
                    await cancel_delayed_message({'channel': msg.channel, 'author': msg.author, 'msg_num': match.group(3), 'confirmed': False})
                    return

                match = re.match(r'~g(iggle)? +send +(\S+) *$', msg.content)
                if match:
                    await send_delay_message({'channel': msg.channel, 'author': msg.author, 'msg_num': match.group(2)})
                    return

                match = re.match(r'~g(iggle)? +edit +(\S+)( +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|-?\d+))?( +([^\n]+))?(\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    try:
                        await parse_args(edit_delay_message, {'discord_message': msg, 'message_id': match.group(2), 'delay': match.group(4), 'content': match.group(12)}, match.group(10))
                        return
                    except GigParseException:
                        pass

                match = re.match(r'~g(iggle)? +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|-?\d+|template)( +([^\n]+))?(\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    try:
                        await parse_args(process_delay_message, {'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': msg.id, 'author_id': msg.author.id, 'delay': match.group(2), 'content': match.group(10)}, match.group(8))
                        return
                    except GigParseException:
                        pass

                if re.match(r'~g(iggle)? +reload *$', msg.content) and msg.author.id == 669370838478225448:
                    load_from_db(delayed_messages)
                    await list_delay_messages(msg.channel, msg.author.id, "all")
                    return

                match = re.match(r'~g(iggle)? +(time-format|tf)( +(12|24))? *$', msg.content)
                if match:
                    if match.group(4):
                        giguser.users[msg.author.id].set_time_format(match.group(4))
                        await msg.channel.send(embed=discord.Embed(description=f"Your time display format has been set to {match.group(4)}-hour", color=0x00ff00))
                    elif giguser.users[msg.author.id].format_24:
                        await msg.channel.send(embed=discord.Embed(description="Your time display format is 24-hour", color=0x00ff00))
                    else:
                        await msg.channel.send(embed=discord.Embed(description=f"Your time display format is 12-hour", color=0x00ff00))
                    return

                match = re.match(r'~g(iggle)? +(help|\?)( +(\S+))? *$', msg.content)
                if match:
                    await msg.channel.send(help.show_help(match.group(4)))
                    return

                match = re.match(r'~g(iggle)? +p(ropose)?( +([^\n]+))?(\n(.+))?$', msg.content, re.DOTALL)
                if match:
                    try:
                        await parse_args(process_delay_message, {'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': msg.id, 'author_id': msg.author.id, 'delay': 'proposal', 'content': match.group(6)}, match.group(4))
                        return
                    except GigParseException:
                        pass

                match = re.match(r'~g(iggle)? +(timezone|tz)( +(\S+))? *$', msg.content)
                if match:
                    if match[4]:
                        await set_user_timezone(msg.channel, msg.author, match[4])
                    else:
                        await show_user_timezone(msg.channel, msg.author.id)
                    return

                if re.match(r'~g(iggle)? +(timezones|tzs) *$', msg.content):
                    await msg.channel.send(embed=discord.Embed(description=gigtz.display_timezones(client.user.mention), color=0x00ff00))
                    return

                match = re.match(r'~g(iggle)? +vip +list( +(all))? *$', msg.content)
                if match:
                    await list_vips(msg, match.group(3))
                    return

                match = re.match(r'~g(iggle)? +vip +add +(\d+) +(\S+)( +(\d))? *$', msg.content)
                if match:
                    await add_vip(msg, match.group(2), match.group(3), match.group(5))
                    return

                match = re.match(r'~g(iggle)? +vip +remove +(\d+) *$', msg.content)
                if match:
                    await remove_vip(msg, match.group(2))
                    return

                match = re.match(r'^~g(iggle)? +adduser +(\S+)( +(\S+))? *$', msg.content)
                if match and msg.author.id == 669370838478225448:
                    if match.group(3):
                        guild_id = int(match.group(3))
                    else:
                        guild_id = msg.guild.id
                    giguser.save_user(int(match.group(2)), client.get_user(int(match.group(2))).name, int(guild_id), client.get_guild(guild_id).name)
                    await msg.channel.send(f"Permissions granted for {client.get_user(int(match.group(2))).name} in {client.get_guild(guild_id).name}")
                    return

                await msg.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`~giggle help`", color=0xff0000))

            except Exception as e:
                if msg.author.id == 669370838478225448:
                    await msg.channel.send(f"`{format_exc()}`")
                else:
                    await msg.channel.send(embed=discord.Embed(description=f"Whoops!  Something went wrong.  Please contact {client.user.mention} for help", color=0xff0000))
                    await client.get_user(669370838478225448).send(f"{msg.author.mention} hit an unhandled exception in the {msg.guild.name} server\n\n`{format_exc()}`")
        else:
            await msg.channel.send(embed=discord.Embed(description=f"You do not have premission to interact with me on this server\n\nDM {client.user.mention} to request permission\n\nPlease include the server id ({msg.guild.id}) in your message", color=0xff0000))

@client.event
async def on_voice_state_update(member, before, after):
    if not before.channel and after.channel and (member.id, member.guild.id) in giguser.vips:
        # Make sure we're not in the grace period
        grace_period = 7200 # Default is two hours
        if giguser.vips[(member.id, member.guild.id)].grace_period:
            grace_period = giguser.vips[(member.id, member.guild.id)].grace_period * 60 * 60
        if not giguser.vips[(member.id, member.guild.id)].last_sent or time() - giguser.vips[(member.id, member.guild.id)].last_sent > grace_period:
            giguser.vips[(member.id, member.guild.id)].set_last_sent(time())
            await process_delay_message({'guild': member.guild, 'request_message_id': time(), 'delay': '0', 'from_template': giguser.vips[(member.id, member.guild.id)].template_id })

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with thegigler'))

@client.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name == '☑️':
        for msg_id in delayed_messages:
            if payload.message_id == delayed_messages[msg_id].last_repeat_message:
                await process_proposal_reaction(payload, msg_id, True)
                return

    await process_reaction(payload, client)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == '☑️':
        for msg_id in delayed_messages:
            if payload.message_id == delayed_messages[msg_id].last_repeat_message:
                await process_proposal_reaction(payload, msg_id, False)
                return

@client.event
async def on_guild_join(guild):
    user = client.get_user(669370838478225448)
    await user.send(f"{client.user.name} bot joined {guild.name}")

gigtz.load_timezones()
giguser.load_users()
load_from_db(delayed_messages)

client.run(bot_token)
