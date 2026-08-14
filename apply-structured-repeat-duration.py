#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path


def replace_exact(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} match(es), found {count}")
    return text.replace(old, new, expected)


def regex_replace(text: str, pattern: str, replacement: str, label: str, expected: int = 1, flags: int = 0) -> str:
    new_text, count = re.subn(pattern, lambda _m: replacement, text, count=expected, flags=flags)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} match(es), found {count}")
    return new_text


def get_function(text: str, name: str) -> tuple[int, int, str]:
    m = re.search(rf'^(?:async )?def {re.escape(name)}\(', text, re.MULTILINE)
    if not m:
        raise RuntimeError(f"Could not find function {name}")
    start = m.start()
    next_m = re.search(r'^(?:@|async def |def |class )', text[m.end():], re.MULTILINE)
    end = m.end() + next_m.start() if next_m else len(text)
    return start, end, text[start:end]


def replace_function(text: str, name: str, new_block: str) -> str:
    start, end, _ = get_function(text, name)
    return text[:start] + new_block + text[end:]


def edit_function(text: str, name: str, transform) -> str:
    start, end, block = get_function(text, name)
    block = transform(block)
    return text[:start] + block + text[end:]


EDIT_CHOICES = '''@app_commands.choices(
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
'''

SCHEDULE_CHOICES = '''@app_commands.choices(
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
'''

