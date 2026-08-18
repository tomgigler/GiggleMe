# Moving from `~giggle` to `/giggle`

GiggleMe's primary command interface has moved from classic `~giggle` / `~g`
prefix commands to Discord slash commands.

The slash commands provide Discord-native command discovery, option descriptions,
autocomplete, and validation. Start typing:

```text
/giggle
```

to see the available commands.

## Common command translations

| Classic command | Slash command |
| --- | --- |
| `~g list` | `/giggle list` |
| `~g show <id>` | `/giggle show message:<id>` |
| `~g show raw <id>` | `/giggle show message:<id> format:Raw Markdown` |
| `~g show raw+ <id>` | `/giggle show message:<id> format:Raw+` |
| `~g send <id>` | `/giggle send message:<id>` |
| `~g cancel <id>` | `/giggle cancel message:<id>` |
| `~g modify <discord-message-id>` | `/giggle edit-sent` |
| `~g edit <id> ...` | `/giggle edit` |
| `~g template ...` | `/giggle template create` |
| `~g auto-reply <trigger> ...` | `/giggle auto-reply create` |
| `~g <time> ...` | `/giggle schedule` |
| `~g timezone` / `~g tz` | `/giggle timezone` |
| `~g timezones` / `~g tzs` | `/giggle timezone` and use autocomplete |
| `~g time-format` / `~g tf` | `/giggle time-format` |
| `~g vip list` | `/giggle vip list` |
| `~g vip add ...` | `/giggle vip add` |
| `~g vip remove ...` | `/giggle vip remove` |
| `~g adduser ...` | `/giggle user grant` |
| `~g help` | `/giggle help` |

Aliases such as `delete`, `remove`, `clear`, and `rm` that previously canceled
stored messages are replaced by `/giggle cancel`.

## Scheduling messages

The classic scheduler packed the delivery time, options, and message body into
one text command:

```text
~giggle 8-20 9:30 PM channel=general repeat=days:1
This is the message body
```

With slash commands, use:

```text
/giggle schedule
```

Discord will present the available fields individually. The delivery time is
still entered as text so existing GiggleMe time formats remain familiar.

Examples of supported time values include:

```text
0
15
8-20 9:30 PM
8-20 21:30
2026-8-20 9:30 PM
2026-8-20 21:30
```

`0` means now and a bare positive integer is a number of minutes from now.

Repeat and duration values no longer need to be typed as command-line syntax.
Choose the unit and enter the number directly in the slash command.

## Finding stored messages

Commands that operate on stored messages use Discord autocomplete where
possible. Begin typing a message ID or description and GiggleMe will offer
matching stored items.

Special references such as `last` and `next` are still available on commands
where they make sense.

## Raw and Raw+

`/giggle show` supports:

- **Normal** for the usual rendered message
- **Raw Markdown** for the stored message body
- **Raw+** for reconstructed classic scheduling text

Raw+ is useful when creating several similar schedules or when copying a
scheduled message into the GiggleMe web interface.

## Legacy compatibility

`/giggle legacy` provides a compatibility path for old GiggleMe command text.

Multiline classic scheduling text currently has a Discord limitation: text
pasted into a slash-command string option may lose the newline separating the
command options from the message body. For new schedules, `/giggle schedule`
is the recommended interface.

Some classic prefix functionality may remain available temporarily for
backward compatibility while the transition is completed.

## Auto Replies

Auto Replies are configured with `/giggle auto-reply create`. The trigger and
behavior options are supplied as slash-command fields, and GiggleMe then opens
a modal for the reply body.

The configured Auto Reply still intentionally examines normal server messages
for its trigger. Message Content therefore remains required for Auto Reply
matching even though Auto Reply configuration has moved to slash commands.

## Need help?

Use:

```text
/giggle help
```

and choose the command you want help with.
