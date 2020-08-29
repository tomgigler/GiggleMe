#!/usr/bin/env python
import discord
import re
import os
import asyncio
from settings import bot_token

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
}

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

async def process_vol_message(message):
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

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == 460410391290314752:
        await process_vol_message(message)
        
    if re.search(r'^~giggle.*[-]?[0-9]*\.?[0-9]+ ?[CFcf](?:\s+|$|\?|\.|,)', message.content):
        await process_temps(message)

    if client.user.mentioned_in(message):
        await message.channel.send(f"Hi!  I convert temperatures.  Just put ~giggle at the beginning of your message")

client.run(bot_token)
