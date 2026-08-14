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
from types import SimpleNamespace
import help
from confirm import confirm_request
import gigtz
import gigdb
import giguser
import gigguild
import gigchannel
from delayed_message import Message, Template, AutoReply
from gigparse import parse_args, GigParseException

class GigException(Exception):
    pass

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
slash_commands_synced = False

giggle_group = app_commands.Group(
    name="giggle",
    description="GiggleMe commands"
)

user_group = app_commands.Group(
    name="user",
    description="Manage GiggleMe user permissions"
)

template_group = app_commands.Group(
    name="template",
    description="Create and manage GiggleMe templates"
)

vip_group = app_commands.Group(
    name="vip",
    description="Manage VIP voice-channel announcements"
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
            "`category` chooses scheduled messages, repeats, templates, or auto-replies.\n"
            "`count` limits the result to the next N items where supported.\n"
            "`scope:All servers` is available only to the bot owner."
        ),
        inline=False
    )
    return embed


def show_slash_help_embed():
    embed = discord.Embed(
        title="/giggle show",
        description="Show a scheduled message, template, auto-reply, or other stored item.",
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
        value="Choose normal, raw Markdown, or Raw+ for text ready to paste into `/giggle legacy`.",
        inline=False
    )
    return embed


def send_slash_help_embed():
    embed = discord.Embed(
        title="/giggle send",
        description="Send a scheduled message immediately.",
        color=0x00ff00
    )
    embed.add_field(
        name="Message",
        value=(
            "Supply a message ID, or use `last` for the most recently scheduled "
            "message associated with your account."
        ),
        inline=False
    )
    embed.add_field(
        name="Confirmation",
        value="GiggleMe will ask for confirmation before sending the message.",
        inline=False
    )
    return embed


def cancel_slash_help_embed():
    embed = discord.Embed(
        title="/giggle cancel",
        description="Cancel a stored GiggleMe message.",
        color=0x00ff00
    )
    embed.add_field(
        name="Message",
        value=(
            "Supply a message ID, or use `last`, `next`, or `all`.\n"
            "`all` cancels all scheduled messages authored by you."
        ),
        inline=False
    )
    embed.add_field(
        name="Confirmation",
        value="GiggleMe will ask for confirmation before deleting anything.",
        inline=False
    )
    return embed


def edit_sent_slash_help_embed():
    embed = discord.Embed(
        title="/giggle edit-sent",
        description="Edit the content of a Discord message previously sent by GiggleMe.",
        color=0x00ff00
    )
    embed.add_field(
        name="Message ID",
        value=(
            "Use the Discord message ID of a message that GiggleMe has already sent. "
            "This is different from a GiggleMe scheduled-message ID."
        ),
        inline=False
    )
    embed.add_field(
        name="Content",
        value="Supply the replacement message content.",
        inline=False
    )
    return embed


def edit_slash_help_embed():
    embed = discord.Embed(
        title="/giggle edit",
        description="Edit a stored GiggleMe message or related item.",
        color=0x00ff00
    )
    embed.add_field(
        name="Message",
        value=(
            "Select a stored GiggleMe message ID, or use `last` for your most "
            "recently scheduled message. These are GiggleMe's 8-character IDs, "
            "not Discord message IDs."
        ),
        inline=False
    )
    embed.add_field(
        name="Editable fields",
        value=(
            "`time` - new delivery time; uses the same formats as `/giggle schedule`\n"
            "`channel` - destination channel name, mention, or ID\n"
            "`repeat_unit` + `repeat_every` - repeat interval; choose minutes, "
            "hours, days, weeks, or months. Choose Remove repeat to stop repeating.\n"
            "`description` - stored description\n"
            "`content` - message content\n"
            "`duration_unit` + `duration_for` - how long to repeat; choose minutes, "
            "hours, days, weeks, or months. Choose No duration limit to clear it.\n"
            "`pin` - enable or disable pinning\n"
            "`publish` - enable or disable publishing"
        ),
        inline=False
    )
    embed.add_field(
        name="Time formats",
        value=(
            "`0` - send now\n"
            "`15` - 15 minutes from now\n"
            "`8-14 9:30 PM` or `8-14 21:30` - current year\n"
            "`2026-8-14 9:30 PM` or `2026-8-14 21:30` - explicit year\n"
            "All times use your configured GiggleMe time zone."
        ),
        inline=False
    )
    return embed


def template_slash_help_embed():
    embed = discord.Embed(
        title="/giggle template create",
        description="Create a reusable GiggleMe message template.",
        color=0x00ff00
    )
    embed.add_field(
        name="Required",
        value="`content` - the message body to store in the template",
        inline=False
    )
    embed.add_field(
        name="Options",
        value=(
            "`channel` - default delivery channel when the template is used; "
            "defaults to the current channel\n"
            "`description` - short description used when listing templates"
        ),
        inline=False
    )
    embed.add_field(
        name="Using templates",
        value=(
            "Use `/giggle schedule` and select the template with `from_template`. "
            "If you do not specify a channel or description when scheduling, "
            "the template's stored values are used."
        ),
        inline=False
    )
    embed.add_field(
        name="Managing templates",
        value=(
            "Templates also work with `/giggle list`, `/giggle show`, "
            "`/giggle edit`, and `/giggle cancel`."
        ),
        inline=False
    )
    return embed


def vip_slash_help_embed():
    embed = discord.Embed(
        title="/giggle vip",
        description=(
            "Manage VIP voice-channel announcements. When a configured VIP "
            "joins voice after the grace period, GiggleMe sends the selected template."
        ),
        color=0x00ff00
    )
    embed.add_field(
        name="List",
        value=(
            "`/giggle vip list` shows VIPs for this server. "
            "The bot owner may choose the all-server scope."
        ),
        inline=False
    )
    embed.add_field(
        name="Add or update",
        value=(
            "`/giggle vip add user:<member> template:<template>` adds or updates a VIP.\n"
            "`grace_hours` is optional; when omitted, the existing two-hour default is used."
        ),
        inline=False
    )
    embed.add_field(
        name="Remove",
        value="`/giggle vip remove user:<vip>` removes the VIP from this server.",
        inline=False
    )
    return embed


def user_permissions_slash_help_embed():
    embed = discord.Embed(
        title="/giggle user",
        description="Manage who may use GiggleMe in a server.",
        color=0x00ff00
    )
    embed.add_field(
        name="Grant",
        value=(
            "`/giggle user grant user:<user>` grants GiggleMe permission "
            "in the current server. The optional `server` field can target "
            "another server GiggleMe belongs to."
        ),
        inline=False
    )
    embed.add_field(
        name="Revoke",
        value=(
            "`/giggle user revoke user:<user>` removes that user's GiggleMe "
            "permission for the selected server. User settings and scheduled "
            "messages are not deleted."
        ),
        inline=False
    )
    embed.add_field(
        name="Who can use these commands",
        value="User permission management is restricted to the configured bot owner.",
        inline=False
    )
    embed.add_field(
        name="Administrators",
        value=(
            "Server administrators are automatically registered when they interact "
            "with GiggleMe, so revoking an administrator is not a permanent block."
        ),
        inline=False
    )
    return embed


