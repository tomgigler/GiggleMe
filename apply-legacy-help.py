#!/usr/bin/env python3
import ast
import re
import sys
from pathlib import Path


def replace_legacy_help_function(text):
    start = text.find("def legacy_slash_help_embed(")
    if start == -1:
        raise RuntimeError("Could not find legacy_slash_help_embed")

    end = text.find("\ndef schedule_slash_help_embed(", start)
    if end == -1:
        raise RuntimeError("Could not find schedule_slash_help_embed after legacy help")

    new_function = '''def legacy_slash_help_embed(topic=None):
    topic = (topic or "").strip().lower()
    topic = topic.replace("_", "-").replace(" ", "-")

    aliases = {
        "schedule": "",
        "options": "",
        "ch": "channel",
        "description": "desc",
        "template": "from-template",
        "from-template": "from-template",
        "from_template": "from-template",
        "topic": "set-topic",
        "channel-name": "set-channel-name",
        "set_channel_name": "set-channel-name",
        "raw": "raw+"
    }
    topic = aliases.get(topic, topic)

    if not topic:
        embed = discord.Embed(
            title="Legacy scheduler syntax",
            description=(
                "`/giggle legacy` runs GiggleMe's old text scheduling syntax "
                "without requiring Message Content."
            ),
            color=0x00ff00
        )
        embed.add_field(
            name="Command format",
            value=(
                "```text\\n"
                "~giggle <time> [option=value ...]\\n"
                "<message body>\\n"
                "```\\n"
                "The `~giggle` / `~g` prefix is optional inside `/giggle legacy`."
            ),
            inline=False
        )
        embed.add_field(
            name="Example",
            value=(
                "```text\\n"
                "~giggle 2026-08-14 21:30 channel=general "
                "repeat=hours:6 duration=days:2 desc=\\"status reminder\\"\\n"
                "Remember to post the status update\\n"
                "```"
            ),
            inline=False
        )
        embed.add_field(
            name="Options",
            value=(
                "`channel` · `repeat` · `duration` · `desc` · `from_template` · "
                "`pin` · `set-topic` · `set-channel-name` · `publish`"
            ),
            inline=False
        )
        embed.add_field(
            name="More help",
            value=(
                "Paste `~giggle help <topic>` into `/giggle legacy`.\\n"
                "Topics: `time`, `channel`, `repeat`, `duration`, `desc`, "
                "`from_template`, `pin`, `set-topic`, `set-channel-name`, "
                "`publish`, `raw+`."
            ),
            inline=False
        )
        return embed

    help_topics = {
        "time": (
            "Delivery time",
            (
                "`0` sends now. A positive integer is minutes from now.\\n"
                "`8-14 9:30 PM` or `8-14 21:30` uses the current year.\\n"
                "`2026-8-14 9:30 PM` or `2026-8-14 21:30` specifies the year.\\n"
                "Seconds are optional. Times use your configured GiggleMe time zone."
            )
        ),
        "channel": (
            "channel=<channel>",
            (
                "Select the delivery channel by name, channel mention/reference, or ID.\\n"
                "If omitted, GiggleMe uses the channel where `/giggle legacy` was invoked.\\n"
                "Example: `channel=general`"
            )
        ),
        "repeat": (
            "repeat=<frequency>",
            (
                "Repeat values: `minutes:N`, `hours:N`, `days:N`, `weeks:N`, "
                "or `months:N`, where N is a positive integer.\\n"
                "Legacy `daily`, `weekly`, and `monthly` values are also accepted.\\n"
                "Optional: append `;skip_if=N` to skip delivery when the previous "
                "delivery is among the last N messages.\\n"
                "Example: `repeat=hours:6;skip_if=3`"
            )
        ),
        "duration": (
            "duration=<duration>",
            (
                "Limits how long a repeating message remains active. It only makes "
                "sense with `repeat`.\\n"
                "Values: `minutes:N`, `hours:N`, `days:N`, `weeks:N`, or `months:N`.\\n"
                "Example: `duration=days:7`"
            )
        ),
        "desc": (
            "desc=<description>",
            (
                "Adds a short description to make stored messages easier to identify.\\n"
                "Quote descriptions containing spaces.\\n"
                "Example: `desc=\\"weekday status reminder\\"`"
            )
        ),
        "from-template": (
            "from_template=<template-id>",
            (
                "Builds the message from an existing GiggleMe template. Do not include "
                "a message body when using `from_template`.\\n"
                "If channel or description is omitted, the template can supply them.\\n"
                "Example: `from_template=ABC12345`"
            )
        ),
        "pin": (
            "pin=true",
            (
                "Pins the delivered message. GiggleMe must have permission to manage "
                "messages in the destination channel.\\n"
                "`pin` cannot be combined with `set-topic` or `set-channel-name`."
            )
        ),
        "set-topic": (
            "set-topic=true",
            (
                "Uses the message body as the destination channel topic instead of "
                "posting a message. GiggleMe needs Manage Channels permission.\\n"
                "Cannot be combined with `pin`, `set-channel-name`, or `publish`."
            )
        ),
        "set-channel-name": (
            "set-channel-name=true",
            (
                "Uses the message body as the destination channel name instead of "
                "posting a message. GiggleMe needs Manage Channels permission.\\n"
                "Cannot be combined with `pin`, `set-topic`, or `publish`."
            )
        ),
        "publish": (
            "publish=true",
            (
                "Publishes the delivered message when the destination supports "
                "publishing.\\n"
                "Cannot be combined with `set-topic` or `set-channel-name`."
            )
        ),
        "raw+": (
            "Raw+ workflow",
            (
                "Use `/giggle show` with **Raw+** to reconstruct a stored message as "
                "legacy scheduling text. Copy it, edit the time/body/options, then "
                "paste it into `/giggle legacy`.\\n"
                "This is useful when creating several similar scheduled messages."
            )
        )
    }

    if topic not in help_topics:
        embed = legacy_slash_help_embed()
        embed.add_field(
            name="Unknown help topic",
            value=f"`{topic}` is not a legacy scheduler help topic.",
            inline=False
        )
        return embed

    title, value = help_topics[topic]
    embed = discord.Embed(
        title=f"Legacy help: {title}",
        description=value,
        color=0x00ff00
    )
    embed.add_field(
        name="Back to legacy help",
        value="Paste `~giggle help` into `/giggle legacy`.",
        inline=False
    )
    return embed

'''
    return text[:start] + new_function + text[end + 1:]


