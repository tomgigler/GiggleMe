#!/usr/bin/env python
import discord


class ConfirmationView(discord.ui.View):
    def __init__(self, member_id, seconds):
        super().__init__(timeout=seconds)
        self.member_id = member_id
        self.response = None

    async def interaction_check(self, interaction):
        if interaction.user.id == self.member_id:
            return True

        await interaction.response.send_message(
            "This confirmation belongs to another user.",
            ephemeral=True
        )
        return False

    def disable_buttons(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(
        label="Yes",
        emoji="✅",
        style=discord.ButtonStyle.success
    )
    async def confirm_yes(self, interaction, button):
        self.response = True
        self.disable_buttons()
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(
        label="No",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def confirm_no(self, interaction, button):
        self.response = False
        self.disable_buttons()
        await interaction.response.edit_message(view=self)
        self.stop()


async def confirm_request(channel, member_id, prompt, seconds, client):
    view = ConfirmationView(member_id, seconds)

    confirmation_message = await channel.send(
        embed=discord.Embed(
            description=prompt,
            color=0x0000ff
        ),
        view=view
    )

    timed_out = await view.wait()

    if timed_out:
        view.disable_buttons()
        try:
            await confirmation_message.edit(view=view)
        except discord.HTTPException:
            pass

    return view.response