def legacy_slash_help_embed():
    embed = discord.Embed(
        title="/giggle legacy",
        description=(
            "Schedule a message using GiggleMe's old text-command syntax. "
            "This is intended to pair with `/giggle show` → **Raw+**."
        ),
        color=0x00ff00
    )
    embed.add_field(
        name="Input",
        value=(
            "Paste the old scheduling text that used to follow `~giggle`. "
            "The full `~giggle` or `~g` prefix is also accepted."
        ),
        inline=False
    )
    embed.add_field(
        name="Examples",
        value=(
            "`5 channel=general repeat=hours:6` followed by a newline and the message body.\n"
            "`~giggle 0 from_template=abc12345` also works with the old prefix intact."
        ),
        inline=False
    )
    embed.add_field(
        name="Raw+ workflow",
        value=(
            "Schedule one message, show it with **Raw+**, edit the copied text, "
            "then paste it into `/giggle legacy` to create a similar message."
        ),
        inline=False
    )
    embed.add_field(
        name="Scope",
        value=(
            "Legacy supports the old **scheduling syntax only**. It does not "
            "restore retired prefix commands such as timezone, VIP, or help."
        ),
        inline=False
    )
    return embed


def schedule_slash_help_embed():
    embed = discord.Embed(
        title="/giggle schedule",
        description="Schedule a message for future delivery.",
        color=0x00ff00
    )
    embed.add_field(
        name="Required",
        value=(
            "`time` - when to deliver; see the Time formats section below\n"
            "`content` - message body, unless `from_template` is used"
        ),
        inline=False
    )
    embed.add_field(
        name="Options",
        value=(
            "`channel` - destination channel; defaults to the current channel\n"
            "`repeat_unit` + `repeat_every` - repeat interval in minutes, hours, "
            "days, weeks, or months\n"
            "`duration_unit` + `duration_for` - how long the repeat remains active\n"
            "`description` - short description used when listing messages\n"
            "`from_template` - create the body from a stored template\n"
            "`pin`, `publish`, `set_topic`, `set_channel_name` - delivery behavior"
        ),
        inline=False
    )
    embed.add_field(
        name="Time formats",
        value=(
            "All times use your configured GiggleMe time zone.\n"
            "`0` - send now\n"
            "`15` - send 15 minutes from now\n"
            "`8-14 9:30 PM` - August 14 at 9:30 PM in the current year\n"
            "`8-14 21:30` - August 14 at 21:30 in the current year\n"
            "`2026-8-14 9:30 PM` - explicit year, 12-hour time\n"
            "`2026-8-14 21:30` - explicit year, 24-hour time\n"
            "Seconds are optional, for example `21:30:15`."
        ),
        inline=False
    )
    embed.add_field(
        name="Templates",
        value=(
            "Create reusable message bodies with `/giggle template create`, "
            "then select them with `from_template`."
        ),
        inline=False
    )
    return embed


