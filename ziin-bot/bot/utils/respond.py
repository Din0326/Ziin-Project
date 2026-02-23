from __future__ import annotations

from typing import Any

import discord
from discord.ext import commands


async def respond(
    target: commands.Context | discord.Interaction,
    content: str | None = None,
    *,
    embed: discord.Embed | None = None,
    embeds: list[discord.Embed] | None = None,
    ephemeral: bool = False,
    delete_after: float | None = None,
    **kwargs: Any,
):
    """Send a message to either a prefix ctx or an interaction safely.

    - For prefix ctx: uses ctx.reply (falls back to ctx.send)
    - For interactions: uses response.send_message unless already responded, then followup.send
    """
    if isinstance(target, commands.Context):
        # Hybrid commands have ctx.interaction when invoked via /command
        inter = getattr(target, "interaction", None)
        if isinstance(inter, discord.Interaction):
            return await respond(
                inter,
                content,
                embed=embed,
                embeds=embeds,
                ephemeral=ephemeral,
                delete_after=delete_after,
                **kwargs,
            )

        try:
            return await target.reply(
                content=content,
                embed=embed,
                embeds=embeds,
                mention_author=False,
                delete_after=delete_after,
                **kwargs,
            )
        except Exception:
            return await target.send(
                content=content,
                embed=embed,
                embeds=embeds,
                delete_after=delete_after,
                **kwargs,
            )

    # Interaction path
    if target.response.is_done():
        return await target.followup.send(
            content=content,
            embed=embed,
            embeds=embeds,
            ephemeral=ephemeral,
            delete_after=delete_after,
            **kwargs,
        )
    return await target.response.send_message(
        content=content,
        embed=embed,
        embeds=embeds,
        ephemeral=ephemeral,
        delete_after=delete_after,
        **kwargs,
    )
