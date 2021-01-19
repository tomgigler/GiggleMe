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
import gigdb
import giguser
from delayed_message import Message, Template, Proposal
from gigparse import parse_args, GigParseException
import gigvotes

class GigException(Exception):
    pass

client = discord.Client()
delayed_messages = {}
votes = gigvotes.GigVote()

def load_from_db(delayed_messages):

    loop = asyncio.get_event_loop()

    for row in gigdb.get_all("messages"):
        message_id = row[0]
        delivery_time = row[3]

        if delivery_time and delivery_time >= 0:
            delayed_messages[message_id] = Message(message_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
            loop.create_task(schedule_delay_message(delayed_messages[message_id]))

        elif delivery_time and delivery_time < 0:
            delayed_messages[message_id] = Proposal(message_id, row[1], row[2], row[4], row[6], row[7], row[8])
            votes.load_proposal_votes(message_id)
        else:
            delayed_messages[message_id] = Template(message_id, row[1], row[2], row[4], row[7], row[8])

    gigtz.load_timezones()
    giguser.load_users()

def get_channel_by_name_or_id(guild, channel_param):
    channel = discord.utils.get(guild.channels, name=channel_param)
    if not channel:
        try:
            channel = discord.utils.get(guild.channels, id=int(channel_param))
        except:
            pass
    if not channel:
        raise GigException(f"Cannot find {channel_param} channel")
    return channel

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
    duration = params.pop('duration', None)

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help`")

    if not content and not from_template:
        raise GigException(f"Message body required if not creating a message from a template\n\nTo see help type:\n\n`~giggle help`")
    elif content and from_template:
        raise GigException(f"Message body not allowed when creating a message from a template\n\nTo see help type:\n\n`~giggle help`")

    if from_template:
        if from_template not in delayed_messages:
            raise GigException(f"Cannot find template {from_template}")
        if type(delayed_messages[from_template]) is not Template:
            raise GigException(f"{from_template} is not a template")
        content = delayed_messages[from_template].content
        if not channel:
            channel = delayed_messages[from_template].get_delivery_channel(client).name
        if not description:
            description = delayed_messages[from_template].description

    # get channel
    if channel:
        delivery_channel = get_channel_by_name_or_id(guild, channel)
    else:
        delivery_channel = request_channel

    # get propose_in_channel
    if propose_in_channel_name:
        if delay == 'proposal':
            delivery_time = -1
            propose_in_channel = get_channel_by_name_or_id(guild, propose_in_channel_name)
        else:
            raise GigException(f"Parameter **propose_in_channel** may only be used with proposals\n\nTo see help type:\n\n`~giggle help proposal`")
        if repeat is not None:
            raise GigException(f"Parameter **repeat** may not be used with proposals\n\nTo see help type:\n\n`~giggle help proposal`")
        if duration is not None:
            raise GigException(f"Parameter **duration** may not be used with proposals\n\nTo see help type:\n\n`~giggle help proposal`")
    elif delay == 'proposal':
        raise GigException(f"Parameter **propose_in_channel** is required with proposals\n\nTo see help type:\n\n`~giggle help proposal`")

    # validate repeat string
    repeat_output = ""
    if repeat:
        match = re.match('((minutes:(\d+))|(hours:(\d+))|daily|weekly|monthly)(;skip_if=(\d+))?$', repeat)
        if not match:
            raise GigException(f"Invalid repeat string `{repeat}`")
        if not match.group(3) and not match.group(5):
            repeat_output = f" and will repeat {match.group(1)}"
        elif match.group(3):
            repeat_output = f" and will repeat every {match.group(3)} minutes"
        elif match.group(5):
            repeat_output = f" and will repeat every {match.group(5)} hours"

    # get required_approvals
    if required_approvals:
        if delay == 'proposal':
            if not re.match(r'\d+$', required_approvals) or int(required_approvals) == 0:
                raise GigException(f"Invalid value for **required_approvals**.  Must be a positive integer greater than 0\n\n"
                        "To see help type:\n\n`~giggle help proposal`")
        else:
            raise GigException(f"Invalid command.  Parameter **required_approvals** may only be used with proposals"
                    "\n\nTo see help type:\n\n`~giggle help proposal`")
    else:
        required_approvals = '2'

    if delay == 'proposal':
        pass

    elif delay == 'template':
        delivery_time = None
        if repeat is not None:
            raise GigException("The repeat option may not be used when creating a template")

    elif re.match(r'\d+$', delay):
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
                raise GigException(f"{delay} is not a valid DateTime")

    # validate duration
    repeat_until = None
    if duration:
        if not repeat:
            raise GigException("Duration may only be used with repeating messages")
        if not re.match(r'(minutes:\d+|hours:\d+|days:\d+|[Nn]one)$', duration):
            raise GigException("Invalid value for duration")
        if delivery_time == 0:
            repeat_until = add_duration(time(), duration, author_id)
        else:
            repeat_until = add_duration(delivery_time, duration, author_id)

    #Make sure {roles} exist
    replace_mentions(content, guild.id)

    # create new Message
    if delivery_time is not None and delivery_time >= 0:
        newMessage =  Message(None, guild.id, delivery_channel.id, delivery_time, author_id, repeat, None, content, description, repeat_until)
    elif delivery_time and delivery_time < 0:
        newMessage =  Proposal(None, guild.id, delivery_channel.id, author_id, None, content, description)
    else:
        newMessage =  Template(None, guild.id, delivery_channel.id, author_id, content, description)

    delayed_messages[newMessage.id] = newMessage

    if type(newMessage) is Template or type(newMessage) is Proposal:
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
            await request_channel.send(embed=discord.Embed(description=f"Your message will be delivered to the **{delivery_channel.name}** channel now" + repeat_output, color=0x00ff00))
    elif request_channel:
        embed=discord.Embed(description=f"Your message will be delivered to the **{delivery_channel.name}** channel at {gigtz.display_localized_time(newMessage.delivery_time, giguser.users[author_id].timezone, giguser.users[author_id].format_24)}" + repeat_output, color=0x00ff00)
        embed.add_field(name="Message ID", value=f"{newMessage.id}", inline=True)
        await request_channel.send(embed=embed)

    if author_id:
        giguser.users[author_id].set_last_message(newMessage.id)

    await schedule_delay_message(newMessage)

async def propose_message(msg, propose_in_channel, request_channel, required_approvals):
    votes.vote(msg.id, client.user.id, int(required_approvals))
    output = "> **A MESSAGE HAS BEEN PROPOSED**\n"
    output += f"> **Author:** {msg.get_author(client).name}\n"
    output += f"> **Channel:** {msg.get_delivery_channel(client).name}\n"
    output += "> **Current approvals:** 0\n"
    output += f"> **Required approvals:** {votes.get_required_approvals(msg.id, client.user.id)}\n"
    output += msg.content
    proposal_message = await propose_in_channel.send(output)
    await proposal_message.add_reaction('☑️')
    delayed_messages[msg.id].last_repeat_message = proposal_message.id
    delayed_messages[msg.id].update_db()
    embed=discord.Embed(description=f"Your message has been proposed in the **{propose_in_channel}** channel\n\nIt will be delivered to the **{msg.get_delivery_channel(client).name}** channel when it is approved", color=0x00ff00)
    embed.add_field(name="Proposal ID", value=f"{msg.id}", inline=True)
    await request_channel.send(embed=embed)

async def process_proposal_reaction(user_id, guild_id, channel_id, message_id, msg_id, vote=None):
    if user_id == client.user.id:
        return
    msg = delayed_messages[msg_id]
    required_approvals = votes.get_required_approvals(msg_id, client.user.id)
    if vote is not None:
        votes.vote(msg_id, user_id, vote)
    else:
        votes.remove_proposal(msg_id)
        votes.vote(msg_id, client.user.id, int(required_approvals))
    total_approvals = votes.vote_count(msg_id)
    output = f"> **Author:** {msg.get_author(client).name}\n"
    output += f"> **Channel:** {msg.get_delivery_channel(client).name}\n"

    if total_approvals < required_approvals:
        output = "> **A MESSAGE HAS BEEN PROPOSED**\n" + output
        output += f"> **Current approvals:** {total_approvals}\n"
        output += f"> **Required approvals:** {required_approvals}\n"
    else:
        timezone = None
        format_24 = None
        if msg.author_id in giguser.users:
            timezone = giguser.users[msg.author_id].timezone
            format_24 = giguser.users[msg.author_id].format_24
        output = "> **MESSAGE APPROVED AND SENT**\n" + output
        output += f"> **Sent:** {gigtz.display_localized_time(time(), timezone, format_24)}\n"
        output += f"> **Total approvals:** {required_approvals}\n"
        msg.last_repeat_message = None
        msg.delivery_time = 0
        msg.update_db()
        votes.remove_proposal(msg_id)
        await schedule_delay_message(msg)

    output += msg.content
    guild = client.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    await message.edit(content=output)

def replace_mentions(content, guild_id):
        guild = discord.utils.get(client.guilds, id=int(guild_id))

        for mention in re.finditer(r'{([^}]+)}', content):
            if mention.group(1) == 'everyone':
                mention_replace = '@everyone'
            elif mention.group(1) == 'here':
                mention_replace = '@here'
            else:
                # TODO: try searching for user mention.group(1)
                raise GigException(f"Cannot find role {mention.group(1)}")

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

    guild = msg.get_guild(client)

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
            async for old_message in msg.get_delivery_channel(client).history(limit=skip_if):
                if old_message.id == msg.last_repeat_message:
                    skip_delivery = True

            if skip_if != 0 and msg.last_repeat_message == msg.get_delivery_channel(client).last_message_id:
                try:
                    old_message = await msg.get_delivery_channel(client).fetch_message(msg.last_repeat_message)
                    await old_message.delete()
                    skip_delivery = False
                except:
                    pass

        sent_message = None
        if not skip_delivery:
            sent_message = await msg.get_delivery_channel(client).send(content)
        if msg.repeat is not None:
            match = re.match(r'(minutes:(\d+)|hours:(\d+)|daily|weekly|monthly)', msg.repeat)
            if match:
                if match.group(2):
                    msg.delivery_time = gigtz.add_minutes(msg.delivery_time, int(match.group(2)), giguser.users[msg.author_id].timezone)
                elif match.group(3):
                    msg.delivery_time = gigtz.add_hours(msg.delivery_time, int(match.group(3)), giguser.users[msg.author_id].timezone)
                elif match.group(1) == 'daily':
                    msg.delivery_time = gigtz.add_days(msg.delivery_time, 1, giguser.users[msg.author_id].timezone)
                elif match.group(1) == 'weekly':
                    msg.delivery_time = gigtz.add_week(msg.delivery_time, giguser.users[msg.author_id].timezone)
                elif match.group(1) == 'monthly':
                    msg.delivery_time = gigtz.add_month(msg.delivery_time, giguser.users[msg.author_id].timezone)
                if sent_message:
                    msg.last_repeat_message = sent_message.id
                msg.update_db()
                if msg.repeat_until and msg.delivery_time > msg.repeat_until:
                    delayed_messages.pop(msg.id).delete_from_db()
                else:
                    loop = asyncio.get_event_loop()
                    loop.create_task(schedule_delay_message(msg))
        else:
            delayed_messages.pop(msg.id).delete_from_db()

async def list_delay_messages(channel, author_id, next_or_all, message_type=None):
    count = 0
    total = 0
    if message_type == 'templates' or message_type == 'template' or message_type == 'tmp':
        message_type = 'templates'
    elif message_type == 'proposals' or message_type == 'proposal' or message_type == 'p':
        message_type = 'proposals'
    elif message_type == 'repeats' or message_type == 'repeat':
        message_type = 'repeats'

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
        raise GigException("Value for next must be greater than 0")

    if (message_type == 'templates' or message_type == 'proposals') and max_count:
        raise GigException("**next** not valid with Templates and Proposals")
    if message_type is None:
        output = "> **====================**\n>  **Scheduled Messages**\n> **====================**\n"
    else:
        output = f"> **====================**\n>  **{message_type.capitalize()}**\n> **====================**\n"

    sorted_messages = {}
    for msg_id in delayed_messages:
        if message_type == 'templates':
            if type(delayed_messages[msg_id]) is Template:
                sorted_messages[msg_id] = delayed_messages[msg_id]
        elif message_type == 'proposals':
            if type(delayed_messages[msg_id]) is Proposal:
                sorted_messages[msg_id] = delayed_messages[msg_id]
        else:
            if type(delayed_messages[msg_id]) is Message:
                if message_type == 'repeats' or message_type == 'repeat':
                    if delayed_messages[msg_id].repeat is not None:
                        sorted_messages[msg_id] = delayed_messages[msg_id]
                else:
                    sorted_messages[msg_id] = delayed_messages[msg_id]

    if message_type != 'templates' and message_type != 'proposals':
        sorted_messages = {k: v for k, v in sorted(sorted_messages.items(), key=lambda item: item[1].delivery_time)}

    for msg_id in sorted_messages:
        msg = sorted_messages[msg_id]
        if msg.guild_id == channel.guild.id or next_or_all == "all" and author_id == 669370838478225448:
            output += await msg.get_show_output(client, show_id=True, guild_id=channel.guild.id) + "> \n"
            count += 1
            total += 1
            if count == 4:
                await channel.send(output)
                output = ""
                count = 0
            if total == max_count:
                break
    if total > 0:
        await channel.send(output + "> **====================**\n")
    else:
        if message_type is not None:
            await channel.send(embed=discord.Embed(description=f"No {message_type} found", color=0x00ff00))
        else:
            await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def show_user_timezone(channel, author_id):
    output = f"Your time zone is currently set to:  **{gigtz.timezones[giguser.users[author_id].timezone].name}**\n\nUse `~giggle timezone <timezone>` to set your time zone\n\nTo see a list of available time zones type `~giggle timezones`"
    await channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def set_user_timezone(channel, author, tz):
    output, color = giguser.users[author.id].set_timezone(tz)
    await channel.send(embed=discord.Embed(description=output, color=color))

async def show_delayed_message(channel, author_id, msg_num, raw):
    content = ""
    show_id = False
    if msg_num == 'last':
        if author_id in giguser.users:
            msg_num = giguser.users[author_id].last_message_id
            show_id = True
    if msg_num == 'next':
        messages = {}
        for msg_id in delayed_messages:
            if delayed_messages[msg_id].delivery_time is not None and delayed_messages[msg_id].guild_id == channel.guild.id:
                messages[msg_id] = delayed_messages[msg_id]
        if messages:
            msg_num = min(messages.values(), key=lambda x: x.delivery_time).id
            show_id = True

    if msg_num in delayed_messages:
        output = await delayed_messages[msg_num].get_show_output(client, raw=raw, show_id=show_id, guild_id=channel.guild.id, show_content=True)
        await channel.send(output)
    else:
        await channel.send(embed=discord.Embed(description=f"Message {msg_num} not found", color=0xff0000))

async def send_delay_message(channel, author, msg_num):

    if msg_num == 'last':
        message_id = giguser.users[author.id].last_message_id
    else:
        message_id = msg_num

    if message_id in delayed_messages:
        if msg_num == 'last':
            if not await confirm_request(channel, author.id, f"Send message {message_id} now?", 15, client):
                return

        msg = delayed_messages[message_id]
        if type(msg) is Template:
            raise GigException(f"{message_id} is a template and cannot be sent")
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
    duration = params.pop('duration', None)

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help edit`")
    
    # validate repeat string
    if repeat:
        if not re.match('(minutes:\d+|hours:\d+|daily|weekly|monthly|[Nn]one)(;skip_if=\d+)?$', repeat):
            raise GigException(f"Invalid repeat string `{repeat}`")

    need_to_confirm = False
    message_type = "Message"

    if not delay and not channel and not repeat and not description and not content and not duration:
        await discord_message.channel.send(embed=discord.Embed(description="You must modify at least one of scheduled time, channel, repeat, description, content, or duration"))
        return

    if message_id == 'last':
        message_id = giguser.users[discord_message.author.id].last_message_id
        need_to_confirm = True

    if message_id in delayed_messages:

        msg = delayed_messages[message_id]
        if type(msg) is Template:
            if msg.delivery_time == None:
                message_type = "Template"
                if repeat is not None:
                    raise GigException("The repeat option may not be used when editing a template")
                if delay:
                    raise GigException("Cannot set a delivery time for a template")
            else:
                message_type = "Proposal"
                if repeat is not None:
                    raise GigException("The repeat option may not be used when editing a proposal")
                if delay:
                    raise GigException("A delivery time may not be specified when editing a proposal")

        delivery_time = msg.delivery_time
        if delay:
            if re.match(r'\d+$', delay):
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
                        raise GigException(f"{delay} is not a valid DateTime")

        # validate duration
        if duration:
            if not msg.repeat and not repeat or repeat and (repeat == 'None' or repeat == 'none'):
                raise GigException("Duration may only be used with repeating messages")
            if not re.match(r'(minutes:\d+|hours:\d+|days:\d+|[Nn]one)$', duration):
                raise GigException("Invalid value for duration")

        # Confirm channel exists
        if channel:
            delivery_channel = get_channel_by_name_or_id(discord_message.guild, channel)

        if content:
            #Make sure {roles} exist
            replace_mentions(content, discord_message.guild.id)

        if need_to_confirm:
            if not await confirm_request(discord_message.channel, discord_message.author.id, f"Edit message {message_id}?", 10, client):
                return

        embed = discord.Embed(description=f"{type(msg).__name__} edited", color=0x00ff00)
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
        if duration:
            if duration == 'none' or duration == 'None':
                msg.repeat_until = None
            else:
                msg.repeat_until = add_duration(delivery_time, duration, msg.author_id)

        if delay:
            loop = asyncio.get_event_loop()
            newMessage = Message(msg.id, msg.guild_id, msg.delivery_channel_id, delivery_time, msg.author_id, msg.repeat, msg.last_repeat_message, msg.content, msg.description, msg.repeat_until)
            delayed_messages[msg.id] = newMessage
            if delivery_time == 0:
                embed.add_field(name="Deliver", value="Now", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{gigtz.display_localized_time(newMessage.delivery_time, giguser.users[discord_message.author.id].timezone, giguser.users[discord_message.author.id].format_24)}", inline=False)
            loop.create_task(schedule_delay_message(newMessage))
        else:
            msg.update_db()

        if type == "Proposal":
            # We need to update the proposal
            proposal_message = None
            for channel in discord_message.guild.text_channels:
                async for message in channel.history(limit=200):
                    if message.id == msg.last_repeat_message:
                        proposal_message = message
                        break
                if proposal_message:
                    break
            await process_proposal_reaction(None, msg.guild_id, channel.id, proposal_message.id, msg.id)

        await discord_message.channel.send(embed=embed)

    else:
        await discord_message.channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

def add_duration(delivery_time, duration, user_id):
    match = re.match(r'(minutes|hours|days):(\d+)$', duration)
    if match.group(1) == 'minutes':
        return gigtz.add_minutes(delivery_time, int(match.group(2)), giguser.users[user_id].timezone)
    elif match.group(1) == 'hours':
        return gigtz.add_hours(delivery_time, int(match.group(2)), giguser.users[user_id].timezone)
    elif match.group(1) == 'days':
        return gigtz.add_days(delivery_time, int(match.group(2)), giguser.users[user_id].timezone)

async def cancel_all_delay_message(member, channel):
    if not await confirm_request(channel, member.id, "Cancel all messages authored by you?", 10, client):
        return
    message_count = 0
    messages_to_remove = []
    for msg_id in delayed_messages:
        if delayed_messages[msg_id].delivery_time is not None and delayed_messages[msg_id].delivery_time >= 0:
            messages_to_remove.append(delayed_messages[msg_id])
    for msg in messages_to_remove:
        if msg.author_id == member.id:
            delayed_messages.pop(msg.id).delete_from_db()
            message_count += 1
    if message_count > 0:
        await channel.send(embed=discord.Embed(description=f"Canceled {message_count} messages", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

async def cancel_delayed_message(channel, author, msg_num):
    if msg_num == 'all':
        await cancel_all_delay_message(author, channel)
        return

    if msg_num == 'last':
        msg_num = giguser.users[author.id].last_message_id

    if msg_num == 'next':
        messages = {}
        for msg_id in delayed_messages:
            if type(delayed_messages[msg_id]) is Message and delayed_messages[msg_id].guild_id == channel.guild.id:
                messages[msg_id] = delayed_messages[msg_id]
        if messages:
            msg_num = min(messages.values(), key=lambda x: x.delivery_time).id

    if msg_num in delayed_messages:

        if not await confirm_request(channel, author.id, f"Delete {type(delayed_messages[msg_num]).__name__.lower()} {msg_num}", 15, client):
            return

        if type(delayed_messages[msg_num]) is Proposal:
            votes.remove_proposal(msg_num)
        await channel.send(embed=discord.Embed(description=f"{type(delayed_messages[msg_num]).__name__} deleted", color=0x00ff00))
        delayed_messages.pop(msg_num).delete_from_db()
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

async def add_vip(msg, vip_id, template_id, grace_period):
    if not client.get_user(int(vip_id)):
        raise GigException(f"Cannot find user {vip_id}")
    if template_id not in delayed_messages.keys():
        raise GigException(f"Cannot find template {template_id}")
    if type(delayed_messages[template_id]) is not Template:
        raise GigException(f"{template_id} is not a template")
    giguser.save_vip(giguser.Vip(vip_id, msg.guild.id, template_id, grace_period))
    await msg.channel.send(embed=discord.Embed(description="Updated Vip", color=0x00ff00))

async def remove_vip(msg, vip_id):
    if (int(vip_id), msg.guild.id) not in giguser.vips:
        raise GigException(f"{vip_id} not in vips list")
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

async def show_guild_config(msg):
    output = f"**Config Settings**"
    output += "\n**proposal_channel**:  "
    try:
        output += get_channel_by_name_or_id(msg.guild, giguser.guilds[msg.guild.id].proposal_channel_id).name
    except:
        output += str(giguser.guilds[msg.guild.id].proposal_channel_id)
    output += "\n**approval_channel**:  "
    try:
        output += get_channel_by_name_or_id(msg.guild, giguser.guilds[msg.guild.id].approval_channel_id).name
    except:
        output += str(giguser.guilds[msg.guild.id].approval_channel_id)
    output += "\n**delivery_channel**:  "
    try:
        output += get_channel_by_name_or_id(msg.guild, giguser.guilds[msg.guild.id].delivery_channel_id).name
    except:
        output += str(giguser.guilds[msg.guild.id].delivery_channel_id)
    await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def set_guild_config(params):
    msg = params.pop('msg')
    proposal_channel_param = params.pop('proposal_channel', None)
    approval_channel_param = params.pop('approval_channel', None)
    delivery_channel_param = params.pop('delivery_channel', None)

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help`")

    output = ""
    if proposal_channel_param:
        proposal_channel = get_channel_by_name_or_id(msg.guild, proposal_channel_param)
        giguser.guilds[msg.guild.id].set_proposal_channel_id(proposal_channel.id)
        output += f"**proposal_channel** set to **{proposal_channel.name}**\n"
    if approval_channel_param:
        approval_channel = get_channel_by_name_or_id(msg.guild, approval_channel_param)
        giguser.guilds[msg.guild.id].set_approval_channel_id(approval_channel.id)
        output += f"**approval_channel** set to **{approval_channel.name}**\n"
    if delivery_channel_param:
        delivery_channel = get_channel_by_name_or_id(msg.guild, delivery_channel_param)
        giguser.guilds[msg.guild.id].set_delivery_channel_id(delivery_channel.id)
        output += f"**delivery_channel** set to **{delivery_channel.name}**\n"

    await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if isinstance(msg.channel, discord.channel.DMChannel):
        user = client.get_user(669370838478225448)
        await user.send(f"{msg.author.mention} said {msg.content}")
        return

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
                    await cancel_delayed_message(msg.channel, msg.author, match.group(3))
                    return

                match = re.match(r'~g(iggle)? +send +(\S+) *$', msg.content)
                if match:
                    await send_delay_message(msg.channel, msg.author, match.group(2))
                    return

                match = re.match(r'~g(iggle)? +edit +(\S+)( +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|\d+))?( +([^\n]+))?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    try:
                        await parse_args(edit_delay_message, {'discord_message': msg, 'message_id': match.group(2), 'delay': match.group(4), 'content': match.group(12)}, match.group(10))
                        return
                    except GigParseException:
                        pass

                match = re.match(r'~g(iggle)? +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|\d+|template)( +([^\n]+))?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    try:
                        await parse_args(process_delay_message, {'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': msg.id, 'author_id': msg.author.id, 'delay': match.group(2), 'content': match.group(10)}, match.group(8))
                        return
                    except GigParseException:
                        pass

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

                match = re.match(r'~g(iggle)? +set( +([^\n]+))? *$', msg.content)
                if match:
                    if match.group(3):
                        await parse_args(set_guild_config, {'msg': msg}, match.group(3))
                    else:
                        await show_guild_config(msg)
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

            except GigParseException:
                await msg.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`~giggle help`", color=0xff0000))

            except GigException as e:
                await msg.channel.send(embed=discord.Embed(description=str(e), color=0xff0000))

            except Exception as e:
                if msg.author.id == 669370838478225448:
                    await msg.channel.send(f"`{format_exc()}`")
                else:
                    await msg.channel.send(embed=discord.Embed(description=f"Whoops!  Something went wrong.  Please contact {client.user.mention} for help", color=0xff0000))
                    await client.get_user(669370838478225448).send(f"{msg.author.mention} hit an unhandled exception in the {msg.guild.name} server\n\n`{format_exc()}`")
        else:
            await msg.channel.send(embed=discord.Embed(description=f"You do not have premission to interact with me on this server\n\nDM {client.user.mention} to request permission\n\n"
                    "Please include the server id ({msg.guild.id}) in your message", color=0xff0000))

    elif msg.guild.id in giguser.guilds and msg.channel.id == giguser.guilds[msg.guild.id].proposal_channel_id and giguser.guilds[msg.guild.id].delivery_channel_id and giguser.guilds[msg.guild.id].approval_channel_id:
        await process_delay_message({'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': time(), 'author_id': msg.author.id, 'delay': 'proposal',
            'content': msg.content, 'channel': giguser.guilds[msg.guild.id].delivery_channel_id, 'desc': f"Proposal from {msg.author.name}", 'propose_in_channel': giguser.guilds[msg.guild.id].approval_channel_id})

@client.event
async def on_voice_state_update(member, before, after):
    if not before.channel and after.channel and (member.id, member.guild.id) in giguser.vips:
        # Make sure we're not in the grace period
        grace_period = 7200 # Default is two hours
        if giguser.vips[(member.id, member.guild.id)].grace_period is not None:
            grace_period = giguser.vips[(member.id, member.guild.id)].grace_period * 60 * 60
        if not giguser.vips[(member.id, member.guild.id)].last_sent or time() - giguser.vips[(member.id, member.guild.id)].last_sent > grace_period:
            giguser.vips[(member.id, member.guild.id)].set_last_sent(time())
            await process_delay_message({'guild': member.guild, 'request_message_id': time(), 'delay': '0', 'from_template': giguser.vips[(member.id, member.guild.id)].template_id })

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with thegigler'))

@client.event
async def on_raw_reaction_add(payload):
    process_reaction(payload)
    if payload.emoji.name == '☑️':
        for msg_id in delayed_messages:
            if payload.message_id == delayed_messages[msg_id].last_repeat_message:
                await process_proposal_reaction(payload.user_id, payload.guild_id, payload.channel_id, payload.message_id, msg_id, True)
                return


@client.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == '☑️':
        for msg_id in delayed_messages:
            if payload.message_id == delayed_messages[msg_id].last_repeat_message:
                await process_proposal_reaction(payload.user_id, payload.guild_id, payload.channel_id, payload.message_id, msg_id, False)
                return

@client.event
async def on_guild_join(guild):
    user = client.get_user(669370838478225448)
    await user.send(f"{client.user.name} bot joined {guild.name}")

gigtz.load_timezones()
giguser.load_users()
load_from_db(delayed_messages)

client.run(bot_token)
