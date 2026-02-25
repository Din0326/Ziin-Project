import random

from bot.core.classed import Cog_Extension
from bot.utils.i18n import t_ctx
from discord import app_commands
from discord.ext import commands
from discord.utils import get


class Basic(Cog_Extension):

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["延遲", "延遲測試"],
        description="查看機器人延遲",
        help="顯示機器人目前與 Discord API 的延遲。\n用法：ping",
    )
    async def ping(self, ctx: commands.Context):
        await ctx.send(t_ctx(ctx, "ping", round(self.bot.latency * 1000)))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["說", "回聲"],
        description="讓機器人重送一段文字",
        help="機器人會刪除你的訊息後，將內容重新發送到目前頻道。\n用法：echo <文字內容>",
    )
    @app_commands.describe(msg="要讓機器人發送的內容")
    async def echo(self, ctx: commands.Context, *, msg: str):
        await ctx.message.delete()
        await ctx.channel.send(msg)

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["抽選", "隨機選擇"],
        description="從多個選項中隨機挑一個",
        help="輸入多個選項，機器人會隨機回覆其中一項。\n用法：pick 選項A 選項B 選項C",
    )
    @app_commands.describe(args="請用空白分隔多個選項")
    async def pick(self, ctx: commands.Context, *, args: str):
        answer = random.choice(args.split(" "))
        await ctx.send(answer)

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["進語音", "加入語音"],
        description="將機器人加入你的語音頻道",
        help="讓機器人加入你目前所在的語音頻道。\n用法：join",
    )
    async def join(self, ctx: commands.Context):
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            await channel.connect()
            print(f"The bot has connected to {channel}\\n")

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["離開語音", "退語音"],
        description="讓機器人離開語音頻道",
        help="讓機器人離開目前連線中的語音頻道。\n用法：leave",
    )
    async def leave(self, ctx: commands.Context):
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            print(f"The bot has left {channel}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Basic(bot))
