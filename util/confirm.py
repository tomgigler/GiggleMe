#!/usr/bin/env python
import discord
import asyncio

confirmation_requests = {}

class ConfirmationRequest:
    def __init__(self, member_id):
        self.member_id = member_id
        self.response = None

async def confirm_request(channel, member_id, prompt, seconds, client):
    confirmation_message = await channel.send(embed=discord.Embed(description=f"{prompt}\n\n✅ Yes\n\n❌ No", color=0x0000ff))
    await confirmation_message.add_reaction('✅')
    await confirmation_message.add_reaction('❌')

    confirmation_requests[confirmation_message.id] = ConfirmationRequest(member_id)

    for i in range(seconds):
        await asyncio.sleep(1)
        if confirmation_requests[confirmation_message.id].response is not None:
            break

    confirmation_request = confirmation_requests.pop(confirmation_message.id)

    try:
        await confirmation_message.remove_reaction('✅', client.user)
        await confirmation_message.remove_reaction('❌', client.user)
    except:
        pass

    return confirmation_request.response

def process_reaction(payload):
    if payload.message_id in confirmation_requests and payload.user_id == confirmation_requests[payload.message_id].member_id:
            if payload.emoji.name == '✅':
                confirmation_requests[payload.message_id].response = True
            else:
                confirmation_requests[payload.message_id].response = False
