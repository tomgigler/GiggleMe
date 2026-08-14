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

    text = replace_one(
        text,
        '    time="Minutes from now, 0 for now, or a date/time",',
        '    time="When: 0=now, 15=15 min from now, or 8-14 9:30 PM / 2026-8-14 21:30",',
        "schedule time description"
    )

    text = replace_one(
        text,
        '    time="New delivery time or minutes from now",',
        '    time="New time: 0=now, 15=15 min from now, or 8-14 9:30 PM / 2026-8-14 21:30",',
        "edit time description"
    )

    text = replace_one(
        text,
        '            "`time` - minutes from now or a date/time such as `08-14 09:30`\\n"',
        '            "`time` - when to deliver; see the Time formats section below\\n"',
        "schedule required time help"
    )

    old_schedule_time = '''    embed.add_field(
        name="Time",
        value=(
            "The time uses your configured GiggleMe time zone. A number means "
            "that many minutes from now; `0` sends immediately."
        ),
        inline=False
    )
'''

    new_schedule_time = '''    embed.add_field(
        name="Time formats",
        value=(
            "All times use your configured GiggleMe time zone.\\n"
            "`0` - send now\\n"
            "`15` - send 15 minutes from now\\n"
            "`8-14 9:30 PM` - August 14 at 9:30 PM in the current year\\n"
            "`8-14 21:30` - August 14 at 21:30 in the current year\\n"
            "`2026-8-14 9:30 PM` - explicit year, 12-hour time\\n"
            "`2026-8-14 21:30` - explicit year, 24-hour time\\n"
            "Seconds are optional, for example `21:30:15`."
        ),
        inline=False
    )
'''
    text = replace_one(
        text,
        old_schedule_time,
        new_schedule_time,
        "schedule time formats help"
    )

    text = replace_one(
        text,
        '            "`time` - new delivery time or minutes from now\\n"',
        '            "`time` - new delivery time; uses the same formats as `/giggle schedule`\\n"',
        "edit time help"
    )

    note_anchor = '''    embed.add_field(
        name="Note",
'''

    edit_time_field = '''    embed.add_field(
        name="Time formats",
        value=(
            "`0` - send now\\n"
            "`15` - 15 minutes from now\\n"
            "`8-14 9:30 PM` or `8-14 21:30` - current year\\n"
            "`2026-8-14 9:30 PM` or `2026-8-14 21:30` - explicit year\\n"
            "All times use your configured GiggleMe time zone."
        ),
        inline=False
    )
'''

    edit_start = text.find("def edit_slash_help_embed():")
    if edit_start == -1:
        raise RuntimeError("Could not find edit_slash_help_embed")

    edit_end = text.find("\ndef ", edit_start + 1)
    if edit_end == -1:
        edit_end = len(text)

    edit_block = text[edit_start:edit_end]
    if 'name="Time formats"' not in edit_block:
        anchor_pos = edit_block.find(note_anchor)
        if anchor_pos == -1:
            raise RuntimeError("Could not find Edit help Note field")
        edit_block = (
            edit_block[:anchor_pos]
            + edit_time_field
            + edit_block[anchor_pos:]
        )
        text = text[:edit_start] + edit_block + text[edit_end:]

    ast.parse(text, filename=str(path))

    path.write_text(text, encoding="utf-8")
    print("Updated {}".format(path))
    print("Syntax check: PASS")
    print("Time-help clarification: PASS")


if __name__ == "__main__":
    main()
