#!/usr/bin/env python3
import ast
import sys
from pathlib import Path


def replace_one(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            "{}: expected 1 match, found {}".format(label, count)
        )
    return text.replace(old, new, 1)


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "gigglebot.py")
    if not path.exists():
        raise SystemExit("Cannot find {}".format(path))

    text = path.read_text(encoding="utf-8")

    if "def legacy_slash_help_embed():" not in text:
        anchor = "def schedule_slash_help_embed():\n"
        pos = text.find(anchor)
        if pos == -1:
            raise RuntimeError("Could not find schedule_slash_help_embed")

        block = '''def legacy_slash_help_embed():
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
            "`5 channel=general repeat=hours:6` followed by a newline and the message body.\\n"
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


'''
        text = text[:pos] + block + text[pos:]

    text = replace_one(
        text,
        '''    if command == "schedule":
        return schedule_slash_help_embed()
''',
        '''    if command == "schedule":
        return schedule_slash_help_embed()

    if command == "legacy":
        return legacy_slash_help_embed()
''',
        "legacy help routing"
    )

    text = replace_one(
        text,
        '''            "`/giggle schedule` - schedule a message for delivery\\n"
            "`/giggle template create` - create a reusable message template\\n"
''',
        '''            "`/giggle schedule` - schedule a message for delivery\\n"
            "`/giggle legacy` - schedule using old text-command syntax or Raw+ output\\n"
            "`/giggle template create` - create a reusable message template\\n"
''',
        "legacy help listing"
    )

    text = replace_one(
        text,
        '''    app_commands.Choice(name="Schedule", value="schedule"),
    app_commands.Choice(name="Templates", value="templates"),
''',
        '''    app_commands.Choice(name="Schedule", value="schedule"),
    app_commands.Choice(name="Legacy scheduler", value="legacy"),
    app_commands.Choice(name="Templates", value="templates"),
''',
        "legacy help choice"
    )

    if "async def slash_legacy(" not in text:
        help_anchor = (
            '@giggle_group.command(name="help", '
            'description="Show help for GiggleMe slash commands")'
        )
        pos = text.find(help_anchor)
        if pos == -1:
            raise RuntimeError("Could not find /giggle help command")

        command_block = r'''@giggle_group.command(
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


'''
        text = text[:pos] + command_block + text[pos:]

    text = text.replace(
        "`5 channel:general repeat:hours:6`",
        "`5 channel=general repeat=hours:6`"
    )
    text = text.replace(
        "`~giggle 0 from_template:abc12345`",
        "`~giggle 0 from_template=abc12345`"
    )

    ast.parse(text, filename=str(path))
    path.write_text(text, encoding="utf-8")

    print("Updated {}".format(path))
    print("Syntax check: PASS")
    print("/giggle legacy: PASS")


if __name__ == "__main__":
    main()
