import discord
client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "Hello":
        await message.channel.send('Hello yourself')

client.run("NzQ3ODM3NTM2Nzc2NDg2OTUz.X0Ur-g.lM2yGwnEFKVDBRd-yYp5wEypfBE")
