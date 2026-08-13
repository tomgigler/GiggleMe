#!/usr/bin/env python
import discord
from discord import app_commands
import re
import asyncio
import settings
from datetime import datetime
from time import time
from operator import attrgetter
from traceback import format_exc
from typing import Optional
import help
from confirm import confirm_request, process_reaction
import gigtz
import gigdb
import giguser
import gigguild
import gigchannel
from delayed_message import Message, Template, Proposal, AutoReply
from gigparse import parse_args, GigParseException
from gigvotes import votes

class GigException(Exception):
    pass

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
slash_commands_synced = False

giggle_group = app_commands.Group(
    name="giggle",
    description="GiggleMe commands"
)


async def prepare_slash_interaction(interaction):
    guild = interaction.guild
    member = interaction.user

    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "This GiggleMe command must be used in a server.",
            ephemeral=True
        )
        return False

    if member.id not in giguser.user_guilds.keys() or guild.id not in giguser.user_guilds[member.id]:
        if member.guild_permissions.administrator:
            giguser.save_user(member.id, member.name, guild.id, guild.name)

    if member.id not in giguser.user_guilds.keys() or guild.id not in giguser.user_guilds[member.id]:
        await interaction.response.send_message(
            "You are not registered to use GiggleMe in this server.",
            ephemeral=True
        )
        return False

    if time() - giguser.users[member.id].last_active > 3600 and member.id != settings.bot_owner_id:
        owner = client.get_user(settings.bot_owner_id)
        if owner:
            await owner.send(
                f"{member.mention} is interacting with {client.user.mention} in the {guild.name} server"
            )
        giguser.users[member.id].set_last_active(time())

    return True


def timezone_slash_help_embed():
    embed = discord.Embed(
        title="/giggle timezone",
        description="View or change your GiggleMe time zone.",
        color=0x00ff00
    )
    embed.add_field(
        name="View your time zone",
        value="Use `/giggle timezone` without selecting a time zone.",
        inline=False
    )
    embed.add_field(
        name="Change your time zone",
        value="Use `/giggle timezone` and select the `timezone` option.",
        inline=False
    )
    return embed


def time_format_slash_help_embed():
    embed = discord.Embed(
        title="/giggle time-format",
        description="View or change your GiggleMe time display format.",
        color=0x00ff00
    )
    embed.add_field(
        name="View your time format",
        value="Use `/giggle time-format` without selecting a format.",
        inline=False
    )
    embed.add_field(
        name="Change your time format",
        value="Use `/giggle time-format` and select either `12` or `24`.",
        inline=False
    )
    return embed


def list_slash_help_embed():
    embed = discord.Embed(
        title="/giggle list",
        description="List scheduled messages and other stored GiggleMe items.",
        color=0x00ff00
    )
    embed.add_field(
        name="Examples",
        value=(
            "`/giggle list` - list scheduled messages\n"
            "`/giggle list category:Repeating messages` - list repeating messages\n"
            "`/giggle list count:3` - show the next three scheduled messages"
        ),
        inline=False
    )
    embed.add_field(
        name="Options",
        value=(
            "`category` chooses scheduled messages, repeats, templates, proposals, or auto-replies.\n"
            "`count` limits the result to the next N items where supported.\n"
            "`scope:All servers` is available only to the bot owner."
        ),
        inline=False
    )
    return embed


def show_slash_help_embed():
    embed = discord.Embed(
        title="/giggle show",
        description="Show a scheduled message, template, proposal, or other stored item.",
        color=0x00ff00
    )
    embed.add_field(
        name="Message",
        value=(
            "Supply a message ID, or use `last` for your most recently scheduled "
            "message or `next` for the next scheduled message."
        ),
        inline=False
    )
    embed.add_field(
        name="Format",
        value="Choose normal, raw Markdown, or raw+ to include recreation syntax.",
        inline=False
    )
    return embed


def slash_help_embed(command=None):
    if command == "timezone":
        return timezone_slash_help_embed()

    if command == "time-format":
        return time_format_slash_help_embed()

    if command == "list":
        return list_slash_help_embed()

    if command == "show":
        return show_slash_help_embed()

    if command == "test":
        return discord.Embed(
            title="/giggle test",
            description="Verify that GiggleMe slash commands are working.",
            color=0x00ff00
        )

    embed = discord.Embed(
        title="GiggleMe Slash Commands",
        description="Use `/giggle help` with a command option for more information.",
        color=0x00ff00
    )
    embed.add_field(
        name="Available slash commands",
        value=(
            "`/giggle timezone` - view or change your time zone\n"
            "`/giggle time-format` - view or change 12/24-hour display\n"
            "`/giggle list` - list stored messages and related items\n"
            "`/giggle show` - show a stored item\n"
            "`/giggle test` - verify slash-command plumbing"
        ),
        inline=False
    )
    embed.add_field(
        name="Still using legacy commands",
        value=(
            "Commands that have not yet been migrated continue to use the "
            "`~giggle` syntax while the migration is in progress."
        ),
        inline=False
    )
    return embed


MIGRATED_HELP_TOPICS = {
    "timezone": "timezone",
    "timezones": "timezone",
    "tz": "timezone",
    "tzs": "timezone",
    "time-format": "time-format",
    "tf": "time-format",
    "list": "list",
    "ls": "list",
    "show": "show",
    "test": "test",
    "help": None
}


@giggle_group.command(name="test", description="Test GiggleMe slash commands")
async def slash_test(interaction: discord.Interaction):
    await interaction.response.send_message("Good job. You used a slash command.")


@giggle_group.command(name="timezone", description="View or change your GiggleMe time zone")
@app_commands.guild_only()
@app_commands.describe(timezone="Time zone to use; leave blank to show your current setting")
async def slash_timezone(interaction: discord.Interaction, timezone: Optional[str] = None):
    if not await prepare_slash_interaction(interaction):
        return

    user = giguser.users[interaction.user.id]

    if timezone is None:
        if user.timezone:
            output = (
                "Your time zone is currently set to:  "
                f"**{gigtz.timezones[user.timezone].name}**"
            )
        else:
            output = "Your time zone is not currently set"

        await interaction.response.send_message(
            embed=discord.Embed(description=output, color=0x00ff00)
        )
        return

    available_timezones = {
        tz.name for tz in gigtz.timezones.values()
    }

    if timezone not in available_timezones:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    f"Time zone **{timezone}** not found\n"
                    "Use `/giggle timezone` and select one of the available time zones."
                ),
                color=0xff0000
            ),
            ephemeral=True
        )
        return

    output, color = user.set_timezone(timezone)
    await interaction.response.send_message(
        embed=discord.Embed(description=output, color=color)
    )


@slash_timezone.autocomplete("timezone")
async def slash_timezone_autocomplete(interaction: discord.Interaction, current: str):
    current = current.casefold()

    names = sorted(
        tz.name for tz in gigtz.timezones.values()
        if current in tz.name.casefold()
    )

    return [
        app_commands.Choice(name=name, value=name)
        for name in names[:25]
    ]


