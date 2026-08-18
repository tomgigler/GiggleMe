#!/usr/bin/env python

def show_help(command):
    if not command:
        return """> GiggleMe's normal command interface has moved to Discord slash commands.
> 
> Use `/giggle help` for current command help.
> 
> Schedule messages with `/giggle schedule`.
> Create templates with `/giggle template create`.
> Manage VIPs with `/giggle vip`.
> Manage user authorization with `/giggle user`.
> 
> Classic prefix help is temporarily retained as migration guidance.
> Auto Replies are configured with `/giggle auto-reply create`. Trigger matching still requires Message Content because triggers are ordinary server messages."""

    if command == "list":
        return """> `~giggle list <range>`
> 
> Display a list of currently scheduled messages for all users on this server
> **<range>** is optional and may be either `next` or `next <N>` where <N> is a positive integer
> 
> `~giggle list <range> repeats`
> 
> Display a list of repeating messages for all users on this server
> 
> `~giggle list templates`
> 
> Display a list of templates for all users on this server"""

    if command == "show":
        return """> `~giggle show <message-id>`
> 
> Show the contents of the message identified by <message-id>
> 
> `~giggle show raw <message-id>`
> 
> Show the raw (Markdown) message
> 
> **Note:**  `last` may be used as <message-id> to reference your most recently scheduled message
> `next` may be used as <message-id> to reference the next message in the queue
> 
> Both `show` and `show raw` may be used to show templates"""

    if command == "send":
        return """> `~giggle send <message-id>`
> 
> Send message identified by <message-id> immediately and remove it from the queue
> **Note:**  `last` may be used as <message-id> to reference your most recently scheduled message"""

    if command == "modify":
        return """> `~giggle modify <message-id>`
> `<content>`
> 
> replace the content of message identified by <message-id>
> **Note:**  `message-id` is the Discord message id"""

    if command == "edit":
        return """> `~giggle edit <message-id> <time> channel=<channel> repeat=<frequency> duration=<duration> desc="<desc> pin=<True|False>"`
> `<message>`
> 
> Edit message identified by **<message-id>**
> 
> **<time>** may be either a number of minutes from now or a DateTime of the format (YYYY-)MM-DD HH:MM(:SS)
> If not specified, the current delivery time will be used
> 
> **channel=<channel>** changes the message delivery channel to **<channel>**
> 
> **repeat** will repeat your message at the given frequency until you cancel the message or edit it with **repeat=none** unless you have specified a **duration** (see below)
> **<frequency>** may be `none`, `daily`, `weekly`, `monthly`, or `hours:<N>` or `minutes:<N>` where **<N>** is a positive integer
> **<frequency>** may also optionally be followed by `;skip_if=<N>` where **<N>** is a non-negative integer
> If **skip_if** is provided, the message delivery will be skipped if the last delivery is in the last N messages in the channel
> 
> for example: `repeat=daily;skip_if=5`
> 
> **duration** is a duration for repeating messages.  Your message will repeat with the given frequency for **<duration>**
> **<duration>** may be `minutes:<N>`, `hours:<N>`, or `days:<N>` where **<N>** is a positive integer
> You may also use `duration=none` to remove the current duration when editing a message.  This will result in the message repeating until you cancel it or edit again
> 
> **<desc>** is an optional description of the message
> 
> **pin** is optional.  If True, the new message will be pinned
> 
> **<message>** is optional.  If specified, it will replace the body of the current message
> 
> **Note:**  `last` may be used as **<message-id>** to reference your most recently scheduled message
> 
> `edit` may be used to edit templates.  When editing a template, the **<time>** and **repeat** options are not allowed"""

    if command == "cancel":
        return """> `~giggle cancel <message-id>`
> 
> Cancel message or delete template identified by <message-id>
> **Note:**  `last` may be used as <message-id> to reference your most recently scheduled message
> 
> `~giggle cancel all`
> 
> Cancel all delayed messages scheduled by you.  You will be prompted for confirmation
> `cancel all` has no effect on templates"""

    if command == "timezone":
        return """> `~giggle timezone <time zone>`
> 
> Set your time zone to <time zone>
> 
> `~giggle timezone`
> 
> Display your currently set time zone
> 
> To see a list of available time zones type `~giggle timezones`"""

    if command == "time-format":
        return """> `~giggle time-format <12 or 24>`
> 
> Set your time format for times displayed by the bot
> 
> `~giggle time-format`
> 
> Display your currently set time format"""

    if command == "timezones":
        return """> `~giggle timezones`
> 
> Display a list of available time zones"""

    if command == "template" or command == "templates":
        return """> Template creation has moved to the slash-command interface.
> 
> Use `/giggle template create` to create a reusable message template.
> 
> Existing templates may still be managed with the appropriate GiggleMe commands."""

    if command == "vip" or command == "vips":
        return """> VIP management has moved to the slash-command interface.
>
> Use `/giggle vip list` to list VIPs.
> Use `/giggle vip add` to add or update a VIP.
> Use `/giggle vip remove` to remove a VIP."""

    if command == "adduser":
        return """> `~giggle adduser <user-id> <guild-id>`
> 
> Grant a user permission to use GiggleMe.
> 
> **<guild-id>** is optional. If omitted, permission is granted for the current server.
> 
> This command is restricted to the configured bot owner."""

    if command == "help":
        return """> `~giggle help <command>`
> 
> Show the help for <command>
> 
> `~giggle help`
> 
> Show the main help"""

    if command == "repeat":
        return """> **repeat** is optional.  If included, your message will be repeated at the given frequency until you cancel the message
> or **edit** it with **repeat=none** or if an end time is set with **duration** (see below)
> 
> To schedule a repeating message, add `repeat=<frequency>` when creating the message
> You may also add `repeat=<frequency>` when editing a message.  Type `~giggle help edit` or more info on editing messages
> 
> **<frequency>** may be `daily`, `weekly`, `monthly`, or `hours:<N>` or `minutes:<N>` where **<N>** is a positive integer
> 
> For example: `repeat=minutes:20`
> 
> If the previous delivery of a repeating message is the last message in the channel the message will be deleted and replaced with the new delivery
> 
> **<frequency>** may also optionally be followed by `;skip_if=<N>` where **<N>** is a non-negative integer
> 
> If **skip_if** is provided, the message delivery will be skipped if the last delivery is in the last **<N>** messages in the channel
> For example: `repeat=daily;skip_if=5`
> 
> If **skip_if** is 0, the message will always be delivered and will not delete the previouse delivery as specified above
> 
> You may also include a **duration** when scheduling a repeating message.  To include a duration add `duration=<duration>` when scheduling the message
> 
> **<duration>** may be `minutes:<N>`, `hours:<N>`, or `days:<N>` where **<N>** is a positive integer
> 
> For example: `duration=hours:2`"""

    if command in ("auto", "auto-reply", "auto-replies"):
        return """> Auto Reply configuration has moved to Discord slash commands.
>
> Use `/giggle auto-reply create` to create an Auto Reply.
>
> Use `/giggle list category:Auto-replies`, `/giggle show`, `/giggle edit`, and `/giggle cancel` to manage existing Auto Replies.
>
> Auto Reply trigger matching still requires Discord Message Content because the triggering message is ordinary server text, not a slash command."""
    return f"> \"{command}\" is not a recognized help topic\n> \n> Available topics are `list`, `show`, `send`, `edit`, `cancel`, `timezone`, `timezones`, `help`, `repeat`, `template`, `auto-replies`, `vip`, `adduser`"