HELPERS = r'''def build_slash_interval(unit, amount, label, allow_none=False):
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


'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply structured repeat/duration options to GiggleMe")
    parser.add_argument("path", nargs="?", default="gigglebot.py")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"Cannot find {path}")

    text = path.read_text(encoding="utf-8")
    if "def build_slash_interval" in text or "repeat_unit: Optional[str]" in text:
        raise SystemExit("Structured repeat/duration changes appear to already be applied")

    # Help text. These replacements are narrow and do not include the channel line.
    text = replace_exact(
        text,
        '            "`repeat` - minutes:N, hours:N, daily, weekly, monthly, or none\\n"',
        '            "`repeat_unit` + `repeat_every` - repeat interval; choose minutes, "\n'
        '            "hours, days, weeks, or months. Choose Remove repeat to stop repeating.\\n"',
        "edit help repeat"
    )
    text = replace_exact(
        text,
        '            "`duration` - minutes:N, hours:N, days:N, or none\\n"',
        '            "`duration_unit` + `duration_for` - how long to repeat; choose minutes, "\n'
        '            "hours, days, weeks, or months. Choose No duration limit to clear it.\\n"',
        "edit help duration"
    )
    text = replace_exact(
        text,
        '            "`repeat` - minutes:N, hours:N, daily, weekly, or monthly\\n"',
        '            "`repeat_unit` + `repeat_every` - repeat interval in minutes, hours, "\n'
        '            "days, weeks, or months\\n"',
        "schedule help repeat"
    )
    text = replace_exact(
        text,
        '            "`duration` - minutes:N, hours:N, or days:N for repeating messages\\n"',
        '            "`duration_unit` + `duration_for` - how long the repeat remains active\\n"',
        "schedule help duration"
    )

    # Slash option descriptions.
    text = replace_exact(
        text,
        '    repeat="minutes:N, hours:N, daily, weekly, monthly, or none",',
        '    repeat_unit="Unit between repeated deliveries",\n'
        '    repeat_every="Number of repeat units between deliveries",',
        "edit describe repeat"
    )
    text = replace_exact(
        text,
        '    duration="minutes:N, hours:N, days:N, or none",',
        '    duration_unit="Unit for the repeat duration",\n'
        '    duration_for="Number of duration units",',
        "edit describe duration"
    )
    text = replace_exact(
        text,
        '    repeat="minutes:N, hours:N, daily, weekly, or monthly",',
        '    repeat_unit="Unit between repeated deliveries",\n'
        '    repeat_every="Number of repeat units between deliveries",',
        "schedule describe repeat"
    )
    text = replace_exact(
        text,
        '    duration="Repeat duration: minutes:N, hours:N, or days:N",',
        '    duration_unit="Unit for how long the repeat remains active",\n'
        '    duration_for="Number of duration units",',
        "schedule describe duration"
    )

    # Add choice decorators without depending on neighboring channel text.
    text = replace_exact(text, ')\nasync def slash_edit(\n', ')\n' + EDIT_CHOICES + 'async def slash_edit(\n', "edit choices")
    text = replace_exact(text, ')\nasync def slash_schedule(\n', ')\n' + SCHEDULE_CHOICES + 'async def slash_schedule(\n', "schedule choices")

    def change_slash_edit(block: str) -> str:
        block = replace_exact(
            block,
            '    repeat: Optional[str] = None,',
            '    repeat_unit: Optional[str] = None,\n    repeat_every: Optional[int] = None,',
            "edit signature repeat"
        )
        block = replace_exact(
            block,
            '    duration: Optional[str] = None,',
            '    duration_unit: Optional[str] = None,\n    duration_for: Optional[int] = None,',
            "edit signature duration"
        )
        block = replace_exact(
            block,
            '    if message_id is None:\n        return\n\n',
            '''    if message_id is None:\n        return\n\n    try:\n        repeat = build_slash_interval(\n            repeat_unit,\n            repeat_every,\n            "repeat",\n            allow_none=True\n        )\n        duration = build_slash_interval(\n            duration_unit,\n            duration_for,\n            "duration",\n            allow_none=True\n        )\n    except GigException as e:\n        await interaction.response.send_message(\n            embed=discord.Embed(description=str(e), color=0xff0000)\n        )\n        return\n\n''',
            "edit interval construction"
        )
        return block

    def change_slash_schedule(block: str) -> str:
        block = replace_exact(
            block,
            '    repeat: Optional[str] = None,',
            '    repeat_unit: Optional[str] = None,\n    repeat_every: Optional[int] = None,',
            "schedule signature repeat"
        )
        block = replace_exact(
            block,
            '    duration: Optional[str] = None,',
            '    duration_unit: Optional[str] = None,\n    duration_for: Optional[int] = None,',
            "schedule signature duration"
        )
        block = replace_exact(
            block,
            '    await interaction.response.defer()\n',
            '''    try:\n        repeat = build_slash_interval(repeat_unit, repeat_every, "repeat")\n        duration = build_slash_interval(duration_unit, duration_for, "duration")\n    except GigException as e:\n        await interaction.response.send_message(\n            embed=discord.Embed(description=str(e), color=0xff0000)\n        )\n        return\n\n    await interaction.response.defer()\n''',
            "schedule interval construction"
        )
        return block

    text = edit_function(text, "slash_edit", change_slash_edit)
    text = edit_function(text, "slash_schedule", change_slash_schedule)

    # Shared parser/arithmetic helpers.
    text = replace_exact(
        text,
        'async def process_delay_message(params):\n',
        HELPERS + 'async def process_delay_message(params):\n',
        "helper insertion"
    )

    # Existing repeat validation in process_delay_message.
    old_repeat_validation = '''    # validate repeat string\n    repeat_output = ""\n    if repeat:\n        match = re.match('((minutes:(\\d+))|(hours:(\\d+))|daily|weekly|monthly)(;skip_if=(\\d+))?$', repeat)\n        if not match:\n            raise GigException(f"Invalid repeat string `{repeat}`")\n        if not match.group(3) and not match.group(5):\n            repeat_output = f" and will repeat {match.group(1)}"\n        elif match.group(3):\n            repeat_output = f" and will repeat every {match.group(3)} minutes"\n        elif match.group(5):\n            repeat_output = f" and will repeat every {match.group(5)} hours"\n'''
    new_repeat_validation = '''    # validate repeat string. Legacy daily/weekly/monthly values remain valid\n    # so existing stored messages continue to work after the slash migration.\n    repeat_output = ""\n    if repeat:\n        parsed_repeat = parse_repeat_interval(repeat)\n        if not parsed_repeat:\n            raise GigException(f"Invalid repeat string `{repeat}`")\n        repeat_unit, repeat_amount, _ = parsed_repeat\n        display_unit = repeat_unit[:-1] if repeat_amount == 1 else repeat_unit\n        repeat_output = f" and will repeat every {repeat_amount} {display_unit}"\n'''
    text = replace_exact(text, old_repeat_validation, new_repeat_validation, "process repeat validation")

    # Duration validation occurs in process_delay_message and edit_delay_message.
    text = replace_exact(
        text,
        "        if not re.match(r'(minutes:\\d+|hours:\\d+|days:\\d+|[Nn]one)$', duration):",
        "        if not re.match(r'((minutes|hours|days|weeks|months):\\d+|[Nn]one)$', duration):",
        "duration validation",
        expected=2
    )

    # Only process_delay_message has the repeat_until setup directly after validation.
    text = replace_exact(
        text,
        '''        if delivery_time == 0:\n            repeat_until = add_duration(time(), duration, author_id)\n        else:\n            repeat_until = add_duration(delivery_time, duration, author_id)\n''',
        '''        if duration.lower() == "none":\n            repeat_until = None\n        elif delivery_time == 0:\n            repeat_until = add_duration(time(), duration, author_id)\n        else:\n            repeat_until = add_duration(delivery_time, duration, author_id)\n''',
        "duration none handling"
    )

    # Existing skip_if parsing for repeated messages.
    text = replace_exact(
        text,
        '''            match = re.match(r'(minutes:\\d+|hours:\\d+|daily|weekly|monthly);skip_if=(\\d+)', msg.repeat)\n            if match:\n                skip_if = int(match.group(2))\n            else:\n                skip_if = 1\n''',
        '''            parsed_repeat = parse_repeat_interval(msg.repeat)\n            skip_if = (\n                parsed_repeat[2]\n                if parsed_repeat and parsed_repeat[2] is not None\n                else 1\n            )\n''',
        "skip_if parsing"
    )

    # Rescheduling after delivery.
    old_reschedule = '''        if type(msg) is Message and msg.repeat is not None:\n            match = re.match(r'(minutes:(\\d+)|hours:(\\d+)|daily|weekly|monthly)', msg.repeat)\n            if match:\n                if match.group(2):\n                    msg.delivery_time = gigtz.add_minutes(msg.delivery_time, int(match.group(2)), giguser.users[msg.author_id].timezone)\n                elif match.group(3):\n                    msg.delivery_time = gigtz.add_hours(msg.delivery_time, int(match.group(3)), giguser.users[msg.author_id].timezone)\n                elif match.group(1) == 'daily':\n                    msg.delivery_time = gigtz.add_days(msg.delivery_time, 1, giguser.users[msg.author_id].timezone)\n                elif match.group(1) == 'weekly':\n                    msg.delivery_time = gigtz.add_week(msg.delivery_time, giguser.users[msg.author_id].timezone)\n                elif match.group(1) == 'monthly':\n                    msg.delivery_time = gigtz.add_month(msg.delivery_time, giguser.users[msg.author_id].timezone)\n'''
    new_reschedule = '''        if type(msg) is Message and msg.repeat is not None:\n            parsed_repeat = parse_repeat_interval(msg.repeat)\n            if parsed_repeat:\n                repeat_unit, repeat_amount, _ = parsed_repeat\n                msg.delivery_time = add_interval(\n                    msg.delivery_time,\n                    repeat_unit,\n                    repeat_amount,\n                    msg.author_id\n                )\n'''
    text = replace_exact(text, old_reschedule, new_reschedule, "repeat reschedule")

    # Edit validation accepts new stored forms while preserving legacy values.
    text = replace_exact(
        text,
        "                if not re.match('(minutes:\\d+|hours:\\d+|daily|weekly|monthly|[Nn]one)(;skip_if=\\d+)?$', repeat):",
        '                if repeat.lower() != "none" and not parse_repeat_interval(repeat):',
        "edit repeat validation"
    )

    new_add_duration = r'''def add_duration(delivery_time, duration, user_id):
    match = re.match(r'^(minutes|hours|days|weeks|months):(\d+)$', duration)
    if not match:
        raise GigException(f"Invalid duration `{duration}`")
    return add_interval(
        delivery_time,
        match.group(1),
        int(match.group(2)),
        user_id
    )

'''
    text = replace_function(text, "add_duration", new_add_duration)

    # Validate complete transformed file before replacing it.
    ast.parse(text, filename=str(path))
    required = (
        "repeat_unit: Optional[str]",
        "repeat_every: Optional[int]",
        "duration_unit: Optional[str]",
        "duration_for: Optional[int]",
        "def build_slash_interval",
        "def parse_repeat_interval",
        "def add_interval",
        'app_commands.Choice(name="Weeks", value="weeks")',
        'app_commands.Choice(name="Months", value="months")',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Sanity check failed: " + ", ".join(missing))

    temp = path.with_name(path.name + ".structured-options.tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)

    print(f"Updated {path}")
    print("Syntax check: PASS")
    print("Structured repeat/duration transformation: PASS")
    print("Review with: git diff -- gigglebot.py")


if __name__ == "__main__":
    main()