def slash_error_text(error, help_topic=None):
    text = str(error)

    # Some classic command engines include their own "~giggle help" footer.
    # Keep the error itself, but never send a slash-command user back to the
    # classic prefix-command interface.
    legacy_help_pattern = (
        r"\n*\s*To see help type:\s*\n*\s*"
        r"`~giggle help(?: [^`]*)?`\s*"
    )

    text, replacements = re.subn(
        legacy_help_pattern,
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.rstrip()

    if replacements:
        if help_topic:
            text += (
                f"\n\nFor help, use `/giggle help` and choose "
                f"**{help_topic}**."
            )
        else:
            text += "\n\nFor help, use `/giggle help`."

    return text


def slash_help_embed(command=None):
    if command == "timezone":
        return timezone_slash_help_embed()

    if command == "time-format":
        return time_format_slash_help_embed()

    if command == "list":
        return list_slash_help_embed()

    if command == "show":
        return show_slash_help_embed()

    if command == "send":
        return send_slash_help_embed()

    if command == "cancel":
        return cancel_slash_help_embed()

    if command == "edit-sent":
        return edit_sent_slash_help_embed()

    if command == "edit":
        return edit_slash_help_embed()

    if command == "schedule":
        return schedule_slash_help_embed()

    if command == "legacy":
        return legacy_slash_help_embed()

    if command == "templates":
        return template_slash_help_embed()

    if command == "vip":
        return vip_slash_help_embed()

    if command == "users":
        return user_permissions_slash_help_embed()

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
            "`/giggle send` - send a scheduled message immediately\n"
            "`/giggle cancel` - cancel a stored message\n"
            "`/giggle edit-sent` - edit a Discord message already sent by GiggleMe\n"
            "`/giggle edit` - edit a stored GiggleMe item\n"
            "`/giggle schedule` - schedule a message for delivery\n"
            "`/giggle legacy` - schedule using old text-command syntax or Raw+ output\n"
            "`/giggle template create` - create a reusable message template\n"
            "`/giggle vip list|add|remove` - manage VIP voice announcements\n"
            "`/giggle user grant` - grant a user permission to use GiggleMe\n"
            "`/giggle user revoke` - revoke a user's GiggleMe permission\n"
            "`/giggle test` - verify slash-command plumbing"
        ),
        inline=False
    )
    embed.add_field(
        name="Temporary classic-prefix features",
        value=(
            "Classic help and Auto Replies remain temporarily because they still "
            "depend on the privileged Message Content path. Normal GiggleMe "
            "scheduling and management use slash commands."
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
    "send": "send",
    "cancel": "cancel",
    "delete": "cancel",
    "remove": "cancel",
    "clear": "cancel",
    "rm": "cancel",
    "modify": "edit-sent",
    "edit-sent": "edit-sent",
    "edit": "edit",
    "schedule": "schedule",
    "template": "templates",
    "templates": "templates",
    "vip": "vip",
    "adduser": "users",
    "users": "users",
    "test": "test",
    "help": None
}


AUTOCOMPLETE_NONE = "__giggle_none__"
AUTOCOMPLETE_NO_MATCH = "__giggle_no_match__"
AUTOCOMPLETE_NO_CHANNELS = "__giggle_no_channels__"
AUTOCOMPLETE_NO_VIPS = "__giggle_no_vips__"


def get_last_stored_message_id(author_id, guild_id, allowed_types=None):
    if author_id not in giguser.users:
        return None

    msg_id = giguser.users[author_id].last_message_id
    if not msg_id or msg_id not in delayed_messages:
        return None

    msg = delayed_messages[msg_id]

    if msg.guild_id != guild_id:
        return None

    if allowed_types is not None and not isinstance(msg, allowed_types):
        return None

    return msg_id


def get_next_scheduled_message_id(guild_id):
    messages = [
        msg for msg in delayed_messages.values()
        if isinstance(msg, Message)
        and msg.guild_id == guild_id
        and msg.delivery_time is not None
        and msg.delivery_time >= 0
    ]

    if not messages:
        return None

    return min(messages, key=lambda msg: msg.delivery_time).id


async def resolve_slash_message_reference(
    interaction,
    value,
    *,
    allowed_types=None,
    allow_last=False,
    allow_next=False
):
    value = value.strip().casefold()

    if value == "last":
        if not allow_last:
            return None

        msg_id = get_last_stored_message_id(
            interaction.user.id,
            interaction.guild.id,
            allowed_types
        )

        if msg_id is None:
            await interaction.response.send_message(
                "Your most recently scheduled message is no longer stored."
            )
            return None

        return msg_id

    if value == "next":
        if not allow_next:
            return None

        msg_id = get_next_scheduled_message_id(interaction.guild.id)

        if msg_id is None:
            await interaction.response.send_message(
                "There is no scheduled message available as `next`."
            )
            return None

        if allowed_types is not None and not isinstance(
            delayed_messages[msg_id],
            allowed_types
        ):
            await interaction.response.send_message(
                "There is no scheduled message available for this command."
            )
            return None

        return msg_id

    return value


def schedule_channel_autocomplete(interaction, current):
    """Return text channels where GiggleMe can deliver a normal message."""
    if interaction.guild is None:
        return []

    bot_member = interaction.guild.me
    if bot_member is None and client.user is not None:
        bot_member = interaction.guild.get_member(client.user.id)

    if bot_member is None:
        return []

    current = current.casefold().strip()
    choices = []

    channels = sorted(
        interaction.guild.text_channels,
        key=lambda ch: (ch.position, ch.name.casefold())
    )

    for channel in channels:
        permissions = channel.permissions_for(bot_member)

        if not permissions.view_channel or not permissions.send_messages:
            continue

        category = channel.category.name if channel.category else None
        label = f"#{channel.name}"
        if category:
            label += f" — {category}"

        searchable = f"{channel.name} {category or ''} {channel.id}".casefold()
        if current and current not in searchable:
            continue

        choices.append(
            app_commands.Choice(
                name=label[:100],
                value=str(channel.id)
            )
        )

        if len(choices) == 25:
            break

    if choices:
        return choices

    if current:
        label = f'No deliverable channels match "{current[:60]}"'
    else:
        label = "No channels available for message delivery"

    return [
        app_commands.Choice(
            name=label[:100],
            value=AUTOCOMPLETE_NO_CHANNELS
        )
    ]


def stored_message_autocomplete(
    interaction,
    current,
    *,
    allowed_types=None,
    special_choices=None
):
    """Build autocomplete choices for GiggleMe stored-message IDs."""
    current = current.casefold().strip()
    special_choices = special_choices or []

    if interaction.guild is None:
        return [
            app_commands.Choice(
                name="No stored messages available",
                value=AUTOCOMPLETE_NONE
            )
        ]

    items = []
    for msg_id, msg in delayed_messages.items():
        if msg.guild_id != interaction.guild.id:
            continue
        if allowed_types is not None and not isinstance(msg, allowed_types):
            continue
        items.append((msg_id, msg))

    if not items:
        return [
            app_commands.Choice(
                name="No stored messages available for this command",
                value=AUTOCOMPLETE_NONE
            )
        ]

    choices = []

    for value, label in special_choices:
        if not current or current in value.casefold() or current in label.casefold():
            choices.append(
                app_commands.Choice(
                    name=label[:100],
                    value=value
                )
            )

    for msg_id, msg in items:
        kind = type(msg).__name__
        detail = getattr(msg, "description", None) or getattr(msg, "content", None) or ""
        detail = re.sub(r"\s+", " ", detail).strip()

        label = f"{msg_id} [{kind}]"
        if detail:
            label += f" - {detail}"

        if current and current not in msg_id.casefold() and current not in label.casefold():
            continue

        choices.append(
            app_commands.Choice(
                name=label[:100],
                value=msg_id
            )
        )

        if len(choices) == 25:
            break

    if choices:
        return choices[:25]

    typed = current[:70] if current else ""
    name = f'No stored messages match "{typed}"' if typed else "No stored messages available"
    return [
        app_commands.Choice(
            name=name[:100],
            value=AUTOCOMPLETE_NO_MATCH
        )
    ]


def vip_autocomplete(interaction, current):
    """Autocomplete VIPs already configured for the current server."""
    if interaction.guild is None:
        return []

    current = current.casefold().strip()
    choices = []

    for vip in giguser.vips.values():
        if vip.guild_id != interaction.guild.id:
            continue

        user = client.get_user(vip.vip_id)
        user_name = user.name if user else f"User {vip.vip_id}"
        grace = vip.grace_period if vip.grace_period is not None else "default"
        label = f"{user_name} - {vip.template_id} - {grace}h"
        searchable = f"{user_name} {vip.vip_id} {vip.template_id}".casefold()

        if current and current not in searchable:
            continue

        choices.append(
            app_commands.Choice(
                name=label[:100],
                value=str(vip.vip_id)
            )
        )

        if len(choices) == 25:
            break

    if choices:
        return choices

    label = (
        f'No VIPs match "{current[:60]}"'
        if current
        else "No VIPs configured for this server"
    )
    return [
        app_commands.Choice(
            name=label[:100],
            value=AUTOCOMPLETE_NO_VIPS
        )
    ]


async def reject_message_autocomplete_sentinel(interaction, value):
    if value not in (AUTOCOMPLETE_NONE, AUTOCOMPLETE_NO_MATCH):
        return False

    if value == AUTOCOMPLETE_NONE:
        message = "There are no stored messages available for this command."
    else:
        message = "No stored messages match that selection."

    await interaction.response.send_message(message)
    return True


def user_permission_server_autocomplete(interaction, current):
    current = current.casefold().strip()
    choices = []

    guilds = sorted(
        client.guilds,
        key=lambda guild: (
            0 if interaction.guild and guild.id == interaction.guild.id else 1,
            guild.name.casefold()
        )
    )

    for guild in guilds:
        searchable = f"{guild.name} {guild.id}".casefold()
        if current and current not in searchable:
            continue

        label = guild.name
        if interaction.guild and guild.id == interaction.guild.id:
            label += " (current server)"

        choices.append(
            app_commands.Choice(
                name=label[:100],
                value=str(guild.id)
            )
        )

        if len(choices) == 25:
            break

    return choices


async def resolve_user_permission_server(interaction, server):
    if not server:
        return interaction.guild

    try:
        guild_id = int(server)
    except (TypeError, ValueError):
        await interaction.response.send_message(
            f"Server `{server}` is not a valid server ID."
        )
        return None

    guild = client.get_guild(guild_id)
    if guild is None:
        await interaction.response.send_message(
            f"GiggleMe is not connected to server `{server}`."
        )
        return None

    return guild


async def prepare_user_permission_command(interaction):
    if not await prepare_slash_interaction(interaction):
        return False

    if interaction.user.id != settings.bot_owner_id:
        await interaction.response.send_message(
            "Only the configured GiggleMe bot owner can manage user permissions.",
            ephemeral=True
        )
        return False

    return True


@user_group.command(name="grant", description="Grant a user permission to use GiggleMe")
@app_commands.guild_only()
@app_commands.describe(
    user="User to authorize",
    server="Server to authorize the user in; defaults to this server"
)
async def slash_user_grant(
    interaction: discord.Interaction,
    user: discord.User,
    server: Optional[str] = None
):
    if not await prepare_user_permission_command(interaction):
        return

    target_guild = await resolve_user_permission_server(interaction, server)
    if target_guild is None:
        return

    existing_guilds = giguser.user_guilds.get(user.id, [])
    if target_guild.id in existing_guilds:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    f"{user.mention} already has permission to use GiggleMe "
                    f"in **{target_guild.name}**."
                ),
                color=0x00ff00
            )
        )
        return

    giguser.save_user(
        user.id,
        user.name,
        target_guild.id,
        target_guild.name
    )

    await interaction.response.send_message(
        embed=discord.Embed(
            description=(
                f"Permissions granted for {user.mention} "
                f"in **{target_guild.name}**."
            ),
            color=0x00ff00
        )
    )


