#!/usr/bin/env python
import discord
import re
import os
import asyncio
from settings import bot_token
import sys

client = discord.Client()

content_creators = {
    "https://yt3.ggpht.com/a/AATXAJxSQvMvlPBAQ3t22bpTJdB0zVLYT1CaDM4fuwaK=s88-c-k-c0xffffffff-no-rj-mo": "truth-wanted",
    "https://yt3.ggpht.com/a/AATXAJzS8yRqAyP1a1z8VQVEUt-t_jbz3dQwrSvXSHZEDg=s88-c-k-c0xffffffff-no-rj-mo": "axp",
    "https://yt3.ggpht.com/a/AATXAJyfVfb8I2lV2vywvLrakn84yhPHtSptswi37-BK=s88-c-k-c0xffffffff-no-rj-mo": "talk-heathen",
    "https://yt3.ggpht.com/a/AATXAJywmSV97VjI1O8MZ546gBsJYvviV4Y_A9QWVuuGrQ=s88-c-k-c0xffffffff-no-rj-mo": "cosmic-skeptic",
    "https://yt3.ggpht.com/a/AATXAJyNhlhB3AfZL1Fh6Xegc4TSfTPpdRl8gYCohcW3QQ=s88-c-k-c0xffffffff-no-rj-mo": "gm-skeptic",
    "https://yt3.ggpht.com/a/AATXAJwusshuBJWMrdF-RVLeZkHxxxjHIc8aBON3zmNU=s88-c-k-c0xffffffff-no-rj-mo": "viced-rhino",
    "https://yt3.ggpht.com/a/AATXAJz9DQ6bS7M7J7cz_ZxstDneqi_6FKMF3Asb_dHD=s88-c-k-c0xffffffff-no-rj-mo": "tommygig3",
    "https://yt3.ggpht.com/a/AATXAJyTYaBKgP7oK0LeZjX6M118KlP70VHfI_tr9dzp=s88-c-k-c0xffffffff-no-rj-mo": "suris",
    "https://yt3.ggpht.com/a/AATXAJyExzxgK7djYxgxnr2UIXZ8vE23BAq-d0IPRmzzTg=s900-c-k-c0xffffffff-no-rj-mo": "prophet-of-zod",
    "https://yt3.ggpht.com/a/AATXAJx8UL5vsMctl0t4JVFbv0I01jmzFY7Got2gwctiiA=s88-c-k-c0xffffffff-no-rj-mo":  "ocean",
    "https://yt3.ggpht.com/a/AATXAJxYLKl5krz-WivbaKL3_UzOwlT40GGcMXljWsD-Gg=s88-c-k-c0xffffffff-no-rj-mo": "holy-koolaid",
    "https://yt3.ggpht.com/a/AATXAJxrhbzJ8H1Xg4aAl2dZe-kA3ytVtkzZpi9udv1F=s88-c-k-c0xffffffff-no-rj-mo": "jimmy-snow",
    "https://yt3.ggpht.com/a/AATXAJy3orRgbrsu7rPXd4hd7pLrkLmpn_sf-3Acyak=s88-c-k-c0xffffffff-no-rj-mo": "paulogia",
    "https://yt3.ggpht.com/-M_Syakat5rE/AAAAAAAAAAI/AAAAAAAAAAA/OzT9FKHe8c8/s88-c-k-no-mo-rj-c0xffffff/photo.jpg": "logicked",
    "https://yt3.ggpht.com/a/AATXAJzrDsatrY320DB6LclM9Vm1-W2vNDP3efG7H2BN1g=s88-c-k-c0xffffffff-no-rj-mo": "isethoriginal",
    "https://yt3.ggpht.com/a/AATXAJwGqX1M1EgnnSYnmrhejjfQWtXXyGZ0topWRDrSwQ=s88-c-k-c0xffffffff-no-rj-mo": "simon-whistler",
    "https://yt3.ggpht.com/a/AATXAJwA14TaUzPDsmbs9EdRB7UmgF5qpVID4Es2xKfh=s88-c-k-c0xffffffff-no-rj-mo": "simon-whistler",
    "https://yt3.ggpht.com/a/AATXAJzwTTJIyfTRPSovEPrwLWZ_tAl4N7wO65AZNPamqQ=s88-c-k-c0xffffffff-no-rj-mo": "simon-whistler",
    "https://yt3.ggpht.com/a/AATXAJyyX7kXRSqr3GJ2YrXtPBa774tgj2f9TLC2VsPfA6o=s88-c-k-c0xffffffff-no-rj-mo": "unholy-sara",
    "https://yt3.ggpht.com/a/AATXAJyxnZHUlDp6jF3IkdCoDMcjvB8Ld8v5wsThng=s88-c-k-c0xffffffff-no-rj-mo": "aliaki",
    "https://yt3.ggpht.com/a/AATXAJwu9Wa4r4oUBLvG_KhmHX3A7LYPCfee9nJV4VLiSA=s88-c-k-c0xffffffff-no-rj-mo": "cel",
    "https://yt3.ggpht.com/a/AATXAJyp2-dCelQUHHSUpCYq1IRc_FF3Jkb8Zy2qsq4X=s88-c-k-c0xffffffff-no-rj-mo": "aliakai",
    "https://yt3.ggpht.com/a/AATXAJwcW643CDxynJALwTrXFbP8ot1jlfxvHtnMbWrE=s88-c-k-c0xffffffff-no-rj-mo": "celeris-garden",
    "https://yt3.ggpht.com/a/AATXAJzgoZheJtMTNcSBdc4pwViRJ6ktnnT9qRtOD3DIEw=s88-c-k-c0xffffffff-no-rj-mo": "oracle-oriax",
    "https://yt3.ggpht.com/a/AATXAJzywm6ambHpRNhnIbH30Vp6sTONXuAPp2Id2i4oEQ=s88-c-k-c0xffffffff-no-rj-mo": "darkmatter-2525",
}

