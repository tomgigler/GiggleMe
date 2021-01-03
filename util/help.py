#!/usr/bin/env python

def show_help(command):
    if not command:
        return """To schedule <message> to be delivered to <channel> at <time>:

        `~giggle <time> channel=<channel> desc="<brief description>"`
        `<message>`

        <time> may be either a number of minutes from now
        or a DateTime of the format YYYY-MM-DD HH:MM(:SS)
        All times are UTC unless you have set your local
        time with the `~giggle timezone` command

        desc is an optional description of the message
        If included, it must come after channel and be surrounded by double quotes

        The following commands may be used to manage scheduled messages:

        `list`, `show`, `send`, `edit`, `cancel`, `timezone`, `timezones`, `help`

        To see help for one of the above commands:

        `~giggle help <command>`
        """

    if command == "list":
        return """`~giggle list`

        Display a list of currently scheduled messages for all users on this server
        """

    if command == "show":
        return """`~giggle show <message-id>`

        Show the contents of the message identified by <message-id>

        `~giggle show raw <message-id>`

        Show the raw (Markdown) message

        Note:  `last` may be used as <message-id> to reference your most recently scheduled message
        """

    if command == "send":
        return """`~giggle send <message-id>`

        Send message identified by <message-id> immediately and remove it from the queue
        Note:  `last` may be used as <message-id> to reference your most recently scheduled message
        """

    if command == "edit":
        return """`~giggle edit <message-id> <time> channel=<channel> desc="<desc>"`
        `<message>`

        Edit message identified by <message-id>.
        
        <time> may be either a number of minutes from now or a DateTime of the format YYYY-MM-DD HH:MM(:SS)
        If not specified, the current delivery time will be used.
        All times are UTC unless you have set your local time with the `~giggle timezone` command

        channel=<channel> is optional.  If not specified, the current delivery channel will be used.

        desc="<desc>" is optional.  If both channel and desc are included, desc must come after channel

        <message> is optional.  If specified, it will replace the body of the current message.

        Note:  `last` may be used as <message-id> to reference your most recently scheduled message
        """

    if command == "cancel":
        return """`~giggle cancel <message-id>`

        Cancel message identified by <message-id>
        Note:  `last` may be used as <message-id> to reference your most recently scheduled message

        `~giggle cancel all`

        Cancel all delayed messages scheduled by you.  You will be prompted for confirmation
        """

    if command == "timezone":
        return """`~giggle timezone <time zone>`

        Set your time zone to <time zone>

        `~giggle timezone`

        Display your currently set time zone
        """

    if command == "timezones":
        return """`~giggle timezones`

        Display a list of available time zones
        """

    if command == "help":
        return """`~giggle help <command>`

        Show the help for <command>

        `~giggle help`

        Show this help"""