@slash_user_grant.autocomplete("server")
async def slash_user_grant_server_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return user_permission_server_autocomplete(interaction, current)


@user_group.command(name="revoke", description="Revoke a user's permission to use GiggleMe")
@app_commands.guild_only()
@app_commands.describe(
    user="User whose authorization should be removed",
    server="Server to revoke the user from; defaults to this server"
)
async def slash_user_revoke(
    interaction: discord.Interaction,
    user: discord.User,
    server: Optional[str] = None
):
    if not await prepare_user_permission_command(interaction):
        return

    target_guild = await resolve_user_permission_server(interaction, server)
    if target_guild is None:
        return

    if user.id == settings.bot_owner_id:
        await interaction.response.send_message(
            "The configured GiggleMe bot owner's permission cannot be revoked."
        )
        return

    existing_guilds = giguser.user_guilds.get(user.id, [])
    if target_guild.id not in existing_guilds:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    f"{user.mention} does not currently have GiggleMe permission "
                    f"in **{target_guild.name}**."
                ),
                color=0xff0000
            )
        )
        return

    giguser.delete_user_guild(user.id, target_guild.id)

    description = (
        f"Permissions revoked for {user.mention} "
        f"in **{target_guild.name}**."
    )

    member = target_guild.get_member(user.id)
    if member and member.guild_permissions.administrator:
        description += (
            "\n\n**Note:** This user is a server administrator. "
            "Administrators are automatically authorized again when they "
            "interact with GiggleMe."
        )

    await interaction.response.send_message(
        embed=discord.Embed(
            description=description,
            color=0x00ff00
        )
    )


@slash_user_revoke.autocomplete("server")
async def slash_user_revoke_server_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return user_permission_server_autocomplete(interaction, current)


@vip_group.command(name="list", description="List configured VIP voice announcements")
@app_commands.guild_only()
@app_commands.describe(scope="VIPs to list")
@app_commands.choices(scope=[
    app_commands.Choice(name="This server", value="server"),
    app_commands.Choice(name="All servers", value="all")
])
async def slash_vip_list(
    interaction: discord.Interaction,
    scope: str = "server"
):
    if not await prepare_slash_interaction(interaction):
        return

    list_all = scope == "all"
    if list_all and interaction.user.id != settings.bot_owner_id:
        await interaction.response.send_message(
            "Only the configured GiggleMe bot owner can list VIPs from all servers."
        )
        return

    lines = []
    for vip in giguser.vips.values():
        if not list_all and vip.guild_id != interaction.guild.id:
            continue

        user = client.get_user(vip.vip_id)
        user_name = user.name if user else f"User {vip.vip_id}"
        grace = (
            f"{vip.grace_period}h"
            if vip.grace_period is not None
            else "default (2h)"
        )
        line = f"**{user_name}** - `{vip.template_id}` - **{grace}**"

        if list_all:
            guild = client.get_guild(vip.guild_id)
            guild_name = guild.name if guild else str(vip.guild_id)
            line += f" - **{guild_name}**"

        lines.append(line)

    if lines:
        heading = "**VIP - Template - Grace Period**"
        if list_all:
            heading = "**VIP - Template - Grace Period - Server**"
        description = heading + "\n" + "\n".join(lines)
    else:
        description = "No VIPs found."

    await interaction.response.send_message(
        embed=discord.Embed(description=description, color=0x00ff00)
    )


@vip_group.command(name="add", description="Add or update a VIP voice announcement")
@app_commands.guild_only()
@app_commands.describe(
    user="Server member to make a VIP",
    template="Template to send when this VIP joins voice",
    grace_hours="Hours between announcements; blank uses the two-hour default"
)
async def slash_vip_add(
    interaction: discord.Interaction,
    user: discord.Member,
    template: str,
    grace_hours: Optional[int] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    if await reject_message_autocomplete_sentinel(interaction, template):
        return

    if grace_hours is not None and grace_hours < 0:
        await interaction.response.send_message(
            "Grace period must be zero or a positive number of hours."
        )
        return

    if template not in delayed_messages:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Cannot find template `{template}`.",
                color=0xff0000
            )
        )
        return

    if not isinstance(delayed_messages[template], Template):
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"`{template}` is not a template.",
                color=0xff0000
            )
        )
        return

    giguser.save_vip(
        giguser.Vip(
            user.id,
            interaction.guild.id,
            template,
            grace_hours
        )
    )

    grace_text = (
        f"{grace_hours} hour(s)"
        if grace_hours is not None
        else "the default 2 hours"
    )
    await interaction.response.send_message(
        embed=discord.Embed(
            description=(
                f"VIP updated for {user.mention}.\n"
                f"Template: `{template}`\n"
                f"Grace period: **{grace_text}**"
            ),
            color=0x00ff00
        )
    )


@slash_vip_add.autocomplete("template")
async def slash_vip_add_template_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return stored_message_autocomplete(
        interaction,
        current,
        allowed_types=(Template,)
    )


@vip_group.command(name="remove", description="Remove a VIP voice announcement")
@app_commands.guild_only()
@app_commands.describe(user="VIP to remove")
async def slash_vip_remove(
    interaction: discord.Interaction,
    user: str
):
    if not await prepare_slash_interaction(interaction):
        return

    if user == AUTOCOMPLETE_NO_VIPS:
        await interaction.response.send_message(
            "There are no VIPs configured for this server."
        )
        return

    try:
        user_id = int(user)
    except (TypeError, ValueError):
        await interaction.response.send_message(
            f"`{user}` is not a valid VIP user ID."
        )
        return

    key = (user_id, interaction.guild.id)
    if key not in giguser.vips:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"User `{user_id}` is not in this server's VIP list.",
                color=0xff0000
            )
        )
        return

    vip = giguser.vips[key]
    cached_user = client.get_user(user_id)
    user_name = cached_user.name if cached_user else str(user_id)
    giguser.delete_vip(vip)

    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"Removed VIP **{user_name}**.",
            color=0x00ff00
        )
    )


