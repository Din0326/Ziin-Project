import os
import time
from datetime import datetime, timedelta
from platform import python_version
from typing import Optional

import discord
from bot.core.classed import Cog_Extension
from bot.services.user_stats import (get_user_guild_stats,
                                     get_user_voice_channel_stats)
from bot.utils.guild_context import get_ctx_lang_tz, get_guild_context
from bot.utils.timezone import format_local_time
from discord import Activity, ActivityType, Embed, Member, Role
from discord import __version__ as discord_version
from discord.ext import commands
from psutil import Process, virtual_memory


class Meta(Cog_Extension):
	@property
	def message(self):
		return self._message.format(users=len(self.bot.users), guilds=len(self.bot.guilds))

		@message.setter
		def message(self, value):
			if value.split(" ")[0] not in ("playing", "watching", "listening", "streaming", "competing"):
				raise ValueError("無效的活動類型。")

		self._message = value

	async def set(self):
		_type, _name = self.message.split(" ", maxsplit=1)

		await self.bot.change_presence(activity=Activity(
			name=_name, type=getattr(ActivityType, _type, ActivityType.playing)
		))

	@commands.hybrid_command(aliases=["設定狀態","play3"], hidden=True, with_app_command=True)
	async def setactivity(self, ctx: commands.Context, *, text: str):
		user = self.bot.get_user(371871742916034561)
		self.message = f"{text}"
		if ctx.author == user:
			await self.set()
		else:
			await ctx.send("你沒有權限使用這個指令。")

	@commands.hybrid_command(
		aliases=["vt", "語音紀錄", "語音追蹤"],
		with_app_command=True,
		description="查看成員語音進出紀錄",
		help="查看指定成員在各語音頻道的加入、離開與停留時間。\n用法：voicetrack [成員]"
	)
	async def voicetrack(self, ctx: commands.Context, target: Optional[Member]):
		load_Msg = await ctx.send("讀取資料中... <a:load:854870818982723604> ")
		await ctx.trigger_typing()
		target = target or ctx.author
		dt_format = "%d-%m-%Y %H:%M:%S"
		user_img = ctx.author.avatar or ctx.author.default_avatar
		#time = time.strftime(dt_format)
		embed = discord.Embed(title=f"{target.name} 的語音紀錄",
							  colour=ctx.author.colour,
							  timestamp=datetime.utcnow())
		#embed.set_author(name=f"{target.name}'s Voicetrack", icon_url=target.avatar.url)
		embed.set_thumbnail(url=target.avatar.url)
		embed.set_footer(icon_url=(user_img.url),text=f'{ctx.author}')
		for x in range(len(ctx.guild.voice_channels)):
			doce = get_user_voice_channel_stats(target.id, ctx.guild.id, ctx.guild.voice_channels[x].id)
			if doce != None:
				time_join = doce.get('Join')
				time_leave = doce.get('Leave')
				if time_leave == None:
					time_leave = time_total = "無"
				else:
					if datetime.strptime(time_leave,dt_format) < datetime.strptime(time_join,dt_format):
						time_total = "時間資料異常"
					else:
						time_total = datetime.strptime(time_leave,dt_format) - datetime.strptime(time_join,dt_format)
					ch_name = self.bot.get_channel(ctx.guild.voice_channels[x].id).name
			fields=[(ctx.guild.voice_channels[x].name,f"加入：{time_join}\n離開：{time_leave}\n總時長：{time_total}",False)]
			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)
		await ctx.send(embed=embed)
		await load_Msg.delete()
	@commands.hybrid_command(
		aliases=["lb", "top", "排行", "排行榜"],
		with_app_command=True,
		description="查看伺服器貢獻排行榜",
		help="顯示伺服器成員貢獻度前十名。\n用法：leaderboard"
	)
	async def leaderboard(self, ctx: commands.Context):
		total = []
		data_list = []
		leaderboard = {}
		load_msg = await ctx.send("<a:load:854870818982723604> 查詢中... <a:load:854870818982723604>")
		for user in ctx.guild.members:
			if user.bot:
				continue
			info_data = get_user_guild_stats(user.id, ctx.guild.id)
			contribution = info_data.get('total') or 0
			if contribution == 0:
				continue
			leaderboard[user.id] = contribution
			total.append(contribution)
		total = sorted(total, reverse=True)
		lb_list = {k: v for k, v in sorted(leaderboard.items(), key=lambda item: item[1],reverse=True)}
		embed_title = f"{ctx.guild.name} 貢獻排行榜"
		embed_description = "**前 1 ~ 10 名**"
		embed = discord.Embed(title=embed_title,
						   description=embed_description,
						   color=ctx.author.colour)
		embed.set_thumbnail(url=ctx.guild.icon.url)
		num = 1
		if num <= 10:
			for i in lb_list:
				usr = self.bot.get_user(int(i))
				if usr == None:
					continue
				embed.add_field(name=f"{num}.", value=f"{usr.mention}\n**{lb_list[i]}** 分", inline=True)
				if num == 1:
					embed.add_field(name="\u200b",value="\u200b",inline=True)
					embed.add_field(name="\u200b",value="\u200b",inline=True)
				if num == 10:
					break
				num += 1
		await load_msg.delete()
		await ctx.send(embed=embed)

	@commands.hybrid_command(
		aliases=["botinfo", "bi", "機器人資訊"],
		with_app_command=True,
		description="查看機器人狀態資訊",
		help="顯示機器人版本、運行天數、伺服器數量與使用者數量。\n用法：stats"
	)
	async def stats(self, ctx: commands.Context):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		embed = Embed(title=Lang["bot_title"],
					  description=Lang["bot_dev"],
					  colour=ctx.author.colour,
					  timestamp=datetime.utcnow())
		embed.set_thumbnail(url=self.bot.user.avatar.url)
		proc = Process()
		with proc.oneshot():
			uptime = timedelta(seconds=time.time()-proc.create_time())
			cpu_time = timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user)
			mem_total = virtual_memory().total / (1024**2)
			mem_of_total = proc.memory_percent()
			mem_usage = mem_total * (mem_of_total / 100)

		fields = [
			(Lang["bot_owner"],"<@371871742916034561>",False),
			(Lang["bot_version"], self.bot.VERSION, True),
			(Lang["bot_py-version"], python_version(), True),
			(Lang["bot_d.py-version"], discord_version, True),
			(Lang["bot_online-time"],f"{uptime.days} 天", True),
			#(Lang["bot_Ram"], f"{mem_usage:,.1f} / {mem_total:,.0f} MiB ({mem_of_total:.0f}%)", True),
			(Lang["bot_Guilds"], f"{len(self.bot.guilds)}", True),
			(Lang["bot_Users"], f"{len(self.bot.users)}", True)
		]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		#print(uptime)
		await ctx.send(embed=embed)


	@commands.hybrid_command(
		aliases=["memberinfo", "ui", "mi", "用戶資訊", "成員資訊"],
		with_app_command=True,
		description="查看成員詳細資訊",
		help="顯示指定成員的狀態、身分組、加入時間與貢獻資訊。\n用法：userinfo [成員]"
	)
	async def userinfo(self, ctx: commands.Context, target: Optional[Member]):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		target = target or ctx.author
		target_avatar = target.guild_avatar if target.guild_avatar else target.display_avatar or target.default_avatar
		info_data = get_user_guild_stats(target.id, ctx.guild.id)
		contribution = info_data.get('total') or 0
		last_message_time = info_data.get('last_message') or "無資料"
		embed = Embed(title=Lang["ui_title"].format(str(target)),
					  colour=target.colour,
					  timestamp=datetime.utcnow())
		embed.set_thumbnail(url=target_avatar.url)
		fields = [(Lang["ui_Mention"],target.mention,True),
				  (Lang["ui_ID"], target.id, True),
				  (Lang["ui_Nick"], target.nick, True),
				  (Lang["ui_Top-Role"], target.top_role.mention, True),
				  (Lang["ui_Status"], str(target.status).title(), True),
				  (Lang["ui_Activity"], f"-{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'}- {target.activity.name if target.activity else ''}", True),
				  (Lang["ui_Bot"], target.bot, True),
				  (Lang["ui_Boost"], bool(target.premium_since), True),
				  (Lang["ui_contribution"],contribution,True),
				  (Lang["ui_created_at"], format_local_time(target.created_at, guild_tz, "%d/%m/%Y\n%H:%M:%S"), True),
				  (Lang["ui_joined_at"], format_local_time(target.joined_at, guild_tz, "%d/%m/%Y\n%H:%M:%S"), True),
				  (Lang["ui_last_msg"],last_message_time.replace(" ","\n"),True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)

	@commands.hybrid_command(
		aliases=["avatar", "頭像"],
		with_app_command=True,
		description="查看成員頭像",
		help="顯示指定成員的伺服器頭像或個人頭像。\n用法：useravatar <成員>"
	)
	async def useravatar(self, ctx: commands.Context, target: discord.Member):
		target = target or ctx.author
		target_avatar = target.guild_avatar if target.guild_avatar else target.display_avatar or target.default_avatar
		embed = Embed(title=f"{target} 的頭像",
					  colour=target.colour,
					  timestamp=datetime.utcnow())

		embed.set_image(url=target_avatar.url)
		await ctx.send(embed=embed)

	@commands.hybrid_command(
		aliases=["Spotify", "SPOTIFY", "音樂", "正在聽什麼"],
		with_app_command=True,
		description="查看成員目前 Spotify 播放內容",
		help="顯示指定成員目前 Spotify 的歌曲、歌手與專輯資訊。\n用法：spotify [成員]"
	)
	async def spotify(self, ctx: commands.Context, user: discord.Member = None):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		user = user or ctx.author  
		spot = next((activity for activity in user.activities if isinstance(activity, discord.Spotify)), None)
		if spot is None:
			await ctx.send(Lang["spotify_none"])
			return
		song = str(spot.duration).split(".")[0]
		embed = discord.Embed(title=Lang["spotify_title"].format(user.name), color=spot.color)
		embed.add_field(name=Lang["spotify_song"], value=spot.title,inline=False)
		embed.add_field(name=Lang["spotify_artist"], value=spot.artist)
		embed.add_field(name=Lang["spotify_album"], value=spot.album)
		embed.add_field(name=Lang["spotify_tracklink"], value=f"[{spot.title}](https://open.spotify.com/track/{spot.track_id})",inline=False)
		embed.add_field(name=Lang["spotify_time"], value=song)
		embed.set_thumbnail(url=spot.album_cover_url)
		await ctx.send(embed=embed)
	@commands.hybrid_command(
			with_app_command=True,
			aliases=["查ID", "查使用者"],
			description="透過使用者 ID 查詢 Discord 帳號",
			help="輸入 Discord 使用者 ID，查詢帳號基本資訊。\n用法：who <使用者ID>"
	)
	async def who(self, ctx: commands.Context, find: int):
		try:
			target = await self.bot.fetch_user(find)
		except:
			await ctx.reply("找不到這個 ID 對應的使用者。")
			return

		embed = Embed(title="使用者查詢",
					  colour=ctx.author.colour,
					  timestamp=datetime.utcnow())
		target_avatar = target.avatar.url if target.avatar else target.default_avatar.url
		if target_avatar:
			embed.set_thumbnail(url=target_avatar)

		fields = [("名稱", f"**{target}**", True),
				  ("ID", target.id, True),
				  ("機器人帳號", target.bot, True),
				  ("頭像", f'[頭像連結]({target_avatar})' if target_avatar else '無', True),
				  ("狀態", str(target.status).title(), True),
				  ("活動", f"{str(target.activity.type).split('.')[-1].title() if target.activity else '無'} {target.activity.name if target.activity else ''}", True),
				  ("建立時間", target.created_at.strftime("%d/%m/%Y %H:%M:%S"), True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)
	@commands.hybrid_command(
		aliases=["ri", "身分組資訊", "職位資訊"],
		with_app_command=True,
		description="查看身分組資訊",
		help="顯示指定身分組的名稱、ID、顏色、排序與成員數。\n用法：roleinfo [身分組]"
	)
	async def roleinfo(self, ctx: commands.Context, target: Optional[Role]):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		target = target or ctx.author.top_role
		embed = Embed(title=Lang["ri_title"],
					  colour=target.colour,
					  timestamp=datetime.utcnow())

		embed.set_thumbnail(url=ctx.guild.icon.url)


		fields = [(Lang["ri_Name"], target.name, True),
				  (Lang["ri_ID"], target.id, True),
				  (Lang["ri_mention"], target.mention, True),
				  (Lang["ri_mentionable"], target.mentionable, True),
				  (Lang["ri_created_at"], format_local_time(target.created_at, guild_tz, "%Y-%m-%d %H:%M:%S"), True),
				  (Lang["ri_colour"], target.colour, True),
				  (Lang["ri_position"],target.position,True),
				  (Lang["ri_Members-count"], len(target.members), True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)

	@commands.hybrid_command(pass_context=True,hidden=True, with_app_command=True)
	async def getuser(self, ctx: commands.Context, target: Optional[Role]):
		role = target
		if role is None:
			await ctx.send("請提供一個身分組。")
			return
		empty = True
		for member in ctx.message.guild.members:
			if role in member.roles:
				await ctx.send("{0.mention} {0.name}: {0.id}".format(member))
				empty = False
		if empty:
			await ctx.send("目前沒有人擁有 {}".format(role.mention))
		
	@commands.hybrid_command(
		aliases=["guildinfo", "si", "gi", "伺服器資訊"],
		with_app_command=True,
		description="查看伺服器詳細資訊",
		help="顯示伺服器擁有者、成員數、頻道數、身分組數與邀請資訊。\n用法：serverinfo"
	)
	async def serverinfo(self, ctx: commands.Context):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		data = get_guild_context(ctx.guild.id).settings
		prefix = data.get('Prefix')
		embed = Embed(title=Lang["gi_title"].format(ctx.guild.name) + "  /  " + Lang["gi_prefix"] + f"=>    **{prefix}**",
					  colour=ctx.guild.owner.colour,
					  timestamp=datetime.utcnow())

		embed.set_thumbnail(url=ctx.guild.icon.url)
		statuses = [len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members)))]
		fields = [(Lang["gi_Owner"], ctx.guild.owner.mention, True),
				  (Lang["gi_ID"], f"`{ctx.guild.id}`", True),
				  (Lang["gi_region"], str(getattr(ctx.guild, "preferred_locale", "N/A")), True),
				  (Lang["gi_Member-count"], len(ctx.guild.members), True),
				  #(Lang["gi_Got-BAN"], len(await ctx.guild.bans()), True),
				  (Lang["gi_created_at"], format_local_time(ctx.guild.created_at, guild_tz, "%d/%m/%Y %H:%M:%S"), True),
				  (Lang["gi_Human"], len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
				  (Lang["gi_Bot"], len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
				  (Lang["gi_statuses"], f"🟢 {statuses[0]}  🌙 {statuses[1]}  ⛔ {statuses[2]}  ⚫ {statuses[3]}", True),
				  (Lang["gi_channels"], Lang["gi_channels_all"].format(len(ctx.guild.categories),len(ctx.guild.text_channels),len(ctx.guild.voice_channels),len(ctx.guild.stage_channels)), True),
				  (Lang["gi_Text_channels"], len(ctx.guild.text_channels), True),
				  (Lang["gi_voice_channels"], len(ctx.guild.voice_channels), True),
				  (Lang["gi_Categories"], len(ctx.guild.categories), True),
				  (Lang["gi_Roles"], len(ctx.guild.roles), True),
				  (Lang["gi_Invites"], len(await ctx.guild.invites()), True),
				  ("\u200b","\u200b",True)]
		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)

	@commands.hybrid_command(
		aliases=["about", "support"],
			with_app_command=True,
			description="查看 Ziin 介紹與支援連結",
			help="顯示 Ziin 介紹、網頁設定網址與支援伺服器連結。\n用法：aboutziin"
	)
	async def aboutziin(self, ctx: commands.Context):
		base_url = (os.getenv("WEB_DASHBOARD_URL") or os.getenv("NEXTAUTH_URL") or "http://localhost:6001").rstrip("/")
		dashboard_url = base_url if base_url.endswith("/dashboard") else f"{base_url}/dashboard"
		support_url = "https://discord.gg/EtQX9RB9Xr"

		embed = discord.Embed(
				title="Ziin Bot 介紹",
				description=(
					"Ziin 是專為 Discord 打造的紀錄與通知機器人。\n"
					"如果你有問題，歡迎加入支援伺服器。"
				),
			colour=ctx.author.colour,
			timestamp=datetime.utcnow(),
		)
		embed.add_field(name="網頁設定", value=dashboard_url, inline=False)
		embed.add_field(name="支援伺服器", value=support_url, inline=False)

		view = discord.ui.View()
		view.add_item(discord.ui.Button(label="開啟網頁設定", url=dashboard_url))
		view.add_item(discord.ui.Button(label="加入支援伺服器", url=support_url))
		await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meta(bot))
