#!/usr/bin/env python

def show_help(command):
    if not command:
        return """> To schedule **<message>** to be delivered to **<channel>** at **<time>**:
> 
> `~giggle <time> channel=<channel> repeat=<frequency> desc="<brief description>" from_template=<template_id>`
> `<message>`
> 
> **<time>** may be either a number of minutes from now or a DateTime of the format (YYYY-)MM-DD HH:MM(:SS)
> 
> **repeat** is optional.  If included, your message will be repeated at the given frequency until you cancel the message or **edit** it with **repeat=none**
> **<frequency>** may be `daily`, `weekly`, `monthly`, or `hours:NUM` or `minutes:NUM` where `NUM` is a positive integer
> If the previous delivery of a repeating message is the last message in the channel the message will be deleted and replaced with the new delivery
> **<frequency>** may also optionally be followed by `;skip_if=<N>` where N is a non-negative integer
> If **skip_if** is provided, the message delivery will be skipped if the last delivery is in the last N messages in the channel
> If **skip_if** is 0, the message will always be delivered and will not delete the previouse delivery as specified above
> 
> for example: `repeat=daily;skip_if=5`
> 
> **desc** is an optional description of the message
> 
> **from_template** creates the message body from the <template_id> template
> Do not include a message body when using from_template
> 
> To create a template:
> 
> `~giggle template channel=<channel> desc="<brief description>"`
> `<message>`
> 
> The following commands may be used to manage scheduled messages:
> 
> `list`, `show`, `send`, `edit`, `cancel`, `timezone`, `timezones`, `time-format`, `help`
> 
> To see help for one of the above commands:
> 
> `~giggle help <command>`"""

    if command == "list":
        return """> `~giggle list`
> 
> Display a list of currently scheduled messages for all users on this server
> 
> `~giggle list templates`
> 
> Display a list of templates for all users on this server
> 
> `~giggle list repeats`
> 
> Display a list of repeating messages for all users on this server"""

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
> 
> Both `show` and `show raw` may be used to show templates"""

    if command == "send":
        return """> `~giggle send <message-id>`
> 
> Send message identified by <message-id> immediately and remove it from the queue
> **Note:**  `last` may be used as <message-id> to reference your most recently scheduled message"""

    if command == "edit":
        return """> `~giggle edit <message-id> <time> channel=<channel> repeat=<frequency> desc="<desc>"`
> `<message>`
> 
> Edit message identified by <message-id>
> 
> <time> may be either a number of minutes from now or a DateTime of the format (YYYY-)MM-DD HH:MM(:SS)
> If not specified, the current delivery time will be used
> 
> channel=<channel> is optional.  If not specified, the current delivery channel will be used
> 
> repeat is optional.  If included, your message will be repeated at the given frequency until you cancel the message or edit it with repeat=none
> <frequency> may be `none`, `daily`, `weekly`, `monthly`, or `hours:NUM` or `minutes:NUM` where `NUM` is a positive integer
> <frequency> may also optionally be followed by `;skip_if=<N>` where N is a non-negative integer
> If skip_if is provided, the message delivery will be skipped if the last delivery is in the last N messages in the channel
> 
> for example: `repeat=daily;skip_if=5`
> 
> desc is an optional description of the message
> 
> <message> is optional.  If specified, it will replace the body of the current message
> 
> **Note:**  `last` may be used as <message-id> to reference your most recently scheduled message
> 
> `edit` may be used to edit templates.  When editing a template, the <time> and repeat options are not allowed"""

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
> Display your currently set time zone"""

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

    if command == "help":
        return """> `~giggle help <command>`
> 
> Show the help for <command>
> 
> `~giggle help`
> 
> Show the main help"""
    return f"> \"{command}\" is not a recognized command\n> \n> Available commands are `list`, `show`, `send`, `edit`, `cancel`, `timezone`, `timezones`, `help`"