def get_content_creator_names(guild):
    content_creator_names = []
    channels = []
    roles = []
    for channel in guild.channels:
        channels.append(channel.name)
    for role in guild.roles:
        roles.append(role.name)
    for link in content_creators:
        if content_creators[link] in channels and content_creators[link] in roles:
            if content_creators[link] not in content_creator_names:
                content_creator_names.append(content_creators[link])
    return content_creator_names

async def process_temps(message):
    processed_values = []
    for temp in re.findall('[-]?[0-9]*\.?[0-9]+ ?[CFcf](?:\s+|$|\?|\.|,)', message.content):
        match = re.search('([-]?[0-9]*\.?[0-9]+) ?([CFcf])(?:\s+|$|\?|\.|,)', temp)
        value = float(match.group(1))
        scale = match.group(2)
        if scale == 'c':
            scale = 'C'
        if scale == 'f':
            scale = 'F'
        newvalue = value * 1.8 + 32 if scale == 'C' else (value - 32)/1.8
        newscale = 'F' if scale == 'C' else 'C'
        if f"{value}{scale}" not in processed_values:
            await message.channel.send(f"{value} {scale} = {round(newvalue, 1)} {newscale}")
            processed_values.append(f"{value}{scale}")
            processed_values.append(f"{newvalue}{newscale}")

async def list_user_roles(message):
    youtube_roles = []
    server_roles = []
    user_roles = []
    for role in message.guild.roles:
        server_roles.append(role.name)
    for role in message.author.roles:
        user_roles.append(role.name)
    for link in content_creators:
        if content_creators[link] in server_roles and content_creators[link] in user_roles:
            if content_creators[link] not in youtube_roles:
                youtube_roles.append(content_creators[link])
    if len(youtube_roles) > 0:
        await message.channel.send('\n'.join(youtube_roles))

async def add_user_role(message):
    add_role = re.search('~giggle youtube add (.*)', message.content, re.IGNORECASE).group(1)
    content_creator_names = get_content_creator_names(message.guild)
    if add_role not in content_creator_names:
        await message.channel.send(f"Cannot add {add_role} role")
        return
    if discord.utils.get(message.author.roles, name=add_role):
        await message.channel.send(f"You already have the {add_role} role")
        return
    else:
        role = discord.utils.get(message.guild.roles, name=add_role)
        await message.author.add_roles(role)
    if discord.utils.get(message.author.roles, name=add_role):
        await message.channel.send(f"Added {add_role} role")
    else:
        await message.channel.send(f"Failed to add {add_role} role")

async def remove_user_role(message):
    remove_role = re.search('~giggle youtube remove (.*)', message.content, re.IGNORECASE).group(1)
    content_creator_names = get_content_creator_names(message.guild)
    if remove_role not in content_creator_names:
        await message.channel.send(f"Cannot remove {remove_role} role")
        return
    if not discord.utils.get(message.author.roles, name=remove_role):
        await message.channel.send(f"You don't currently have the {remove_role} role")
        return
    else:
        role = discord.utils.get(message.guild.roles, name=remove_role)
        await message.author.remove_roles(role)
    if not discord.utils.get(message.author.roles, name=remove_role):
        await message.channel.send(f"Removed {remove_role} role")
    else:
        await message.channel.send(f"Failed to remove {remove_role} role")

async def list_roles(message):
    youtube_roles = []
    channels = []
    roles = []
    for channel in message.guild.channels:
        channels.append(channel.name)
    for role in message.guild.roles:
        roles.append(role.name)
    for link in content_creators:
        if content_creators[link] in channels and content_creators[link] in roles:
            if content_creators[link] not in youtube_roles:
                youtube_roles.append(content_creators[link])
    if len(youtube_roles) > 0:
        await message.channel.send('\n'.join(youtube_roles))

