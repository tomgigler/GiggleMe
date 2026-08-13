#!/usr/bin/env python
import discord


class ConfirmationView(discord.ui.View):
    def __init__(self, member_id, prompt, seconds):
        super().__init__(timeout=seconds)
        self.member_id = member_id
        self.prompt = prompt
        self.response = None
        self.message = None

    def get_embed(self, status=None):
        description = self.prompt
        color = 0x0000ff

        if status == "confirmed":
            description += "\n\n✅ **Confirmed**"
            color = 0x00ff00
        elif status == "cancelled":
            description += "\n\n❌ **Cancelled**"
            color = 0xff0000
        elif status == "timed_out":
            description += "\n\n⌛ **Timed out**"
            color = 0x808080
        else:
            description += "\n\nChoose **Yes** or **No**."

        return discord.Embed(description=description, color=color)

    def disable_buttons(self):
        for child in self.children:
            child.disabled = True

    async def interaction_check(self, interaction):
        if interaction.user.id == self.member_id:
            return True

        await interaction.response.send_message(
            "This confirmation belongs to another user.",
            ephemeral=True
        )
        return False

    async def finish(self, interaction, response):
        self.response = response
        self.disable_buttons()

        status = "confirmed" if response else "cancelled"

        await interaction.response.edit_message(
            embed=self.get_embed(status),
            view=self
        )

        self.stop()

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def confirm_yes(self, interaction, button):
        await self.finish(interaction, True)

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def confirm_no(self, interaction, button):
        await self.finish(interaction, False)

    async def on_timeout(self):
        self.disable_buttons()

        if self.message is None:
            return

        try:
            await self.message.edit(
                embed=self.get_embed("timed_out"),
                view=self
            )
        except discord.HTTPException:
            # The prompt may have been deleted or become inaccessible.
            pass


async def confirm_request(channel, member_id, prompt, seconds, client):
    """Ask one user to confirm an operation with Discord buttons.

    The client parameter is intentionally retained for compatibility with
    GiggleMe's existing callers even though button confirmations do not need it.
    """
    view = ConfirmationView(member_id, prompt, seconds)

    confirmation_message = await channel.send(
        embed=view.get_embed(),
        view=view
    )
    view.message = confirmation_message

    await view.wait()

    return view.response
