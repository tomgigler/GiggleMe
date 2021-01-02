#!/usr/bin/env python

confirmation_requests = {}

class ConfirmationRequest:
    def __init__(self, confirmation_message, member, func, params):
        self.confirmation_message = confirmation_message
        self.member = member
        self.func = func
        self.params = params

async def confirm_request(channel, member, prompt, timeout, func, params):
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

async def confirmation_process_reaction(reaction, user):
    found = False
    if reaction.message.id in confirmation_requests:
        if(user == confirmation_requests[reaction.message.id].member):
            found = True
            if reaction.emoji == '✅':
                confirmation_request = confirmation_requests.pop(reaction.message.id, None)
                await confirmation_request.func(confirmation_request.params)
            else:
                confirmation_message = confirmation_requests.pop(reaction.message.id, None)

    if found:
        try:
            await reaction.message.remove_reaction('✅', client.user)
            await reaction.message.remove_reaction('❌', client.user)
        except:
            pass