@slash_vip_remove.autocomplete("user")
async def slash_vip_remove_user_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return vip_autocomplete(interaction, current)


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
            )
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
            "Count must be greater than 0."
        )
        return

    message_type = None if category in (None, "scheduled") else category

    if count is not None and message_type == "templates":
        await interaction.response.send_message(
            "Count is not available when listing templates."
        )
        return

    if scope == "all" and interaction.user.id != settings.bot_owner_id:
        await interaction.response.send_message(
            "Only the bot owner can list items from all servers."
        )
        return

    if scope == "all" and count is not None:
        await interaction.response.send_message(
            "Count cannot be combined with the All servers scope."
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
        await interaction.edit_original_response(
            embed=discord.Embed(
                description="List results shown below.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "List"), color=0xff0000)
        )


@giggle_group.command(name="show", description="Show a stored GiggleMe message or template")
@app_commands.guild_only()
@app_commands.describe(
    message="Message ID, last, or next",
    format="How to display the message"
)
@app_commands.choices(format=[
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="Raw Markdown", value="raw"),
    app_commands.Choice(name="Raw+ (legacy recreation)", value="raw+")
])
async def slash_show(
    interaction: discord.Interaction,
    message: str,
    format: Optional[app_commands.Choice[str]] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    message = message.strip().casefold()

    if await reject_message_autocomplete_sentinel(interaction, message):
        return

    resolved_message = await resolve_slash_message_reference(
        interaction,
        message,
        allow_last=True,
        allow_next=True
    )
    if resolved_message is None:
        return
    message = resolved_message

    selected_format = None if format is None else format.value
    raw = None if selected_format in (None, "normal") else selected_format

    await interaction.response.defer()

    try:
        await show_delayed_message(
            interaction.channel,
            interaction.user.id,
            message,
            raw,
            always_show_id=True
        )
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=f"Showing GiggleMe message **{message}**.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "Show"), color=0xff0000)
        )




@slash_show.autocomplete("message")
async def slash_show_message_autocomplete(interaction: discord.Interaction, current: str):
    special_choices = []

    if interaction.guild is not None:
        if get_last_stored_message_id(interaction.user.id, interaction.guild.id):
            special_choices.append(
                ("last", "last - your most recently scheduled message")
            )

        if get_next_scheduled_message_id(interaction.guild.id):
            special_choices.append(
                ("next", "next - the next scheduled message")
            )

    return stored_message_autocomplete(
        interaction,
        current,
        special_choices=special_choices
    )


@giggle_group.command(name="send", description="Send a scheduled message immediately")
@app_commands.guild_only()
@app_commands.describe(message="Message ID, or last")
async def slash_send(interaction: discord.Interaction, message: str):
    if not await prepare_slash_interaction(interaction):
        return

    message = message.strip().casefold()

    if await reject_message_autocomplete_sentinel(interaction, message):
        return

    resolved_message = await resolve_slash_message_reference(
        interaction,
        message,
        allowed_types=(Message,),
        allow_last=True
    )
    if resolved_message is None:
        return
    message = resolved_message

    await interaction.response.defer()

    try:
        await send_delay_message(
            interaction.channel,
            interaction.user,
            message
        )
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=f"Send request completed for message **{message}**.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "Send"), color=0xff0000)
        )




@slash_send.autocomplete("message")
async def slash_send_message_autocomplete(interaction: discord.Interaction, current: str):
    special_choices = []

    if interaction.guild is not None and get_last_stored_message_id(
        interaction.user.id,
        interaction.guild.id,
        (Message,)
    ):
        special_choices.append(
            ("last", "last - your most recently scheduled message")
        )

    return stored_message_autocomplete(
        interaction,
        current,
        allowed_types=(Message,),
        special_choices=special_choices
    )


@giggle_group.command(name="cancel", description="Cancel a stored GiggleMe message")
@app_commands.guild_only()
@app_commands.describe(message="Message ID, last, next, or all")
async def slash_cancel(interaction: discord.Interaction, message: str):
    if not await prepare_slash_interaction(interaction):
        return

    message = message.strip().casefold()

    if await reject_message_autocomplete_sentinel(interaction, message):
        return

    if message != "all":
        resolved_message = await resolve_slash_message_reference(
            interaction,
            message,
            allow_last=True,
            allow_next=True
        )
        if resolved_message is None:
            return
        message = resolved_message

    await interaction.response.defer()

    try:
        await cancel_delayed_message(
            interaction.channel,
            interaction.user,
            message
        )
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=f"Cancel request completed for **{message}**.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "Cancel"), color=0xff0000)
        )




@slash_cancel.autocomplete("message")
async def slash_cancel_message_autocomplete(interaction: discord.Interaction, current: str):
    special_choices = []

    if interaction.guild is not None:
        if get_last_stored_message_id(interaction.user.id, interaction.guild.id):
            special_choices.append(
                ("last", "last - your most recently scheduled message")
            )

        if get_next_scheduled_message_id(interaction.guild.id):
            special_choices.append(
                ("next", "next - the next scheduled message")
            )

        if any(
            isinstance(msg, Message)
            and msg.guild_id == interaction.guild.id
            and msg.author_id == interaction.user.id
            for msg in delayed_messages.values()
        ):
            special_choices.append(
                ("all", "all - all scheduled messages authored by you")
            )

    return stored_message_autocomplete(
        interaction,
        current,
        special_choices=special_choices
    )


@giggle_group.command(
    name="edit-sent",
    description="Edit a Discord message previously sent by GiggleMe"
)
@app_commands.guild_only()
@app_commands.describe(
    message_id="Discord message ID of the GiggleMe message to edit",
    content="Replacement message content"
)
async def slash_edit_sent(
    interaction: discord.Interaction,
    message_id: str,
    content: str
):
    if not await prepare_slash_interaction(interaction):
        return

    await interaction.response.defer()

    try:
        await modify_message(
            interaction.guild.id,
            message_id,
            content
        )
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=f"Discord message **{message_id}** edited.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "Edit sent"), color=0xff0000)
        )


@giggle_group.command(
    name="edit",
    description="Edit a stored GiggleMe message or related item"
)
@app_commands.guild_only()
@app_commands.describe(
    message="GiggleMe message ID, or last",
    time="New time: 0=now, 15=15 min from now, or 8-14 9:30 PM / 2026-8-14 21:30",
    channel="Destination channel; suggestions include channels GiggleMe can send to",
    repeat_unit="Unit between repeated deliveries",
    repeat_every="Number of repeat units between deliveries",
    description="New stored description",
    content="New message content",
    duration_unit="Unit for the repeat duration",
    duration_for="Number of duration units",
    pin="Enable or disable pinning",
    publish="Enable or disable publishing"
)
@app_commands.choices(
    repeat_unit=[
        app_commands.Choice(name="Minutes", value="minutes"),
        app_commands.Choice(name="Hours", value="hours"),
        app_commands.Choice(name="Days", value="days"),
        app_commands.Choice(name="Weeks", value="weeks"),
        app_commands.Choice(name="Months", value="months"),
        app_commands.Choice(name="Remove repeat", value="none")
    ],
    duration_unit=[
        app_commands.Choice(name="Minutes", value="minutes"),
        app_commands.Choice(name="Hours", value="hours"),
        app_commands.Choice(name="Days", value="days"),
        app_commands.Choice(name="Weeks", value="weeks"),
        app_commands.Choice(name="Months", value="months"),
        app_commands.Choice(name="No duration limit", value="none")
    ]
)
async def slash_edit(
    interaction: discord.Interaction,
    message: str,
    time: Optional[str] = None,
    channel: Optional[str] = None,
    repeat_unit: Optional[str] = None,
    repeat_every: Optional[int] = None,
    description: Optional[str] = None,
    content: Optional[str] = None,
    duration_unit: Optional[str] = None,
    duration_for: Optional[int] = None,
    pin: Optional[bool] = None,
    publish: Optional[bool] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    if await reject_message_autocomplete_sentinel(interaction, message):
        return

    if channel == AUTOCOMPLETE_NO_CHANNELS:
        await interaction.response.send_message(
            "GiggleMe does not currently have permission to deliver messages "
            "to any text channel in this server."
        )
        return

    message_id = await resolve_slash_message_reference(
        interaction,
        message,
        allow_last=True
    )
    if message_id is None:
        return

    try:
        repeat = build_slash_interval(
            repeat_unit,
            repeat_every,
            "repeat",
            allow_none=True
        )
        duration = build_slash_interval(
            duration_unit,
            duration_for,
            "duration",
            allow_none=True
        )
    except GigException as e:
        await interaction.response.send_message(
            embed=discord.Embed(description=str(e), color=0xff0000)
        )
        return

    await interaction.response.defer()

    # GiggleMe-generated IDs are lowercase MD5 fragments, but accepting
    # pasted uppercase IDs costs nothing and removes a needless trap.
    message_id = message_id.casefold()

    if not message_id or message_id not in delayed_messages:
        if message.strip().isdigit() and len(message.strip()) >= 17:
            detail = (
                "That looks like a Discord message ID. `/giggle edit` uses the "
                "8-character GiggleMe ID shown by `/giggle list` and `/giggle show`. "
                "Use `/giggle edit-sent` for Discord message IDs."
            )
        else:
            detail = (
                f"GiggleMe message `{message.strip()}` was not found. "
                "Use `/giggle list` to find the stored message ID."
            )

        await interaction.edit_original_response(
            embed=discord.Embed(description=detail, color=0xff0000)
        )
        return

    # edit_delay_message() predates interactions and only relies on these
    # three Message attributes. Keep the existing engine intact while the
    # slash layer supplies its inputs explicitly.
    discord_message = SimpleNamespace(
        channel=interaction.channel,
        author=interaction.user,
        guild=interaction.guild
    )

    params = {
        "discord_message": discord_message,
        "message_id": message_id,
        "delay": time,
        "channel": channel,
        "repeat": repeat,
        "desc": description,
        "content": content,
        "duration": duration,
        "pin": None if pin is None else str(pin).lower(),
        "publish": None if publish is None else str(publish).lower()
    }

    try:
        await edit_delay_message(params)
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=f"Edit request completed for message **{message_id}**.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "Edit"), color=0xff0000)
        )


