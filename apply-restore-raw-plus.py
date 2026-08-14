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


def update_gigglebot(path):
    text = path.read_text(encoding="utf-8")

    text = replace_one(
        text,
        '        value="Choose normal output or raw Markdown.",',
        '        value="Choose normal, raw Markdown, or Raw+ for text ready to paste into `/giggle legacy`.",',
        "show help format"
    )

    text = replace_one(
        text,
        """@app_commands.choices(format=[
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="Raw Markdown", value="raw")
])
""",
        """@app_commands.choices(format=[
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="Raw Markdown", value="raw"),
    app_commands.Choice(name="Raw+ (legacy recreation)", value="raw+")
])
""",
        "show format choices"
    )

    # While the classic parser still exists, recognize old raw+ only to
    # redirect users to slash help.
    text = text.replace(
        r"~g(iggle)? +show( +(raw))?( +(\S+)|next) *$",
        r"~g(iggle)? +show( +(raw\+?))?( +(\S+)|next) *$"
    )

    # Fix the examples added with /giggle legacy. Parameters use name=value;
    # interval values themselves still use the colon, e.g. hours:6.
    text = text.replace(
        "`5 channel:general repeat:hours:6`",
        "`5 channel=general repeat=hours:6`"
    )

    ast.parse(text, filename=str(path))
    path.write_text(text, encoding="utf-8")


def update_delayed_message(path):
    text = path.read_text(encoding="utf-8")

    old_base = """    def get_show_content(self, raw=False, timezone=None):
        if raw:
            return "```\\n" + self.content + "\\n```"
        return self.content

class Message(DelayedMessage):
"""

    new_base = """    def get_show_content(self, raw=False, timezone=None):
        if raw == "raw+":
            return self.content + "\\n```"
        if raw:
            return "```\\n" + self.content + "\\n```"
        return self.content

class Message(DelayedMessage):
"""

    text = replace_one(
        text,
        old_base,
        new_base,
        "base Raw+ content"
    )

    if 'if raw == "raw+":\n            command = f"~giggle ' not in text:
        anchor = """    def update_db(self):
        gigdb.update_message(self.id, self.guild_id, self.delivery_channel_id, self.delivery_time, self.author_id, self.repeat, self.last_repeat_message, self.content, self.description, self.repeat_until, self.special_handling)
"""

        method = """    def get_show_content(self, raw=False, timezone=None):
        if raw != "raw+":
            return super().get_show_content(raw, timezone)

        command = f"~giggle {gigtz.command_localized_time(self.delivery_time, timezone)}"
        command += f" channel={self.delivery_channel_id}"

        if self.repeat:
            command += f" repeat={self.repeat}"

        if self.repeat_until:
            # The original duration unit is not persisted. Emit elapsed
            # minutes so Raw+ always produces valid legacy-scheduler syntax.
            duration_minutes = max(
                1,
                int(round((self.repeat_until - self.delivery_time) / 60))
            )
            command += f" duration=minutes:{duration_minutes}"

        if self.special_handling and self.special_handling & 8:
            command += " pin=true"
        if self.special_handling and self.special_handling & 16:
            command += " set-topic=true"
        if self.special_handling and self.special_handling & 32:
            command += " set-channel-name=true"
        if self.special_handling and self.special_handling & 64:
            command += " publish=true"
        if self.description:
            command += f' desc="{self.description}"'

        return "```\\n" + command + "\\n" + super().get_show_content(raw, timezone)

"""

        count = text.count(anchor)
        if count != 1:
            raise RuntimeError(
                "Message update_db anchor: expected 1 match, found {}".format(count)
            )
        text = text.replace(anchor, method + anchor, 1)

    ast.parse(text, filename=str(path))
    path.write_text(text, encoding="utf-8")


def update_gigtz(path):
    text = path.read_text(encoding="utf-8")

    if "def command_localized_time(" not in text:
        anchor = "def load_timezones():\n"
        method = """def command_localized_time(timestamp, tz_id):
    # Format a stored delivery time for /giggle legacy input.
    if tz_id is None:
        tz_id = 1
    tz = timezone(timezones[tz_id].name)
    return datetime.fromtimestamp(timestamp).astimezone(tz).strftime(
        '%Y-%m-%d %-H:%M:%S'
    )


"""
        pos = text.find(anchor)
        if pos == -1:
            raise RuntimeError("Could not find load_timezones in util/gigtz.py")
        text = text[:pos] + method + text[pos:]

    ast.parse(text, filename=str(path))
    path.write_text(text, encoding="utf-8")


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    gigglebot = root / "gigglebot.py"
    delayed = root / "util" / "delayed_message.py"
    gigtz = root / "util" / "gigtz.py"

    for path in (gigglebot, delayed, gigtz):
        if not path.exists():
            raise SystemExit("Cannot find {}".format(path))

    update_gigglebot(gigglebot)
    update_delayed_message(delayed)
    update_gigtz(gigtz)

    print("Updated gigglebot.py")
    print("Updated util/delayed_message.py")
    print("Updated util/gigtz.py")
    print("Syntax checks: PASS")
    print("Raw+ legacy recreation: PASS")


if __name__ == "__main__":
    main()