async def process_vol_message(message):
    try:
        if re.search(r'Successfully subscribed to (.*)', message.embeds[0].title):
            channel_name = re.search(r'Successfully subscribed to (.*)', message.embeds[0].title).group(1)
            creator_role_found = False
            creator_channel_found = False
            for link in content_creators:
                if link == message.embeds[0].thumbnail.url:
                    for role in message.guild.roles:
                        if role.name == content_creators[link]:
                            creator_role_found = True
                    for channel in message.guild.channels:
                        if channel.name == content_creators[link]:
                            creator_channel_found = True
                    if not creator_channel_found:
                        youtube_category = None
                        for category in message.guild.categories:
                            if category.name == 'YouTube':
                                youtube_category = category
                        if not youtube_category:
                            youtube_category = await message.guild.create_category('YouTube')
                        await message.guild.create_text_channel(name=content_creators[link], category=youtube_category)
                        await message.channel.send(f"I've created the {content_creators[link]} channel")
                    if not creator_role_found:
                        await message.guild.create_role(name=content_creators[link])
                        await message.channel.send(f"I've created the {content_creators[link]} role")
                    await message.channel.send(f"New {channel_name} videos will be posted to the {content_creators[link]} channel and ping the {content_creators[link]} role")
                    return
            await message.channel.send(f"I don't know how to handle {channel_name}'s content.  Please contact my creator to get {channel_name} added to my functionality")
    except:
        pass

    for channel in message.guild.text_channels:
        if channel.name == 'voice-of-light-posts':
            vol_posts_channel = channel

    try:
        if(message.embeds[0].title == 'Youtube subscriptions'):
            return
    except:
        pass

    if vol_posts_channel == message.channel:
        channel_role_name = None
        creator_channel = None
        creator_role = None
        try:
            for link in content_creators:
                if link == message.embeds[0].footer.icon_url:
                    channel_role_name = content_creators[link]
            if channel_role_name:
                for channel in message.guild.text_channels:
                    if channel.name == channel_role_name:
                        creator_channel = channel
                for role in message.guild.roles:
                    if role.name == channel_role_name:
                        creator_role = role

            if not channel_role_name:
                await vol_posts_channel.send(f"Creator not found {message.embeds[0].footer.icon_url}")
                return

            if creator_channel:
                if creator_role:
                    await creator_channel.send(creator_role.mention)
                else:
                    await vol_posts_channel.send(f"Cannot ping role for {message.embeds[0].footer.icon_url}")
                for embed in message.embeds:
                    await creator_channel.send(embed=embed)
            else:
                await vol_posts_channel.send(f"Cannot post to channel for {message.embeds[0].footer.icon_url}")
        except:
            pass

async def process_delay_message(message):
    try:
        server_id = int(re.search(r'server=(\d+)', message.content).group(1))
    except:
        server_id = message.guild.id

    guild = discord.utils.get(client.guilds, id=server_id)
    channel_name = re.search(r'channel=(.+)', message.content).group(1)
    channel = discord.utils.get(guild.channels, name=channel_name)

    try:
        is_admin = message.author.permissions_in(channel).administrator
    except:
        await message.channel.send('Admin permission are required to send delayed messages')
        return
    if is_admin:
        match = re.search(r'^~giggle delay (\d+)[^\n]*[\n](.*)', message.content, re.MULTILINE|re.DOTALL)
        delay = match.group(1)
        msg = match.group(2)
        msg = f"Here's a message from {message.author.mention}:\n" + msg
        await message.channel.send(f"Your message will be delivered to the {channel.name} channel in the {guild.name} server in {delay} minutes")
        await asyncio.sleep(int(delay)*60)
        await channel.send(msg)
    else:
        await message.channel.send('Admin permission are required to send delayed messages')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == 'kill' and message.author.id == 669370838478225448:
        await message.channel.send(f"Killing {client.user.name}")
        sys.exit()

    if re.search(r'^~giggle delay \d+', message.content):
        await process_delay_message(message)
        return

    if message.author.id == 460410391290314752:
        await process_vol_message(message)

    if re.search(r'^~giggle youtube$', message.content, re.IGNORECASE):
        await message.channel.send("""Start your message with "~giggle youtube" followed by one of the commands below:
            roles:
                Show youtube roles currently assigned to you
            add <role>:
                Assign <role> to yourself
            remove <role>:
                Remove <role> from yourself
            list:
                Show available youtube roles on this server""")

    elif re.search(r'^~giggle youtube roles$', message.content, re.IGNORECASE):
        await list_user_roles(message)

    elif re.search(r'^~giggle youtube add \S', message.content, re.IGNORECASE):
        await add_user_role(message)

    elif re.search(r'^~giggle youtube remove \S', message.content, re.IGNORECASE):
        await remove_user_role(message)

    elif re.search(r'^~giggle youtube list$', message.content, re.IGNORECASE):
        await list_roles(message)

    elif re.search(r'^~giggle.*[-]?[0-9]*\.?[0-9]+ ?[CFcf](?:\s+|$|\?|\.|,)', message.content, re.IGNORECASE):
        await process_temps(message)

    if client.user.mentioned_in(message):
        await message.channel.send(f"Hi {message.author.name}!  I convert temperatures.  Just put \"~giggle\" at the beginning of your message")
        vol_posts_channel = None
        for channel in message.guild.text_channels:
            if channel.name == 'voice-of-light-posts':
                vol_posts_channel = channel
        if vol_posts_channel:
            await message.channel.send(f"I also do YouTube announcements on this server.  Type \"~giggle youtube\" for details")


client.run(bot_token)
