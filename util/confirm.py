#!/usr/bin/env python
import discord
import asyncio

confirmation_requests = {}

class ConfirmationRequest:
    def __init__(self, confirmation_message, member, func, params):
        self.confirmation_message = confirmation_message
        self.member = member
        self.func = func
        self.params = params

async def confirm_request(channel, member, prompt, timeout, func, params, client):
    confirmation_message = await channel.send(embed=discord.Embed(description=f"{prompt}\n\n✅ Yes\n\n❌ No", color=0x0000ff))
    await confirmation_message.add_reaction('✅')
    await confirmation_message.add_reaction('❌')

    confirmation_requests[confirmation_message.id] = ConfirmationRequest(confirmation_message, member, func, params)

    await asyncio.sleep(int(timeout))

    try:
        await confirmation_message.remove_reaction('✅', client.user)
        await confirmation_message.remove_reaction('❌', client.user)
    except:
        pass

    confirmation_requests.pop(confirmation_message.id, None)

async def process_reaction(payload, client):
    found = False
    if payload.message_id in confirmation_requests:
        if(payload.user_id == confirmation_requests[payload.message_id].member.id):
            found = True
            if payload.emoji == '✅':
                confirmation_request = confirmation_requests.pop(payload.message_id, None)
                await confirmation_request.func(confirmation_request.params)
            else:
                confirmation_message = confirmation_requests.pop(payload.message_id, None)

    if found:
        try:
            guild = client.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = channel.get_message(payload.message_id)
            await message.remove_reaction('✅', client.user)
            await message.remove_reaction('❌', client.user)
        except:
            pass