def add_help_interpreter(text):
    marker = '''    # Deliberately accept only the old unnamed scheduling grammar.
    match = re.match(
'''
    if "legacy_help_match = re.fullmatch(" in text:
        return text

    count = text.count(marker)
    if count != 1:
        raise RuntimeError(
            "Could not uniquely find legacy scheduling grammar marker "
            "(found {})".format(count)
        )

    block = '''    # The legacy interpreter has its own compact help mini-language.
    # Accept the old help spellings with or without the historical prefix:
    #   help
    #   ?
    #   help repeat
    #   ~giggle help duration
    legacy_help_match = re.fullmatch(
        r"(?:help|\\?)(?:\\s+(.+?))?\\s*",
        legacy_input,
        re.IGNORECASE
    )
    if legacy_help_match:
        await interaction.response.send_message(
            embed=legacy_slash_help_embed(legacy_help_match.group(1))
        )
        return

'''
    return text.replace(marker, block + marker, 1)


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "gigglebot.py")
    if not path.exists():
        raise SystemExit("Cannot find {}".format(path))

    text = path.read_text(encoding="utf-8")
    text = replace_legacy_help_function(text)
    text = add_help_interpreter(text)

    ast.parse(text, filename=str(path))
    path.write_text(text, encoding="utf-8")

    print("Updated {}".format(path))
    print("Syntax check: PASS")
    print("Legacy help mini-language: PASS")


if __name__ == "__main__":
    main()
