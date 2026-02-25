from __future__ import annotations

from dataclasses import dataclass

import discord
from discord import app_commands
from bot.services.guild_settings import get_guild_settings
from discord.ext import commands


@dataclass(slots=True)
class HelpCategory:
    name: str
    commands: list[commands.Command]


class HelpCategorySelect(discord.ui.Select):
    def __init__(self, categories: list[HelpCategory], pages: dict[str, discord.Embed]):
        options = [
            discord.SelectOption(
                label=cat.name,
                value=cat.name,
                description=f"{len(cat.commands)} commands",
            )
            for cat in categories
        ]
        super().__init__(
            placeholder="選擇分類查看指令",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )
        self._pages = pages

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = self.values[0]
        embed = self._pages.get(selected)
        if embed is None:
            await interaction.response.defer()
            return
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, overview: discord.Embed, categories: list[HelpCategory], pages: dict[str, discord.Embed]):
        super().__init__(timeout=180)
        self.overview = overview
        self.add_item(HelpCategorySelect(categories, pages))

    @discord.ui.button(label="總覽", style=discord.ButtonStyle.secondary, row=1)
    async def back_overview(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.overview, view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _resolve_prefix(self, ctx: commands.Context) -> str:
        default_prefix = getattr(getattr(self.bot, "settings", None), "default_prefix", "z!")

        if ctx.guild is not None:
            try:
                data = get_guild_settings(ctx.guild.id)
                configured = data.get("Prefix")
                if isinstance(configured, str) and configured.strip():
                    return configured.strip()
            except Exception:
                pass

        if getattr(ctx, "clean_prefix", None):
            return ctx.clean_prefix

        prefix = default_prefix
        try:
            if ctx.message is not None:
                maybe_prefix = await self.bot.get_prefix(ctx.message)
                if isinstance(maybe_prefix, (list, tuple)):
                    prefix = maybe_prefix[0]
                else:
                    prefix = maybe_prefix
        except Exception:
            pass
        return prefix

    def _visible_commands(self) -> list[commands.Command]:
        result: list[commands.Command] = []
        for cmd in self.bot.commands:
            if cmd.hidden or cmd.parent is not None:
                continue
            if cmd.name in {"load", "unload", "reload", "shutdown"}:
                continue
            result.append(cmd)
        return sorted(result, key=lambda c: c.name)

    def _grouped_commands(self) -> list[HelpCategory]:
        grouped: dict[str, list[commands.Command]] = {}
        for cmd in self._visible_commands():
            group = cmd.cog_name or "Other"
            grouped.setdefault(group, []).append(cmd)

        categories = [
            HelpCategory(name=name, commands=sorted(cmds, key=lambda c: c.name))
            for name, cmds in grouped.items()
        ]
        return sorted(categories, key=lambda x: x.name)

    def _with_common_style(self, embed: discord.Embed) -> discord.Embed:
        embed.color = discord.Color.blurple()
        embed.set_footer(text="Ziin Help Center")
        return embed

    def _build_overview_embed(self, prefix: str, categories: list[HelpCategory]) -> discord.Embed:
        embed = self._with_common_style(
            discord.Embed(
                title="Ziin Help",
                description=(
                    "互動式指令說明面板\n"
                    f"前綴：`{prefix}`  |  Slash：`/help`\n"
                    "使用 `/help 指令名` 可直接查詢單一指令。"
                ),
            )
        )

        for cat in categories[:12]:
            names = " ".join(f"`{prefix}{c.name}`" for c in cat.commands[:8])
            if len(cat.commands) > 8:
                names += " ..."
            embed.add_field(name=f"{cat.name} ({len(cat.commands)})", value=names or "-", inline=False)

        return embed

    def _build_category_pages(self, prefix: str, categories: list[HelpCategory]) -> dict[str, discord.Embed]:
        pages: dict[str, discord.Embed] = {}
        for cat in categories:
            lines: list[str] = []
            for cmd in cat.commands:
                brief = cmd.brief or cmd.help or "無說明"
                one_line = brief.splitlines()[0].strip()
                lines.append(f"`{prefix}{cmd.name}` - {one_line}")

            embed = self._with_common_style(
                discord.Embed(
                    title=f"{cat.name} Commands",
                    description="\n".join(lines) if lines else "此分類目前沒有可見指令",
                )
            )
            pages[cat.name] = embed

        return pages

    def _build_command_detail(self, prefix: str, command: commands.Command) -> discord.Embed:
        usage = f"{prefix}{command.qualified_name}"
        if command.signature:
            usage = f"{usage} {command.signature}"

        embed = self._with_common_style(
            discord.Embed(
                title=f"指令：{command.qualified_name}",
                description=command.help or command.brief or "尚無說明",
            )
        )
        embed.add_field(name="使用方式", value=f"`{usage}`", inline=False)
        embed.add_field(name="Slash", value=f"`/{command.qualified_name}`", inline=True)
        aliases = ", ".join(f"`{a}`" for a in command.aliases) if command.aliases else "無"
        embed.add_field(name="別名", value=aliases, inline=True)
        category = command.cog_name or "Other"
        embed.add_field(name="分類", value=category, inline=True)
        return embed

    @commands.hybrid_command(
        name="help",
        with_app_command=True,
        description="顯示互動式指令說明"
    )
    @app_commands.describe(command_name="要查詢的指令名稱（可留空）")
    async def help(self, ctx: commands.Context, command_name: str | None = None):
        prefix = await self._resolve_prefix(ctx)

        if command_name:
            target = self.bot.get_command(command_name.lower())
            if target is None or target.hidden:
                await ctx.send(f"找不到指令：`{command_name}`")
                return
            await ctx.send(embed=self._build_command_detail(prefix, target))
            return

        categories = self._grouped_commands()
        overview = self._build_overview_embed(prefix, categories)
        pages = self._build_category_pages(prefix, categories)
        view = HelpView(overview, categories, pages)
        await ctx.send(embed=overview, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