@giggle_group.command(name="time-format", description="View or change your GiggleMe time display format")
@app_commands.guild_only()
@app_commands.describe(format="Time display format; leave blank to show your current setting")
@app_commands.choices(format=[
    app_commands.Choice(name="12-hour", value="12"),
    app_commands.Choice(name="24-hour", value="24")
])
async def slash_time_format(interaction: discord.Interaction, format: Optional[str] = None):
    if not await prepare_slash_interaction(interaction):
        return

    user = giguser.users[interaction.user.id]

    if format is not None:
        user.set_time_format(format)
        output = f"Your time display format has been set to {format}-hour"
    elif user.format_24:
        output = "Your time display format is 24-hour"
    else:
        output = "Your time display format is 12-hour"

    await interaction.response.send_message(
        embed=discord.Embed(description=output, color=0x00ff00)
    )


@giggle_group.command(name="list", description="List scheduled messages and stored GiggleMe items")
@app_commands.guild_only()
@app_commands.describe(
    category="Type of item to list",
    count="Show only the next N items",
    scope="List this server, or all servers if you are the bot owner"
)
@app_commands.choices(
    category=[
        app_commands.Choice(name="Scheduled messages", value="scheduled"),
        app_commands.Choice(name="Repeating messages", value="repeats"),
        app_commands.Choice(name="Templates", value="templates"),
        app_commands.Choice(name="Proposals", value="proposals"),
        app_commands.Choice(name="Auto-replies", value="auto-replies")
    ],
    scope=[
        app_commands.Choice(name="This server", value="server"),
        app_commands.Choice(name="All servers", value="all")
    ]
)
async def slash_list(
    interaction: discord.Interaction,
    category: Optional[str] = None,
    count: Optional[int] = None,
    scope: Optional[str] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    if count is not None and count <= 0:
        await interaction.response.send_message(
            "Count must be greater than 0.",
            ephemeral=True
        )
        return

    message_type = None if category in (None, "scheduled") else category

    if count is not None and message_type in ("templates", "proposals"):
        await interaction.response.send_message(
            "Count is not available when listing templates or proposals.",
            ephemeral=True
        )
        return

    if scope == "all" and interaction.user.id != settings.bot_owner_id:
        await interaction.response.send_message(
            "Only the bot owner can list items from all servers.",
            ephemeral=True
        )
        return

    if scope == "all" and count is not None:
        await interaction.response.send_message(
            "Count cannot be combined with the All servers scope.",
            ephemeral=True
        )
        return

    next_or_all = None
    if scope == "all":
        next_or_all = "all"
    elif count is not None:
        next_or_all = f"next {count}"

    await interaction.response.defer()

    try:
        await list_delay_messages(
            interaction.channel,
            interaction.user.id,
            next_or_all,
            message_type
        )
    finally:
        await interaction.delete_original_response()


@giggle_group.command(name="show", description="Show a stored GiggleMe message or template")
@app_commands.guild_only()
@app_commands.describe(
    message="Message ID, last, or next",
    format="How to display the message"
)
@app_commands.choices(format=[
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="Raw Markdown", value="raw"),
    app_commands.Choice(name="Raw + recreation syntax", value="raw+")
])
async def slash_show(
    interaction: discord.Interaction,
    message: str,
    format: Optional[str] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    raw = None if format in (None, "normal") else format

    await interaction.response.defer()

    try:
        await show_delayed_message(
            interaction.channel,
            interaction.user.id,
            message,
            raw
        )
    finally:
        await interaction.delete_original_response()


@giggle_group.command(name="help", description="Show help for GiggleMe slash commands")
@app_commands.describe(command="Slash command to show help for")
@app_commands.choices(command=[
    app_commands.Choice(name="Timezone", value="timezone"),
    app_commands.Choice(name="Time format", value="time-format"),
    app_commands.Choice(name="List", value="list"),
    app_commands.Choice(name="Show", value="show"),
    app_commands.Choice(name="Test", value="test")
])
async def slash_help(interaction: discord.Interaction, command: Optional[str] = None):
    await interaction.response.send_message(embed=slash_help_embed(command))


tree.add_command(giggle_group)

delayed_messages = {}

async def poll_message_table():
    while(True):
        await asyncio.sleep(5)
        try:
            msg_id, action = gigdb.pop_request_queue()
            if action == 'delete':
                msg = delayed_messages.pop(msg_id, None)
                if msg:
                    msg.delete_from_db()
            elif action == 'create':
                row = gigdb.get_message(msg_id)
                delivery_time = row[3]

                if delivery_time is not None and delivery_time >= 0:
                    delayed_messages[msg_id] = Message(id=msg_id, guild_id=row[1], delivery_channel_id=row[2],
                            delivery_time=row[3], author_id=row[4], repeat=row[5], last_repeat_message=row[6],
                            content=row[7], description=row[8], repeat_until=row[9], special_handling=row[10],
                            update_db=False)
                    giguser.users[delayed_messages[msg_id].author_id].set_last_message(msg_id)
                    asyncio.get_event_loop().create_task(schedule_delay_message(delayed_messages[msg_id]))

                elif delivery_time and delivery_time == -1:
                    votes.load_proposal_votes(msg_id)
                    delayed_messages[msg_id] = Proposal(id=msg_id, guild_id=row[1], delivery_channel_id=row[2],
                            author_id=row[4], approval_message_id=row[6], content=row[7], description=row[8],
                            required_approvals=votes.get_required_approvals(msg_id), update_db=False)
                elif delivery_time and delivery_time == -2:
                    delayed_messages[msg_id] = AutoReply(id=msg_id, guild_id=row[1], delivery_channel_id=row[2], author_id=row[4], trigger=row[5],
                            content=row[7], description=row[8], special_handling=row[10], update_db=False)
                else:
                    delayed_messages[msg_id] = Template(id=msg_id, guild_id=row[1], delivery_channel_id=row[2],
                            author_id=row[4], content=row[7], description=row[8], update_db=False)

            elif action == 'edit':
                row = gigdb.get_message(msg_id)
                delivery_time = row[3]

                delayed_messages[msg_id].guild_id = row[1]
                delayed_messages[msg_id].delivery_channel_id = row[2]
                delayed_messages[msg_id].author_id = row[4]
                delayed_messages[msg_id].content = row[7]
                delayed_messages[msg_id].description = row[8]
                delayed_messages[msg_id].special_handling = row[10]

                if delivery_time and delivery_time >= 0:
                    if row[3] != delayed_messages[msg_id].delivery_time:
                        delayed_messages[msg_id] = Message(id=msg_id, guild_id=row[1], delivery_channel_id=row[2],
                                delivery_time=row[3], author_id=row[4], repeat=row[5], last_repeat_message=row[6],
                                content=row[7], description=row[8], repeat_until=row[9], special_handling=row[10],
                                update_db=False)
                        asyncio.get_event_loop().create_task(schedule_delay_message(delayed_messages[msg_id]))
                    else:
                        delayed_messages[msg_id].repeat = row[5]
                        delayed_messages[msg_id].repeat_until = row[9]
        except Exception as e:
            await client.get_user(settings.bot_owner_id).send(f"Unhandled exception when polling message queue\n> "
                    "**msg_id: {msg_id}**\n> **action: {action}**\n\n`{format_exc()}`")

async def get_message_by_id(guild_id, channel_id, message_id):
    guild = client.get_guild(guild_id)
    message = None
    if channel_id is not None:
        channel = guild.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
    else:
        for channel in guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
            except:
                continue
            break
    if not message:
        raise GigException(f"Message " + message_id + " not found")
    return message

def load_from_db(delayed_messages):

    loop = asyncio.get_event_loop()

    for row in gigdb.get_all("messages"):
        message_id = row[0]
        delivery_time = row[3]

        if delivery_time is not None and delivery_time >= 0:
            delayed_messages[message_id] = Message(id=message_id, guild_id=row[1], delivery_channel_id=row[2],
                    delivery_time=row[3], author_id=row[4], repeat=row[5], last_repeat_message=row[6], content=row[7],
                    description=row[8], repeat_until=row[9], special_handling=row[10], update_db=False)
            loop.create_task(schedule_delay_message(delayed_messages[message_id]))

        elif delivery_time and delivery_time == -1:
            votes.load_proposal_votes(message_id)
            delayed_messages[message_id] = Proposal(id=message_id, guild_id=row[1], delivery_channel_id=row[2],
                    author_id=row[4], approval_message_id=row[6], content=row[7], description=row[8],
                    required_approvals=votes.get_required_approvals(message_id), update_db=False)
        elif delivery_time and delivery_time == -2:
            delayed_messages[message_id] = AutoReply(id=message_id, guild_id=row[1], delivery_channel_id=row[2], author_id=row[4], trigger=row[5],
                    content=row[7], description=row[8], special_handling=row[10], update_db=False)
        else:
            delayed_messages[message_id] = Template(id=message_id, guild_id=row[1], delivery_channel_id=row[2],
                    author_id=row[4], content=row[7], description=row[8], update_db=False)

    gigtz.load_timezones()
    giguser.load_users()

def count_guild_messages(guild_id):
    return sum(map(lambda i: i.guild_id == guild_id, delayed_messages.values()))

def get_channel_by_name_or_id(guild, channel_param):
    channel = discord.utils.get(guild.channels, name=channel_param)
    if not channel:
        try:
            channel = discord.utils.get(guild.channels, id=int(re.search(r'(\d+)', channel_param).group(1)))
        except:
            pass
    if not channel:
        try:
            if int(channel_param) in gigchannel.channels:
                return gigchannel.channels[int(channel_param)]
        except:
            for ch in gigchannel.channels.values():
                if ch.name == channel_param:
                    return ch
        raise GigException(f"Cannot find {channel_param} channel")

    #check channel permissions
    if not channel.permissions_for(channel.guild.get_member(client.user.id)).send_messages:
        raise GigException(f"**{client.user.mention}** does not have permission to send messages in {channel.mention}")

    #make sure channel is in gigchannel.channels
    if not channel.id in gigchannel.channels:
        gigchannel.channels[channel.id] = gigchannel.Channel(channel.id, channel.guild.id, channel.name)

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
    pin_message = params.pop('pin', None)
    set_topic = params.pop('set-topic', None)
    set_channel_name = params.pop('set-channel-name', None)
    publish = params.pop('publish', None)
    special_handling = None

    if count_guild_messages(guild.id) >= 10 and not gigguild.guilds[guild.id].plan_level:
        raise GigException(f"You currently have a total of {count_guild_messages(guild.id)} scehduled messages and templates"
            f"\n\nYou are currently using the free version of {client.user.mention} which limits you to a combined total of 10 scehduled messages and templates"
            f"\n\nPlease DM {client.user.mention} to inquire about upgrade options")

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help`")

    if pin_message and ( set_topic or set_channel_name ) or set_topic and set_channel_name:
        raise GigException(f"Invalid command.  You may only use one of `pin`, `set-topic`, and `set-channel-name`")
    elif publish and ( set_topic or set_channel_name ):
        raise GigException(f"Invalid command.  `publish` may not be used with `set-topic` or `set-channel-name`")

    if content is not None and re.search(r'///', content):
        raise GigException(f"Placeholder `///` found in message body")

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
    if not channel:
        channel = request_channel.name
    delivery_channel = get_channel_by_name_or_id(guild, channel)

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
        required_approvals = '1'

    if delay == 'template' or delay == 'proposal':
        if pin_message is not None:
            raise GigException(f"The **pin** option may not be used when creating a {delay}")
        if set_topic is not None:
            raise GigException(f"The **set-topic** option may not be used when creating a {delay}")
        if set_channel_name is not None:
            raise GigException(f"The **set-channel-name** option may not be used when creating a {delay}")
        if delay == 'template':
            delivery_time = None

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

    if pin_message:
        if re.match(r'(true|yes)', pin_message, re.IGNORECASE):
            special_handling = 8
            if type(delivery_channel).__name__ != 'TextChannel':
                raise GigException("The pin option is only valid for Discord TextChannels")
            if not delivery_channel.permissions_for(delivery_channel.guild.get_member(client.user.id)).manage_messages:
                raise GigException(f"**{client.user.mention}** does not have permission to pin messages in {delivery_channel.mention}")
        elif re.match(r'(false|no)', pin_message, re.IGNORECASE):
            pass
        else:
            raise GigException(f"`{pin_message}` is an invalid value for **pin**")

    if set_topic:
        if re.match(r'(true|yes)', set_topic, re.IGNORECASE):
            special_handling = 16
            if type(delivery_channel).__name__ != 'TextChannel' and type(delivery_channel).__name__ != 'StageChannel':
                raise GigException("The set-topic option is only valid for Discord TextChannels and Discord StageChannels")
            if not delivery_channel.permissions_for(delivery_channel.guild.get_member(client.user.id)).manage_channels:
                raise GigException(f"**{client.user.mention}** does not have permission to set the topic in {delivery_channel.mention}")
        elif re.match(r'(false|no)', set_topic, re.IGNORECASE):
            pass
        else:
            raise GigException(f"`{set_topic}` is an invalid value for **set-topic**")

    if set_channel_name:
        if re.match(r'(true|yes)', set_channel_name, re.IGNORECASE):
            special_handling = 32
            if type(delivery_channel).__module__ != 'discord.channel':
                raise GigException("The set-channel-name option is only valid for Discord Channels")
            if not delivery_channel.permissions_for(delivery_channel.guild.get_member(client.user.id)).manage_channels:
                raise GigException(f"**{client.user.mention}** does not have permission to set the channel name  in {delivery_channel.mention}")
        elif re.match(r'(false|no)', set_channel_name, re.IGNORECASE):
            pass
        else:
            raise GigException(f"`{set_channel_name}` is an invalid value for **set-channel-name**")

    if publish:
        if re.match(r'(true|yes)', publish, re.IGNORECASE):
            if not special_handling:
                special_handling = 64
            else:
                special_handling = special_handling | 64
            if type(delivery_channel).__module__ != 'discord.channel':
                raise GigException("The publish option is only valid for Discord Channels")
        elif re.match(r'(false|no)', publish, re.IGNORECASE):
            pass
        else:
            raise GigException(f"`{publish}` is an invalid value for **publish**")

    if special_handling and not special_handling & 16 and not special_handling & 32:
        if type(delivery_channel).__name__ != 'TextChannel' and type(delivery_channel).__module__ != 'gigchannel':
            raise GigException(f"Cannot send messages to {type(delivery_channel).__name__}")

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
        newMessage = Message(id=None, guild_id=guild.id, delivery_channel_id=delivery_channel.id,
                delivery_time=delivery_time, author_id=author_id, repeat=repeat, last_repeat_message=None,
                content=content, description=description, repeat_until=repeat_until, special_handling=special_handling)
    elif delivery_time and delivery_time == -1:
        newMessage = Proposal(id=None, guild_id=guild.id, delivery_channel_id=delivery_channel.id,
                author_id=author_id, approval_message_id=None, content=content, description=description,
                required_approvals=int(required_approvals))
    else:
        newMessage = Template(id=None, guild_id=guild.id, delivery_channel_id=delivery_channel.id,
                author_id=author_id, content=content, description=description)

    delayed_messages[newMessage.id] = newMessage

    if type(newMessage) is Template or type(newMessage) is Proposal:
        if request_channel:
            if delay == 'template':
                embed=discord.Embed(description=f"Your template has been created", color=0x00ff00)
                embed.add_field(name="Template ID", value=f"{newMessage.id}", inline=True)
                await request_channel.send(embed=embed)
            else:
                await propose_message(newMessage, propose_in_channel, request_channel)
        return
    elif delivery_time == 0:
        if request_channel:
            if special_handling and ( special_handling & 16 or special_handling & 32 ):
                await request_channel.send(embed=discord.Embed(description=f"Your change will be made to the {delivery_channel.mention} channel now" + repeat_output, color=0x00ff00))
            else:
                await request_channel.send(embed=discord.Embed(description=f"Your message will be delivered to the {delivery_channel.mention} channel now" + repeat_output, color=0x00ff00))
    elif request_channel:
        if special_handling and ( special_handling & 16 or special_handling & 32 ):
            embed=discord.Embed(description=f"Your change will be made to {delivery_channel.mention} at {gigtz.display_localized_time(newMessage.delivery_time, giguser.users[author_id].timezone, giguser.users[author_id].format_24)}" + repeat_output, color=0x00ff00)
        else:
            embed=discord.Embed(description=f"Your message will be delivered to {delivery_channel.mention} at {gigtz.display_localized_time(newMessage.delivery_time, giguser.users[author_id].timezone, giguser.users[author_id].format_24)}" + repeat_output, color=0x00ff00)
        embed.add_field(name="Message ID", value=f"{newMessage.id}", inline=True)
        await request_channel.send(embed=embed)

    if author_id:
        giguser.users[author_id].set_last_message(newMessage.id)

    await schedule_delay_message(newMessage)

async def propose_message(msg, propose_in_channel, request_channel):
    votes.vote(msg.id, -1, int(msg.required_approvals))
    output = "> **A MESSAGE HAS BEEN PROPOSED**\n"
    output += f"> **Author:** {msg.get_author(client).name}\n"
    output += f"> **Channel:** {msg.get_delivery_channel(client).mention}\n"
    output += "> **Current approvals:** 0\n"
    output += f"> **Required approvals:** {msg.required_approvals}\n"
    output += msg.content
    approval_message = await propose_in_channel.send(output)
    await approval_message.add_reaction('☑️')
    delayed_messages[msg.id].approval_message_id = approval_message.id
    delayed_messages[msg.id].update_db()
    embed=discord.Embed(description=f"Your message has been proposed in {propose_in_channel.mention}\n\nIt will be delivered to {msg.get_delivery_channel(client).mention} when it is approved", color=0x00ff00)
    embed.add_field(name="Proposal ID", value=f"{msg.id}", inline=True)
    await request_channel.send(embed=embed)

async def process_proposal_reaction(user_id, guild_id, channel_id, message_id, msg_id, vote=None, cancel=False):
    if user_id == client.user.id:
        return
    msg = delayed_messages[msg_id]
    if vote is not None:
        votes.vote(msg_id, user_id, vote)
    else:
        votes.remove_proposal(msg_id)
    if not cancel:
        votes.vote(msg_id, -1, msg.required_approvals)
        total_approvals = votes.vote_count(msg_id)
    output = f"> **Author:** {msg.get_author(client).name}\n"
    output += f"> **Channel:** {msg.get_delivery_channel(client).mention}\n"

    if cancel:
        output = "> **THIS PROPOSAL HAS BEEN CANCELED**\n" + output
    elif total_approvals < msg.required_approvals:
        output = "> **A MESSAGE HAS BEEN PROPOSED**\n" + output
        output += f"> **Current approvals:** {total_approvals}\n"
        output += f"> **Required approvals:** {msg.required_approvals}\n"
    else:
        timezone = None
        format_24 = None
        if msg.author_id in giguser.users:
            timezone = giguser.users[msg.author_id].timezone
            format_24 = giguser.users[msg.author_id].format_24
        output = "> **MESSAGE APPROVED AND SENT**\n" + output
        output += f"> **Sent:** {gigtz.display_localized_time(time(), timezone, format_24)}\n"
        output += f"> **Total approvals:** {msg.required_approvals}\n"
        msg.approval_message_id = None
        msg.delivery_time = 0
        msg.update_db()
        votes.remove_proposal(msg_id)
        await schedule_delay_message(msg)

    output += msg.content
    message = await get_message_by_id(guild_id, channel_id, message_id)
    await message.edit(content=output)

def replace_generic_emojis(content, guild_id):
    guild = discord.utils.get(client.guilds, id=int(guild_id))
    if not guild:
        return content
    emoji_names = set()
    for match in re.finditer(r':([^:\n]+):', content):
        emoji_names.add(match.group(1))
    for emoji_name in emoji_names:
        for emoji in guild.emojis:
            if emoji.name == emoji_name:
                content = re.sub(f":{emoji_name}:(?!\d+)", f"<:{emoji_name}:{emoji.id}>", content)
    return content

def replace_mentions(content, guild_id):
        guild = discord.utils.get(client.guilds, id=int(guild_id))

        for match in re.finditer(r'{(([^:}]+)(:([^:}]+))?(:([^}]+))?)}', content):
            mention_replace = ""
            str_to_replace = match.group(1)
            mention = match.group(2)
            modifier = match.group(4)
            roles_to_exclude = match.group(6)
            if mention == 'everyone' or mention == 'here':
                if modifier:
                    raise GigException(f"`{modifier}` not allowed with `{mention}`")
                mention_replace = f"@{mention}"
            elif modifier:
                if modifier != "expand":
                    raise GigException(f"Unrecognized modifier {modifier}")
                role_to_expand = discord.utils.get(guild.roles,name=mention)
                if not role_to_expand:
                    raise GigException(f"Cannot find role {mention}")
                members = set()
                for member in role_to_expand.members:
                    members.add(member)
                if roles_to_exclude:
                    for role in roles_to_exclude.split(","):
                        exclusions = set()
                        role_to_exclude = discord.utils.get(guild.roles,name=role)
                        if not role_to_exclude:
                            role_to_exclude = discord.utils.get(guild.members,name=role)
                            exclusions.add(role_to_exclude)
                            if not role_to_exclude:
                                raise GigException(f"Cannot find role or user {role}")
                        else:
                            for member in role_to_exclude.members:
                                exclusions.add(member)
                        members = members.difference(exclusions)
                mentions = list()
                for member in sorted(members, key=lambda x: x.name.lower()):
                    mentions.append(member.mention)
                mention_replace = ", ".join(mentions)
                if mention_replace == "":
                    raise GigException(f"`{str_to_replace}` results in an empty set")
            else:
                try:
                    mention_replace = discord.utils.get(guild.roles,name=mention).mention
                except:
                    # See if the "role" was a user
                    try:
                        mention_replace = discord.utils.get(guild.members,name=mention).mention
                    except:
                        raise GigException(f"Cannot find role or user {mention}")

            content = re.sub(f"{{{re.escape(str_to_replace)}}}", mention_replace, content)

        return content

async def schedule_delay_message(msg):

    if msg.delivery_time == 0:
        delay = 0
        if type(msg) is Message and msg.repeat:
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
        if type(msg) is Message and msg.repeat is not None and msg.last_repeat_message is not None:
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
            if hasattr(msg, 'special_handling') and msg.special_handling and msg.special_handling & 16:
                if re.match(r'none', content, re.IGNORECASE):
                    await msg.get_delivery_channel(client).edit(topic='')
                else:
                    await msg.get_delivery_channel(client).edit(topic=content)
            elif hasattr(msg, 'special_handling') and msg.special_handling and msg.special_handling & 32:
                await msg.get_delivery_channel(client).edit(name=content)
            else:
                content = replace_generic_emojis(content, msg.guild_id)
                try:
                    while len(content) > 2000:
                        index = content.rfind('\n\n',1500, 2000)
                        if index == -1:
                            index = content.rfind('\n',1500, 2000)
                            if index == -1:
                                index = content.rfind(' ',1500, 2000)
                                if index == -1:
                                    break
                        await msg.get_delivery_channel(client).send(content[:index])
                        content = content[index:]
                    sent_message = await msg.get_delivery_channel(client).send(content)
                except:
                        message_guild = msg.get_guild(client)
                        if message_guild.id in gigguild.guilds:
                            channel = discord.utils.get(message_guild.channels, id=gigguild.guilds[message_guild.id].approval_channel_id)
                            author = msg.get_author(client)
                            if channel:
                                await channel.send(embed=discord.Embed(description=f"{author.mention} message {msg.id} failed to send", color=0xff0000))
                        await client.get_user(settings.bot_owner_id).send(f"{author.mention}'s ({author.id}) message {msg.id} failed to send\n`{format_exc()}`")
                        return

            if hasattr(msg, 'special_handling') and msg.special_handling and msg.special_handling & 8:
                try:
                    await sent_message.pin()
                except discord.HTTPException as e:
                    message_guild = msg.get_guild(client)
                    if message_guild.id in gigguild.guilds:
                        channel = discord.utils.get(message_guild.channels, id=gigguild.guilds[message_guild.id].approval_channel_id)
                        if channel:
                            output = f"{msg.get_author(client).mention} Your message failed to pin\n\n"
                            output += sent_message.jump_url
                            if type(e) is discord.Forbidden:
                                output += f"\n\n{client.user.mention} does not appear to have permission"
                            else:
                                output += "\n\nThis is probably due to the channel having more than 50 pinned messages"
                            await channel.send(embed=discord.Embed(description=output, color=0xff0000))

            if hasattr(msg, 'special_handling') and msg.special_handling and msg.special_handling & 64:
                try:
                    await sent_message.publish()
                except discord.HTTPException as e:
                    message_guild = msg.get_guild(client)
                    if message_guild.id in gigguild.guilds:
                        channel = discord.utils.get(message_guild.channels, id=gigguild.guilds[message_guild.id].approval_channel_id)
                        if channel:
                            output = f"{msg.get_author(client).mention} Your message failed to publish\n\n"
                            output += sent_message.jump_url
                            if type(e) is discord.Forbidden:
                                output += f"\n\n{client.user.mention} does not appear to have permission"
                            await channel.send(embed=discord.Embed(description=output, color=0xff0000))

        if type(msg) is Message and msg.repeat is not None:
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
    elif message_type == 'auto-repl' or message_type == 'auto' or message_type == 'a':
        message_type = 'auto-replies'
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
        elif message_type == 'auto-replies':
            if type(delayed_messages[msg_id]) is AutoReply:
                sorted_messages[msg_id] = delayed_messages[msg_id]
        else:
            if type(delayed_messages[msg_id]) is Message:
                if message_type == 'repeats' or message_type == 'repeat':
                    if delayed_messages[msg_id].repeat is not None:
                        sorted_messages[msg_id] = delayed_messages[msg_id]
                else:
                    sorted_messages[msg_id] = delayed_messages[msg_id]

    if message_type != 'templates' and message_type != 'proposals' and message_type != 'auto-replies':
        sorted_messages = {k: v for k, v in sorted(sorted_messages.items(), key=lambda item: item[1].delivery_time)}

    for msg_id in sorted_messages:
        msg = sorted_messages[msg_id]
        if msg.guild_id == channel.guild.id or next_or_all == "all" and author_id == settings.bot_owner_id:
            output += "> \n" + await msg.get_show_output(client, show_id=True, guild_id=channel.guild.id, timezone=giguser.users[author_id].timezone, format_24=giguser.users[author_id].format_24)
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
    if giguser.users[author_id].timezone:
        output = f"Your time zone is currently set to:  **{gigtz.timezones[giguser.users[author_id].timezone].name}**\n\nUse `~giggle timezone <timezone>` to set your time zone\n\nTo see a list of available time zones type `~giggle timezones`"
    else:
        output = f"Your time zone is not currently set\n\nUse `~giggle timezone <timezone>` to set your time zone\n\nTo see a list of available time zones type `~giggle timezones`"
    await channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def set_user_timezone(channel, author, tz):
    output, color = giguser.users[author.id].set_timezone(tz)
    await channel.send(embed=discord.Embed(description=output, color=color))

async def show_delayed_message(channel, author_id, msg_num, raw):
    show_id = False
    if msg_num == 'last':
        if author_id in giguser.users:
            msg_num = giguser.users[author_id].last_message_id
            show_id = True
    if msg_num == 'next':
        messages = {}
        for msg_id in delayed_messages:
            if hasattr(delayed_messages[msg_id], 'delivery_time') and delayed_messages[msg_id].delivery_time is not None and delayed_messages[msg_id].guild_id == channel.guild.id:
                messages[msg_id] = delayed_messages[msg_id]
        if messages:
            msg_num = min(messages.values(), key=lambda x: x.delivery_time).id
            show_id = True

    if msg_num in delayed_messages:
        output = await delayed_messages[msg_num].get_show_output(client, raw=raw, show_id=show_id, guild_id=channel.guild.id, show_content=True, timezone=giguser.users[author_id].timezone, format_24=giguser.users[author_id].format_24)
        await channel.send(output)
        content = delayed_messages[msg_num].get_show_content(raw, timezone=giguser.users[author_id].timezone)
        if not raw:
            content = replace_generic_emojis(content, delayed_messages[msg_num].guild_id)
        await channel.send(content)
    else:
        await channel.send(embed=discord.Embed(description=f"Message {msg_num} not found", color=0xff0000))

async def send_delay_message(channel, author, msg_num):
    if msg_num == 'last':
        message_id = giguser.users[author.id].last_message_id
    else:
        message_id = msg_num

    if message_id in delayed_messages:
        msg = delayed_messages[message_id]
        if type(msg) is Template or type(msg) is AutoReply:
            raise GigException(f"**{message_id}** is a(n) **{type(msg).__name__}** and cannot be sent")
        prompt = f"Send message {message_id} now?"
        if type(msg) is Proposal:
            prompt = f"Send proposed message {message_id} now?"
        if not await confirm_request(channel, author.id, prompt, 15, client):
            return

        msg.delivery_time = 0

        await schedule_delay_message(msg)

        await channel.send(embed=discord.Embed(description="Message sent", color=0x00ff00))
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

async def modify_message(guild_id, message_id, content):
    message = await get_message_by_id(guild_id, None, message_id)
    if message.author.id is not client.user.id:
        # raise GigException(f"**{message_id}** is not a message sent by (client.user)")
        raise GigException(f"**{message_id}** is not a message sent by {client.user.name}")
    await message.edit(content=content)

async def edit_delay_message(params):
    discord_message = params.pop('discord_message', None)
    message_id = params.pop('message_id', None)
    delay = params.pop('delay', None)
    channel = params.pop('channel', None)
    repeat = params.pop('repeat', None)
    description = params.pop('desc', None)
    content = params.pop('content', None)
    duration = params.pop('duration', None)
    pin_message = params.pop('pin', None)
    publish = params.pop('publish', None)

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help edit`")

    need_to_confirm = False

    if not delay and not channel and not repeat and not description and not content and not duration and not pin_message and not publish:
        await discord_message.channel.send(embed=discord.Embed(description="You must modify at least one of scheduled time, channel, repeat, description, content, duration, pin or publish"))
        return

    if message_id == 'last':
        message_id = giguser.users[discord_message.author.id].last_message_id
        need_to_confirm = True

    if message_id in delayed_messages:

        msg = delayed_messages[message_id]
        if type(msg) is Message:
            delivery_time = msg.delivery_time
            # validate repeat string
            if repeat:
                if not re.match('(minutes:\d+|hours:\d+|daily|weekly|monthly|[Nn]one)(;skip_if=\d+)?$', repeat):
                    raise GigException(f"Invalid repeat string `{repeat}`")

        else:
            if repeat is not None:
                raise GigException(f"The **repeat** option may not be used when editing a(n) {type(msg).__name__.lower()}")
            if delay:
                raise GigException(f"A delivery time may not be specified when editing a(n) {type(msg).__name__.lower()}")
            if pin_message:
                raise GigException(f"The **pin** option may not be used when editing a(n) {type(msg).__name__.lower()}")
            if publish:
                raise GigException(f"The **publish** may not be used when editing a(n) {type(msg).__name__.lower()}")
            if type(msg) == AutoReply:
                if duration:
                    raise GigException(f"The **duration** option may not be used when editing a(n) {type(msg).__name__.lower()}")

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

        if content and type(msg) != AutoReply:
            #Make sure {roles} exist if message is not an AutoReply
            replace_mentions(content, discord_message.guild.id)

        if need_to_confirm:
            if not await confirm_request(discord_message.channel, discord_message.author.id, f"Edit message {message_id}?", 10, client):
                return

        embed = discord.Embed(description=f"{type(msg).__name__} edited", color=0x00ff00)

        if pin_message:
            if msg.special_handling and msg.special_handling & 16:
                raise GigException("pin may not be used with set-topic")
            if msg.special_handling and msg.special_handling & 32:
                raise GigException("pin may not be used with set-channel-name")
            if re.match(r'(true|yes)', pin_message, re.IGNORECASE):
                if msg.special_handling:
                    msg.special_handling = msg.special_handling | 8
                else:
                    msg.special_handling = 8
            elif re.match(r'(false|no)', pin_message, re.IGNORECASE):
                if msg.special_handling:
                    msg.special_handling = msg.special_handling & 247 # all bits but 8
            else:
                raise GigException(f"`{pin_message}` is an invalid value for **pin**")

        if publish:
            if msg.special_handling and msg.special_handling & 16:
                raise GigException("publish may not be used with set-topic")
            if msg.special_handling and msg.special_handling & 32:
                raise GigException("publish may not be used with set-channel-name")
            if re.match(r'(true|yes)', publish, re.IGNORECASE):
                if msg.special_handling:
                    msg.special_handling = msg.special_handling | 64
                else:
                    msg.special_handling = 64
            elif re.match(r'(false|no)', publish, re.IGNORECASE):
                if msg.special_handling:
                    msg.special_handling = msg.special_handling & 191 # all bits but 64
            else:
                raise GigException(f"`{publish}` is an invalid value for **publish**")

        if channel:
            msg.delivery_channel_id = delivery_channel.id
            embed.add_field(name="Channel", value=f"{delivery_channel.mention}", inline=False)
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
            newMessage = Message(id=msg.id, guild_id=msg.guild_id, delivery_channel_id=msg.delivery_channel_id,
                    delivery_time=delivery_time, author_id=msg.author_id, repeat=msg.repeat,
                    last_repeat_message=msg.last_repeat_message, content=msg.content, description=msg.description,
                    repeat_until=msg.repeat_until, special_handling=msg.special_handling)
            delayed_messages[msg.id] = newMessage
            if delivery_time == 0:
                embed.add_field(name="Deliver", value="Now", inline=False)
            else:
                embed.add_field(name="Deliver", value=f"{gigtz.display_localized_time(newMessage.delivery_time, giguser.users[discord_message.author.id].timezone, giguser.users[discord_message.author.id].format_24)}", inline=False)
            loop.create_task(schedule_delay_message(newMessage))
        else:
            msg.update_db()

        if type(msg) == Proposal:
            # We need to update the proposal
            await process_proposal_reaction(None, msg.guild_id, None, msg.approval_message_id, msg.id)

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
        if type(delayed_messages[msg_id]) is Message and delayed_messages[msg_id].author_id == member.id:
            messages_to_remove.append(delayed_messages[msg_id])
    for msg in messages_to_remove:
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
            await process_proposal_reaction(None, channel.guild.id, None, delayed_messages[msg_num].approval_message_id, msg_num, None, True)
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
        if giguser.vips[vip].guild_id == msg.guild.id or list_all and msg.author.id == settings.bot_owner_id:
            if not client.get_user(giguser.vips[vip].vip_id):
                output += f"Cannot find user {vip[0]}\n"
            else:
                output += "**" + client.get_user(giguser.vips[vip].vip_id).name + "**"
                output += " **-** "
                output += "**" + giguser.vips[vip].template_id + "**"
                output += " **-** "
                if giguser.vips[vip].grace_period is not None:
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
        output += get_channel_by_name_or_id(msg.guild, str(gigguild.guilds[msg.guild.id].proposal_channel_id)).mention
    except:
        output += str(gigguild.guilds[msg.guild.id].proposal_channel_id)
    output += "\n**approval_channel**:  "
    try:
        output += get_channel_by_name_or_id(msg.guild, str(gigguild.guilds[msg.guild.id].approval_channel_id)).mention
    except:
        output += str(gigguild.guilds[msg.guild.id].approval_channel_id)
    output += "\n**delivery_channel**:  "
    try:
        output += get_channel_by_name_or_id(msg.guild, str(gigguild.guilds[msg.guild.id].delivery_channel_id)).mention
    except:
        output += str(gigguild.guilds[msg.guild.id].delivery_channel_id)
    output += "\n**Plan Level**:  "
    if not gigguild.guilds[msg.guild.id].plan_level:
        output += "Free"
    elif gigguild.guilds[msg.guild.id].plan_level == 1:
        output += "Basic"
    elif gigguild.guilds[msg.guild.id].plan_level == 2:
        output += "Premium"
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
        gigguild.guilds[msg.guild.id].set_proposal_channel_id(proposal_channel.id)
        output += f"**proposal_channel** set to **{proposal_channel.mention}**\n"
    if approval_channel_param:
        approval_channel = get_channel_by_name_or_id(msg.guild, approval_channel_param)
        gigguild.guilds[msg.guild.id].set_approval_channel_id(approval_channel.id)
        output += f"**approval_channel** set to **{approval_channel.mention}**\n"
    if delivery_channel_param:
        delivery_channel = get_channel_by_name_or_id(msg.guild, delivery_channel_param)
        gigguild.guilds[msg.guild.id].set_delivery_channel_id(delivery_channel.id)
        output += f"**delivery_channel** set to **{delivery_channel.mention}**\n"

    await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

async def create_auto_reply(params):
    guild_id = params.pop('guild_id')
    author_id = params.pop('author_id')
    trigger = params.pop('trigger')
    reply = params.pop('reply')
    message_channel = params.pop('message_channel')
    channel = params.pop('channel', None)
    desc = params.pop('desc', None)
    wildcard = params.pop('wildcard', None)
    delete = params.pop('delete', None)
    report = params.pop('report', None)

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help`")

    channel_id = None
    if channel is not None:
        channel_id = get_channel_by_name_or_id(client.get_guild(guild_id), channel).id

    special_handling = 0

    if wildcard is not None:
        if wildcard.lower() != 'true' and wildcard.lower() != 'false' and wildcard != '0' and wildcard != '1' and wildcard.lower() != 'yes' and wildcard.lower() != 'no':
            raise GigException(f"**{wildcard}** is an invalid value for wildcard\n\nTo see help type:\n\n`~giggle help`")
        if wildcard.lower() == 'true' or wildcard == '1' or wildcard.lower() == 'yes':
            special_handling = special_handling | 1

    if delete is not None:
        if delete.lower() != 'true' and delete.lower() != 'false' and delete != '0' and delete != '1' and delete.lower() != 'yes' and delete.lower() != 'no':
            raise GigException(f"**{delete}** is an invalid value for delete\n\nTo see help type:\n\n`~giggle help`")
        if delete.lower() == 'true' or delete == '1' or delete.lower() == 'yes':
            special_handling = special_handling | 2

    if report is not None:
        if report.lower() != 'true' and report.lower() != 'false' and report != '0' and report != '1' and report.lower() != 'yes' and report.lower() != 'no':
            raise GigException(f"**{report}** is an invalid value for report\n\nTo see help type:\n\n`~giggle help`")
        if report.lower() == 'true' or report == '1' or report.lower() == 'yes':
            special_handling = special_handling | 4

    if special_handling == 0:
        special_handling = None

    for message_id in delayed_messages:
        if type(delayed_messages[message_id]) is AutoReply and delayed_messages[message_id].guild_id == guild_id and delayed_messages[message_id].trigger.lower() == trigger.lower():
            embed=discord.Embed(description=f"**{delayed_messages[message_id].trigger}** is already in use", color=0xff0000)
            embed.add_field(name="ID", value=f"{message_id}", inline=True)
            await message_channel.send(embed=embed)
            return

    newAutoReply = AutoReply(None, guild_id, channel_id, author_id, trigger, reply, desc, special_handling, True)
    delayed_messages[newAutoReply.id] = newAutoReply
    embed=discord.Embed(description=f"Your auto reply has been created", color=0x00ff00)
    embed.add_field(name="ID", value=f"{newAutoReply.id}", inline=True)
    await message_channel.send(embed=embed)

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if isinstance(msg.channel, discord.channel.DMChannel):
        if msg.author.id == settings.bot_owner_id:
            match = re.match(r'(\d{18})\s+(.+)', msg.content)
            if match:
                user = client.get_user(int(match.group(1)))
                await user.send(match.group(2))
        else:
            user = client.get_user(settings.bot_owner_id)
            content = re.sub("\n", "\n> ", msg.content)
            await user.send(f"{msg.author.mention} ({msg.author.id}) said:\n> {content}")
        return

    if re.match(r'~(giggle|g |g$)', msg.content):
        if msg.author.id not in giguser.user_guilds.keys() or msg.guild.id not in giguser.user_guilds[msg.author.id]:
            if msg.author.guild_permissions.administrator:
                giguser.save_user(msg.author.id, msg.author.name, msg.guild.id, client.get_guild(msg.guild.id).name)
        if msg.author.id in giguser.user_guilds.keys() and msg.guild.id in giguser.user_guilds[msg.author.id]:
            try:
                if time() - giguser.users[msg.author.id].last_active > 3600 and msg.author.id != settings.bot_owner_id:
                    await client.get_user(settings.bot_owner_id).send(f"{msg.author.mention} is interacting with {client.user.mention} in the {msg.guild.name} server")
                    giguser.users[msg.author.id].set_last_active(time())

                match = re.match(r'~g(iggle)? +(auto(-reply)?)( +([^\s\n]+))\s*([^\n]*)\n(.+)', msg.content, re.DOTALL)
                if match:
                    await parse_args(create_auto_reply, {'message_channel': msg.channel, 'guild_id': msg.guild.id, 'author_id': msg.author.id, 'trigger': match.group(5), 'reply': match.group(7)}, match.group(6))
                    return

                match = re.match(r'~g(iggle)? +(list|ls)( +((all)|(next( +\d+)?)))?( +(templates?|tmp|repeats?|p(roposals?)|a(uto(-replies)?)?)?)? *$', msg.content)
                if match:
                    await msg.channel.send(embed=list_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +show( +(raw\+?))?( +(\S+)|next) *$', msg.content)
                if match:
                    await msg.channel.send(embed=show_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +(cancel|delete|remove|clear|rm) +(\S+) *$', msg.content)
                if match:
                    await cancel_delayed_message(msg.channel, msg.author, match.group(3))
                    return

                match = re.match(r'~g(iggle)? +send +(\S+) *$', msg.content)
                if match:
                    await send_delay_message(msg.channel, msg.author, match.group(2))
                    return

                match = re.match(r'~g(iggle)? +modify +(\d+) *\n(.*)$', msg.content)
                if match:
                    await modify_message(msg.guild.id, match.group(2), match.group(3))
                    return

                match = re.match(r'~g(iggle)? +edit +(\S+)( +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|\d+))?( +([^\n]+))?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    await parse_args(edit_delay_message, {'discord_message': msg, 'message_id': match.group(2), 'delay': match.group(4), 'content': match.group(12)}, match.group(10))
                    return

                match = re.match(r'~g(iggle)? +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|\d+|template)( +([^\n]+))?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    await parse_args(process_delay_message, {'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': msg.id, 'author_id': msg.author.id, 'delay': match.group(2), 'content': match.group(10)}, match.group(8))
                    return

                match = re.match(r'~g(iggle)? +(time-format|tf)( +(12|24))? *$', msg.content)
                if match:
                    await msg.channel.send(embed=time_format_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +(help|\?)( +(\S+))? *$', msg.content)
                if match:
                    topic = match.group(4)

                    if topic is None:
                        await msg.channel.send(embed=slash_help_embed())
                    elif topic in MIGRATED_HELP_TOPICS:
                        await msg.channel.send(
                            embed=slash_help_embed(MIGRATED_HELP_TOPICS[topic])
                        )
                    else:
                        await msg.channel.send(help.show_help(topic))
                    return

                match = re.match(r'~g(iggle)? +p(ropose)?( +([^\n]+))?(\n(.+))?$', msg.content, re.DOTALL)
                if match:
                    await parse_args(process_delay_message, {'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': msg.id, 'author_id': msg.author.id, 'delay': 'proposal', 'content': match.group(6)}, match.group(4))
                    return

                match = re.match(r'~g(iggle)? +(timezone|tz)( +(\S+))? *$', msg.content)
                if match:
                    await msg.channel.send(embed=timezone_slash_help_embed())
                    return

                if re.match(r'~g(iggle)? +(timezones|tzs) *$', msg.content):
                    await msg.channel.send(embed=timezone_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +vip +list( +(all))? *$', msg.content)
                if match:
                    await list_vips(msg, match.group(3))
                    return

                match = re.match(r'~g(iggle)? +vip +add +(\d+) +(\S+)( +(\d+))? *$', msg.content)
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
                if match and msg.author.id == settings.bot_owner_id:
                    if match.group(3):
                        guild_id = int(match.group(3))
                    else:
                        guild_id = msg.guild.id
                    giguser.save_user(int(match.group(2)), client.get_user(int(match.group(2))).name, int(guild_id), client.get_guild(guild_id).name)
                    await msg.channel.send(f"Permissions granted for {client.get_user(int(match.group(2))).mention} in {client.get_guild(guild_id).name}")
                    return

                await msg.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`~giggle help`", color=0xff0000))

            except GigParseException as e:
                await msg.channel.send(embed=discord.Embed(description=f"{str(e)}\n\nTo see help type:\n\n`~giggle help` ", color=0xff0000))
                return

            except GigException as e:
                await msg.channel.send(embed=discord.Embed(description=str(e), color=0xff0000))

            except Exception as e:
                if msg.author.id == settings.bot_owner_id:
                    await msg.channel.send(f"`{format_exc()}`")
                else:
                    await msg.channel.send(embed=discord.Embed(description=f"Whoops!  Something went wrong.  Please contact {client.user.mention} for help", color=0xff0000))
                    await client.get_user(settings.bot_owner_id).send(f"{msg.author.mention} hit an unhandled exception in the {msg.guild.name} server\n\n`{format_exc()}`")
        else:
            await msg.channel.send(embed=discord.Embed(description=f"You do not have premission to interact with me on this server\n\nDM {client.user.mention} to request permission", color=0xff0000))

    elif msg.guild.id in gigguild.guilds and msg.channel.id == gigguild.guilds[msg.guild.id].proposal_channel_id and gigguild.guilds[msg.guild.id].delivery_channel_id and gigguild.guilds[msg.guild.id].approval_channel_id:
        await process_delay_message({'guild': msg.guild, 'request_channel': msg.channel, 'request_message_id': time(), 'author_id': msg.author.id, 'delay': 'proposal',
            'content': msg.content, 'channel': gigguild.guilds[msg.guild.id].delivery_channel_id, 'desc': f"Proposal from {msg.author.name}", 'propose_in_channel': gigguild.guilds[msg.guild.id].approval_channel_id})

    else:
        for message_id in delayed_messages:
            if type(delayed_messages[message_id]) is AutoReply:
                if msg.guild.id == delayed_messages[message_id].guild_id:
                    if ( delayed_messages[message_id].special_handling and
                        delayed_messages[message_id].special_handling & 1 and
                        re.match(f".*{delayed_messages[message_id].trigger}.*", msg.content, re.IGNORECASE | re.DOTALL) or
                        msg.content.lower() == delayed_messages[message_id].trigger.lower()):
                        content = re.sub(f"{{user}}", msg.author.mention, delayed_messages[message_id].content)
                        content = re.sub(f"{{server}}", msg.guild.name, content)
                        try:
                            content = replace_mentions(content, msg.guild.id)
                        except:
                            pass
                        channel = msg.channel
                        if delayed_messages[message_id].delivery_channel_id is not None:
                            channel = get_channel_by_name_or_id(msg.guild, str(delayed_messages[message_id].delivery_channel_id))
                        if channel.permissions_for(msg.author).send_messages:
                            while len(content) > 2000:
                                index = content.rfind('\n\n',1500, 2000)
                                if index == -1:
                                    index = content.rfind('\n',1500, 2000)
                                    if index == -1:
                                        index = content.rfind(' ',1500, 2000)
                                        if index == -1:
                                            break
                                await channel.send(content[:index])
                                content = content[index:]
                            if not delayed_messages[message_id].special_handling or not delayed_messages[message_id].special_handling & 4:
                                await channel.send(content)
                        if delayed_messages[message_id].special_handling and delayed_messages[message_id].special_handling & 2:
                            await msg.delete()
                        if delayed_messages[message_id].special_handling and delayed_messages[message_id].special_handling & 4:
                            channel = discord.utils.get(msg.guild.channels, id=gigguild.guilds[msg.guild.id].approval_channel_id)
                            if delayed_messages[message_id].special_handling and delayed_messages[message_id].special_handling & 2:
                                await channel.send(f"The following message from {msg.author.mention} has been deleted from {msg.channel.mention}:\n{msg.content}")
                            else:
                                await channel.send(f"The following message from {msg.author.mention} has been posted in {msg.channel.mention}:\n{msg.content}")

@client.event
async def on_voice_state_update(member, before, after):
    if not before.channel and after.channel and (member.id, member.guild.id) in giguser.vips:
        # Make sure we're not in the grace period
        grace_period = 7200 # Default is two hours
        if giguser.vips[(member.id, member.guild.id)].grace_period is not None:
            grace_period = giguser.vips[(member.id, member.guild.id)].grace_period * 60 * 60
        if not giguser.vips[(member.id, member.guild.id)].last_sent or time() - giguser.vips[(member.id, member.guild.id)].last_sent > float(grace_period):
            giguser.vips[(member.id, member.guild.id)].set_last_sent(time())
            await process_delay_message({'guild': member.guild, 'request_message_id': time(), 'delay': '0', 'from_template': giguser.vips[(member.id, member.guild.id)].template_id })

@client.event
async def on_ready():
    global slash_commands_synced

    if not slash_commands_synced:
        for guild in client.guilds:
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
        slash_commands_synced = True

    await client.change_presence(activity=discord.Game('~giggle help'))

@client.event
async def on_raw_reaction_add(payload):
    process_reaction(payload)
    if payload.emoji.name == '☑️':
        for msg_id in delayed_messages:
            if type(delayed_messages[msg_id]) is Proposal and payload.message_id == delayed_messages[msg_id].approval_message_id:
                await process_proposal_reaction(payload.user_id, payload.guild_id, payload.channel_id, payload.message_id, msg_id, True)
                return


@client.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == '☑️':
        for msg_id in delayed_messages:
            if type(delayed_messages[msg_id]) is Proposal and payload.message_id == delayed_messages[msg_id].approval_message_id:
                await process_proposal_reaction(payload.user_id, payload.guild_id, payload.channel_id, payload.message_id, msg_id, False)
                return

@client.event
async def on_guild_join(guild):
    user = client.get_user(settings.bot_owner_id)
    await user.send(f"{client.user.mention} joined {guild.name} {guild.id}")

async def main():
    gigtz.load_timezones()
    giguser.load_users()
    gigguild.load_guilds()
    gigchannel.load_channels()
    load_from_db(delayed_messages)

    asyncio.create_task(poll_message_table())

    async with client:
        await client.start(settings.bot_token)


asyncio.run(main())