@slash_edit.autocomplete("message")
async def slash_edit_message_autocomplete(interaction: discord.Interaction, current: str):
    special_choices = []

    if interaction.guild is not None and get_last_stored_message_id(
        interaction.user.id,
        interaction.guild.id
    ):
        special_choices.append(
            ("last", "last - your most recently scheduled message")
        )

    return stored_message_autocomplete(
        interaction,
        current,
        special_choices=special_choices
    )


@slash_edit.autocomplete("channel")
async def slash_edit_channel_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return schedule_channel_autocomplete(interaction, current)


@template_group.command(
    name="create",
    description="Create a reusable GiggleMe message template"
)
@app_commands.guild_only()
@app_commands.describe(
    content="Message body to store in the template",
    channel="Default delivery channel; defaults to this channel",
    description="Short description used when listing the template"
)
async def slash_template_create(
    interaction: discord.Interaction,
    content: str,
    channel: Optional[str] = None,
    description: Optional[str] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    if channel == AUTOCOMPLETE_NO_CHANNELS:
        await interaction.response.send_message(
            "GiggleMe does not currently have permission to deliver messages "
            "to any text channel in this server."
        )
        return

    await interaction.response.defer()

    params = {
        "guild": interaction.guild,
        "request_channel": interaction.channel,
        "request_message_id": interaction.id,
        "author_id": interaction.user.id,
        "delay": "template",
        "content": content,
        "channel": channel,
        "desc": description
    }

    try:
        await process_delay_message(params)
        await interaction.edit_original_response(
            embed=discord.Embed(
                description="Template creation completed.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=slash_error_text(e, "Templates"),
                color=0xff0000
            )
        )


@slash_template_create.autocomplete("channel")
async def slash_template_create_channel_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return schedule_channel_autocomplete(interaction, current)


@giggle_group.command(
    name="schedule",
    description="Schedule a message for future delivery"
)
@app_commands.guild_only()
@app_commands.describe(
    time="When: 0=now, 15=15 min from now, or 8-14 9:30 PM / 2026-8-14 21:30",
    content="Message body; omit when using from_template",
    channel="Destination channel; suggestions include channels GiggleMe can send to",
    repeat_unit="Unit between repeated deliveries",
    repeat_every="Number of repeat units between deliveries",
    description="Short description used when listing the message",
    from_template="Stored template ID to use as the message body",
    duration_unit="Unit for how long the repeat remains active",
    duration_for="Number of duration units",
    pin="Pin the delivered message",
    publish="Publish the delivered message",
    set_topic="Set the channel topic instead of posting a message",
    set_channel_name="Set the channel name instead of posting a message"
)
@app_commands.choices(
    repeat_unit=[
        app_commands.Choice(name="Minutes", value="minutes"),
        app_commands.Choice(name="Hours", value="hours"),
        app_commands.Choice(name="Days", value="days"),
        app_commands.Choice(name="Weeks", value="weeks"),
        app_commands.Choice(name="Months", value="months")
    ],
    duration_unit=[
        app_commands.Choice(name="Minutes", value="minutes"),
        app_commands.Choice(name="Hours", value="hours"),
        app_commands.Choice(name="Days", value="days"),
        app_commands.Choice(name="Weeks", value="weeks"),
        app_commands.Choice(name="Months", value="months")
    ]
)
async def slash_schedule(
    interaction: discord.Interaction,
    time: str,
    content: Optional[str] = None,
    channel: Optional[str] = None,
    repeat_unit: Optional[str] = None,
    repeat_every: Optional[int] = None,
    description: Optional[str] = None,
    from_template: Optional[str] = None,
    duration_unit: Optional[str] = None,
    duration_for: Optional[int] = None,
    pin: Optional[bool] = None,
    publish: Optional[bool] = None,
    set_topic: Optional[bool] = None,
    set_channel_name: Optional[bool] = None
):
    if not await prepare_slash_interaction(interaction):
        return

    if from_template:
        from_template = from_template.strip().casefold()

    if from_template and await reject_message_autocomplete_sentinel(
        interaction,
        from_template
    ):
        return

    if channel == AUTOCOMPLETE_NO_CHANNELS:
        await interaction.response.send_message(
            "GiggleMe does not currently have permission to deliver messages "
            "to any text channel in this server."
        )
        return

    try:
        repeat = build_slash_interval(repeat_unit, repeat_every, "repeat")
        duration = build_slash_interval(duration_unit, duration_for, "duration")
    except GigException as e:
        await interaction.response.send_message(
            embed=discord.Embed(description=str(e), color=0xff0000)
        )
        return

    await interaction.response.defer()

    params = {
        "guild": interaction.guild,
        "request_channel": interaction.channel,
        "request_message_id": interaction.id,
        "author_id": interaction.user.id,
        "delay": time,
        "content": content,
        "channel": channel,
        "repeat": repeat,
        "desc": description,
        "from_template": from_template,
        "duration": duration,
        "pin": None if pin is None else str(pin).lower(),
        "publish": None if publish is None else str(publish).lower(),
        "set-topic": None if set_topic is None else str(set_topic).lower(),
        "set-channel-name": (
            None if set_channel_name is None else str(set_channel_name).lower()
        )
    }

    try:
        await process_delay_message(params)
        await interaction.edit_original_response(
            embed=discord.Embed(
                description="Schedule request completed.",
                color=0x00ff00
            )
        )
    except GigException as e:
        await interaction.edit_original_response(
            embed=discord.Embed(description=slash_error_text(e, "Schedule"), color=0xff0000)
        )


@slash_schedule.autocomplete("channel")
async def slash_schedule_channel_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return schedule_channel_autocomplete(interaction, current)


@slash_schedule.autocomplete("from_template")
async def slash_schedule_template_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    return stored_message_autocomplete(
        interaction,
        current,
        allowed_types=(Template,)
    )


@giggle_group.command(
    name="legacy",
    description="Schedule using GiggleMe's old text-command syntax"
)
@app_commands.guild_only()
@app_commands.describe(
    input="Paste old scheduling text or Raw+ output"
)
async def slash_legacy(
    interaction: discord.Interaction,
    input: str
):
    if not await prepare_slash_interaction(interaction):
        return

    legacy_input = input.strip()

    # Accept a whole Discord code block as well as just its contents.
    if legacy_input.startswith("```") and legacy_input.endswith("```"):
        legacy_input = re.sub(
            r"^```(?:text)?[ \t]*\n?",
            "",
            legacy_input,
            count=1,
            flags=re.IGNORECASE
        )
        legacy_input = re.sub(
            r"\n?```$",
            "",
            legacy_input,
            count=1
        ).strip()

    # Raw+ includes the old prefix. It is optional here.
    legacy_input = re.sub(
        r"^~g(?:iggle)?\s+",
        "",
        legacy_input,
        count=1,
        flags=re.IGNORECASE
    )

    # Deliberately accept only the old unnamed scheduling grammar.
    match = re.match(
        r"^((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}"
        r"(:\d{1,2})?( +(AM|PM))?|\d+)"
        r"( +([^\n]+))?( *\n(.*))?$",
        legacy_input,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        await interaction.response.send_message(
            embed=legacy_slash_help_embed()
        )
        return

    await interaction.response.defer()

    params = {
        "guild": interaction.guild,
        "request_channel": interaction.channel,
        "request_message_id": interaction.id,
        "author_id": interaction.user.id,
        "delay": match.group(1),
        "content": match.group(9)
    }

    try:
        await parse_args(
            process_delay_message,
            params,
            match.group(7)
        )
        await interaction.edit_original_response(
            embed=discord.Embed(
                description="Legacy schedule request completed.",
                color=0x00ff00
            )
        )
    except (GigParseException, GigException) as e:
        await interaction.edit_original_response(
            embed=discord.Embed(
                description=slash_error_text(e, "Legacy scheduler"),
                color=0xff0000
            )
        )


@giggle_group.command(name="help", description="Show help for GiggleMe slash commands")
@app_commands.describe(command="Slash command to show help for")
@app_commands.choices(command=[
    app_commands.Choice(name="Timezone", value="timezone"),
    app_commands.Choice(name="Time format", value="time-format"),
    app_commands.Choice(name="List", value="list"),
    app_commands.Choice(name="Show", value="show"),
    app_commands.Choice(name="Send", value="send"),
    app_commands.Choice(name="Cancel", value="cancel"),
    app_commands.Choice(name="Edit sent", value="edit-sent"),
    app_commands.Choice(name="Edit", value="edit"),
    app_commands.Choice(name="Schedule", value="schedule"),
    app_commands.Choice(name="Legacy scheduler", value="legacy"),
    app_commands.Choice(name="Templates", value="templates"),
    app_commands.Choice(name="VIPs", value="vip"),
    app_commands.Choice(name="User permissions", value="users"),
    app_commands.Choice(name="Test", value="test")
])
async def slash_help(interaction: discord.Interaction, command: Optional[str] = None):
    await interaction.response.send_message(embed=slash_help_embed(command))


giggle_group.add_command(template_group)
giggle_group.add_command(vip_group)
giggle_group.add_command(user_group)
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

                elif delivery_time == -2:
                    delayed_messages[msg_id] = AutoReply(id=msg_id, guild_id=row[1], delivery_channel_id=row[2], author_id=row[4], trigger=row[5],
                            content=row[7], description=row[8], special_handling=row[10], update_db=False)
                elif delivery_time is None:
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

        elif delivery_time == -2:
            delayed_messages[message_id] = AutoReply(id=message_id, guild_id=row[1], delivery_channel_id=row[2], author_id=row[4], trigger=row[5],
                    content=row[7], description=row[8], special_handling=row[10], update_db=False)
        elif delivery_time is None:
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

def build_slash_interval(unit, amount, label, allow_none=False):
    """Convert structured slash options into GiggleMe's stored interval string."""
    if unit is None and amount is None:
        return None

    if unit is None:
        raise GigException(f"Select a {label} unit when specifying an amount")

    if unit == "none":
        if not allow_none:
            raise GigException(f"{label.capitalize()} cannot be removed here")
        if amount is not None:
            raise GigException(
                f"Do not specify a {label} amount when selecting {unit}"
            )
        return "none"

    if amount is None:
        raise GigException(f"Enter a {label} amount after selecting {unit}")

    if amount <= 0:
        raise GigException(f"{label.capitalize()} amount must be greater than 0")

    return f"{unit}:{amount}"


def parse_repeat_interval(repeat):
    """Return (unit, amount, skip_if) for current and legacy repeat strings."""
    if not repeat:
        return None

    match = re.match(
        r'^(minutes|hours|days|weeks|months):(\d+)(?:;skip_if=(\d+))?$',
        repeat,
        re.IGNORECASE
    )
    if match:
        return (
            match.group(1).lower(),
            int(match.group(2)),
            None if match.group(3) is None else int(match.group(3))
        )

    match = re.match(
        r'^(daily|weekly|monthly)(?:;skip_if=(\d+))?$',
        repeat,
        re.IGNORECASE
    )
    if not match:
        return None

    legacy = {
        "daily": ("days", 1),
        "weekly": ("weeks", 1),
        "monthly": ("months", 1)
    }
    unit, amount = legacy[match.group(1).lower()]
    return (
        unit,
        amount,
        None if match.group(2) is None else int(match.group(2))
    )


def add_interval(delivery_time, unit, amount, user_id):
    timezone_id = giguser.users[user_id].timezone

    if unit == "minutes":
        return gigtz.add_minutes(delivery_time, amount, timezone_id)
    if unit == "hours":
        return gigtz.add_hours(delivery_time, amount, timezone_id)
    if unit == "days":
        return gigtz.add_days(delivery_time, amount, timezone_id)
    if unit == "weeks":
        for _ in range(amount):
            delivery_time = gigtz.add_week(delivery_time, timezone_id)
        return delivery_time
    if unit == "months":
        for _ in range(amount):
            delivery_time = gigtz.add_month(delivery_time, timezone_id)
        return delivery_time

    raise GigException(f"Invalid interval unit `{unit}`")


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

    # validate repeat string. Legacy daily/weekly/monthly values remain valid
    # so existing stored messages continue to work after the slash migration.
    repeat_output = ""
    if repeat:
        parsed_repeat = parse_repeat_interval(repeat)
        if not parsed_repeat:
            raise GigException(f"Invalid repeat string `{repeat}`")
        repeat_unit, repeat_amount, _ = parsed_repeat
        display_unit = repeat_unit[:-1] if repeat_amount == 1 else repeat_unit
        repeat_output = f" and will repeat every {repeat_amount} {display_unit}"

    if delay == 'template':
        if pin_message is not None:
            raise GigException("The **pin** option may not be used when creating a template")
        if set_topic is not None:
            raise GigException("The **set-topic** option may not be used when creating a template")
        if set_channel_name is not None:
            raise GigException("The **set-channel-name** option may not be used when creating a template")
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
        if not re.match(r'((minutes|hours|days|weeks|months):\d+|[Nn]one)$', duration):
            raise GigException("Invalid value for duration")
        if duration.lower() == "none":
            repeat_until = None
        elif delivery_time == 0:
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
    else:
        newMessage = Template(id=None, guild_id=guild.id, delivery_channel_id=delivery_channel.id,
                author_id=author_id, content=content, description=description)

    delayed_messages[newMessage.id] = newMessage

    if type(newMessage) is Template:
        if request_channel:
            embed=discord.Embed(description=f"Your template has been created", color=0x00ff00)
            embed.add_field(name="Template ID", value=f"{newMessage.id}", inline=True)
            await request_channel.send(embed=embed)
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

    # Delivery may be minutes, hours, or days away. Do not keep the command
    # handler waiting for the delivery coroutine to finish; register it as a
    # background task and return once the message has been scheduled.
    asyncio.create_task(schedule_delay_message(newMessage))

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
            parsed_repeat = parse_repeat_interval(msg.repeat)
            skip_if = (
                parsed_repeat[2]
                if parsed_repeat and parsed_repeat[2] is not None
                else 1
            )
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
            parsed_repeat = parse_repeat_interval(msg.repeat)
            if parsed_repeat:
                repeat_unit, repeat_amount, _ = parsed_repeat
                msg.delivery_time = add_interval(
                    msg.delivery_time,
                    repeat_unit,
                    repeat_amount,
                    msg.author_id
                )
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

    if message_type == 'templates' and max_count:
        raise GigException("**next** not valid with Templates")
    if message_type is None:
        output = "> **====================**\n>  **Scheduled Messages**\n> **====================**\n"
    else:
        output = f"> **====================**\n>  **{message_type.capitalize()}**\n> **====================**\n"

    sorted_messages = {}
    for msg_id in delayed_messages:
        if message_type == 'templates':
            if type(delayed_messages[msg_id]) is Template:
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

    if message_type != 'templates' and message_type != 'auto-replies':
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

async def show_delayed_message(channel, author_id, msg_num, raw, always_show_id=False):
    show_id = always_show_id
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
        if msg_num == "last":
            description = "Your most recently scheduled message is no longer stored"
        elif msg_num == "next":
            description = "There is no scheduled message available as next"
        else:
            description = f"Message {msg_num} not found"
        await channel.send(embed=discord.Embed(description=description, color=0xff0000))

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
                if repeat.lower() != "none" and not parse_repeat_interval(repeat):
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
            if not re.match(r'((minutes|hours|days|weeks|months):\d+|[Nn]one)$', duration):
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

        await discord_message.channel.send(embed=embed)

    else:
        await discord_message.channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

def add_duration(delivery_time, duration, user_id):
    match = re.match(r'^(minutes|hours|days|weeks|months):(\d+)$', duration)
    if not match:
        raise GigException(f"Invalid duration `{duration}`")
    return add_interval(
        delivery_time,
        match.group(1),
        int(match.group(2)),
        user_id
    )

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

        await channel.send(embed=discord.Embed(description=f"{type(delayed_messages[msg_num]).__name__} deleted", color=0x00ff00))
        delayed_messages.pop(msg_num).delete_from_db()
    else:
        await channel.send(embed=discord.Embed(description="Message not found", color=0xff0000))

async def show_guild_config(msg):
    output = f"**Config Settings**"
    output += "\n**approval_channel**:  "
    try:
        output += get_channel_by_name_or_id(msg.guild, str(gigguild.guilds[msg.guild.id].approval_channel_id)).mention
    except:
        output += str(gigguild.guilds[msg.guild.id].approval_channel_id)
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
    approval_channel_param = params.pop('approval_channel', None)

    if params:
        raise GigException(f"Invalid command.  Parameter **{next(iter(params))}** is unrecognized\n\nTo see help type:\n\n`~giggle help`")

    output = ""
    if approval_channel_param:
        approval_channel = get_channel_by_name_or_id(msg.guild, approval_channel_param)
        gigguild.guilds[msg.guild.id].set_approval_channel_id(approval_channel.id)
        output += f"**approval_channel** set to **{approval_channel.mention}**\n"

    await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

# Auto Replies intentionally remain on the classic interface for now.
# They inspect arbitrary guild message text and therefore depend on Discord's
# privileged MESSAGE_CONTENT intent. Remove the AutoReply feature in the same
# change that removes that intent; do not spend migration effort moving it to
# slash commands.

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

                match = re.match(r'~g(iggle)? +(list|ls)( +((all)|(next( +\d+)?)))?( +(templates?|tmp|repeats?|a(uto(-replies)?)?)?)? *$', msg.content)
                if match:
                    await msg.channel.send(embed=list_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +show( +(raw\+?))?( +(\S+)|next) *$', msg.content)
                if match:
                    await msg.channel.send(embed=show_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +(cancel|delete|remove|clear|rm) +(\S+) *$', msg.content)
                if match:
                    await msg.channel.send(embed=cancel_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +send +(\S+) *$', msg.content)
                if match:
                    await msg.channel.send(embed=send_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +modify +(\d+) *\n(.*)$', msg.content)
                if match:
                    await msg.channel.send(embed=edit_sent_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +edit +(\S+)( +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|\d+))?( +([^\n]+))?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    await msg.channel.send(embed=edit_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +template( +[^\n]+)?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    await msg.channel.send(embed=template_slash_help_embed())
                    return

                # Classic unnamed scheduling is retired. Keep recognizing the
                # old syntax long enough to direct users to the slash interface.
                match = re.match(r'~g(iggle)? +((\d{4}-)?\d{1,2}-\d{1,2} +\d{1,2}:\d{1,2}(:\d{1,2})?( +(AM|PM))?|\d+)( +([^\n]+))?( *\n(.*))?$', msg.content, re.DOTALL)
                if match:
                    await msg.channel.send(embed=schedule_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +(time-format|tf)( +(12|24))? *$', msg.content)
                if match:
                    await msg.channel.send(embed=time_format_slash_help_embed())
                    return

                match = re.match(r'~g(iggle)? +(help|\?)( +(\S+))? *$', msg.content)
                if match:
                    await msg.channel.send(help.show_help(match.group(4)))
                    return

                match = re.match(r'~g(iggle)? +(timezone|tz)( +(\S+))? *$', msg.content)
                if match:
                    await msg.channel.send(embed=timezone_slash_help_embed())
                    return

                if re.match(r'~g(iggle)? +(timezones|tzs) *$', msg.content):
                    await msg.channel.send(embed=timezone_slash_help_embed())
                    return

                if re.match(r'~g(iggle)? +vip(?: +.*)?$', msg.content, re.DOTALL):
                    await msg.channel.send(embed=vip_slash_help_embed())
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
                    await msg.channel.send(embed=user_permissions_slash_help_embed())
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

    await client.change_presence(activity=discord.Game('/giggle help'))

@client.event
async def on_guild_join(guild):
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)

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
