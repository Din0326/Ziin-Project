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
			raise ValueError("Invalid activity type.")

		self._message = value

	async def set(self):
		_type, _name = self.message.split(" ", maxsplit=1)

		await self.bot.change_presence(activity=Activity(
			name=_name, type=getattr(ActivityType, _type, ActivityType.playing)
		))

	@commands.hybrid_command(aliases=["?湔??","play3"],hidden=True, with_app_command=True)
	async def setactivity(self, ctx: commands.Context, *, text: str):
		user = self.bot.get_user(371871742916034561)
		self.message = f"{text}"
		if ctx.author == user:
			await self.set()
		else:
			await ctx.send("雿?甈???璈")

	@commands.hybrid_command(aliases=["vt"], with_app_command=True)
	async def voicetrack(self, ctx: commands.Context, target: Optional[Member]):
		load_Msg = await ctx.send("loading data... <a:load:854870818982723604> ")
		await ctx.trigger_typing()
		target = target or ctx.author
		dt_format = "%d-%m-%Y %H:%M:%S"
		user_img = ctx.author.avatar or ctx.author.default_avatar
		#time = time.strftime(dt_format)
		embed = discord.Embed(title=f"{target.name}'s Voicetrack",
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
					time_leave = time_total = "N/A"
				else:
					if datetime.strptime(time_leave,dt_format) < datetime.strptime(time_join,dt_format):
						time_total = "Invalid time data"
					else:
						time_total = datetime.strptime(time_leave,dt_format) - datetime.strptime(time_join,dt_format)
					ch_name = self.bot.get_channel(ctx.guild.voice_channels[x].id).name
			fields=[(ctx.guild.voice_channels[x].name,f"Join: {time_join}\nLeave: {time_leave}\nTotal: {time_total}",False)]
			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)
		await ctx.send(embed=embed)
		await load_Msg.delete()
	@commands.hybrid_command(aliases=["lb","top"], with_app_command=True)
	async def leaderboard(self, ctx: commands.Context):
		total = []
		data_list = []
		leaderboard = {}
		load_msg = await ctx.send("<a:load:854870818982723604> searching... <a:load:854870818982723604>")
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
		embed_title = ctx.guild.name + " 鞎Ｙ摨行?銵?"
		embed_description = f"**1 ~ 10 ??*"
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
				embed.add_field(name=f"{num}.", value=f"{usr.mention}\n**{lb_list[i]}** 撠?", inline=True)
				if num == 1:
					embed.add_field(name="\u200b",value="\u200b",inline=True)
					embed.add_field(name="\u200b",value="\u200b",inline=True)
				if num == 10:
					break
				num += 1
		await load_msg.delete()
		await ctx.send(embed=embed)

	@commands.hybrid_command(aliases=["link","??","pingulink"], with_app_command=True)
	async def botlink(self, ctx: commands.Context):
		user = self.bot.get_user(371871742916034561)
		user_img =user.avatar or user.default_avatar
		embed = discord.Embed(title=f"{self.bot.user.name} ?隢?蝯?暺?!", url="https://discord.com/api/oauth2/authorize?client_id=616799674396967003&permissions=8&scope=bot")
		embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
		embed.set_thumbnail(url=self.bot.user.avatar.url)
		embed.set_footer(icon_url=(user_img.url),text=f'{user}')
		fields = [("Owner??????身?韌", "**Din#0203?????z!**\n\n?隢ot?閬?蝞∠??⊥????雿輻Log?  \n?隢?隢??仿 z!help 隤芣??稞n???唬遙雿?憿??臬遣霅堆?隢脣 [Support Server](https://discord.gg/EtQX9RB9Xr)", True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)
		await ctx.send(embed=embed)

	# @commands.hybrid_command(with_app_command=True)
	# async def help(self, ctx: commands.Context, title: typing.Optional[str] = None):
	# 	title = title or None
	# 	Lang , guild_tz = get_ctx_lang_tz(ctx)
	# 	data = get_guild_context(ctx.guild.id).settings
	# 	prefix = data.get('Prefix')
	# 	help_list = ['basic','guild','admin','log']
	# 	if title == None or title.lower() not in help_list:
	# 		embed = Embed(title=Lang["help_title"],
	# 				description=Lang["help_description"].format(prefix),
	# 				colour=ctx.author.colour,
	# 				timestamp=datetime.utcnow())
	# 		embed.add_field(name=Lang["help_basic"], value="`{0}link`,`{0}ui`,`{0}avatar`,`{0}spotify`,`{0}ri`,`{0}gi`,`{0}stats`,`{0}ping`,`{0}voicetrack`".format(prefix), inline=False)
	# 		embed.add_field(name=Lang["help_guild"], value="`{0}timezone`,`{0}language`,`{0}prefix`".format(prefix), inline=False)
	# 		embed.add_field(name=Lang["help_admin"], value="`{0}nick`,`{0}mute`,`{0}unmute`,`{0}ban`,`{0}unban`,`{0}clear`".format(prefix), inline=False)
	# 		embed.add_field(name=Lang["help_log"], value="`{0}setting`,`{0}ingore`,`{0}show`,`{0}setlog`".format(prefix), inline=False)
	# 		await ctx.send(embed=embed,delete_after=120)
	# 	else:
	# 		if title.lower() == "basic":
	# 			embed = Embed(title=Lang["help_title"],
	# 					colour=ctx.author.colour,
	# 					timestamp=datetime.utcnow())
	# 			embed.add_field(name=Lang['help_ui'], value="`{0}ui @user`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_ri'], value="`{0}ri @role`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_gi'], value="`{0}gi`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_avatar'], value="`{0}avatar @user`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_spotify'], value="`{0}spotify @user`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_stats'], value="`{0}stats`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_voicetrack'], value="`{0}voicetrack @user`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_ping'], value="`{0}ping`".format(prefix), inline=True)
	# 			embed.add_field(name=Lang['help_link'], value=Lang['help_link_value'].format(prefix), inline=True)
	# 			await ctx.send(embed=embed,delete_after=120)
	# 		elif title.lower() == "guild":
	# 			embed = Embed(title=Lang["help_title"],
	# 					colour=ctx.author.colour,
	# 					timestamp=datetime.utcnow())
	# 			embed.add_field(name=Lang["help_timezone"], value=Lang["help_timezone_value"].format(prefix), inline=False)
	# 			embed.add_field(name=Lang["help_language"], value=Lang["help_language_value"].format(prefix), inline=False)
	# 			embed.add_field(name=Lang["help_prefix"], value=Lang["help_prefix_value"].format(prefix), inline=False)
	# 			await ctx.send(embed=embed,delete_after=120)
	# 		elif title.lower() == "admin":
	# 			embed = Embed(title=Lang["help_title"],
	# 					colour=ctx.author.colour,
	# 					timestamp=datetime.utcnow())
	# 			embed.add_field(name="Mute User", value="`{0}mute @user`".format(prefix), inline=True)
	# 			embed.add_field(name="unmute User", value="`{0}unmute @user`".format(prefix), inline=True)
	# 			embed.add_field(name="\u200b",value="\u200b",inline=True)
	# 			embed.add_field(name="BAN User", value="`{0}ban @user <reason>`\n>>> <reason> is optional".format(prefix), inline=True)
	# 			embed.add_field(name="UNBAN User", value="`{0}unban <user id>`".format(prefix), inline=True)
	# 			embed.add_field(name="\u200b",value="\u200b",inline=True)
	# 			embed.add_field(name="Change Nickname", value="`{0}nick @user <new_nick>`".format(prefix), inline=True)
	# 			embed.add_field(name="Delete Message", value="`{0}clear <count> <@user>`\n>>> <@user> is optional\n>>> if selected user, all messages sent by <user> \n>>> will be deleted".format(prefix), inline=True)
	# 			embed.add_field(name="\u200b",value="\u200b",inline=True)
	# 			await ctx.send(embed=embed,delete_after=120)
	# 		elif title.lower() == "log":
	# 			embed = Embed(title=Lang["help_title"],
	# 					colour=ctx.author.colour,
	# 					timestamp=datetime.utcnow())
	# 			embed.add_field(name="Log setting", value="`{0}setting`\n>>> log display setting".format(prefix), inline=False)
	# 			embed.add_field(name="set Log display Channel", value="`{0}setlog <info> #channel`\n>>> info = ( msg / guild / member / voice )".format(prefix), inline=False)
	# 			embed.add_field(name="Ignore channel", value="`{0}ignore #channel`\n>>> Ignore channel messages (change/delete) log".format(prefix), inline=False)
	# 			embed.add_field(name="Show ignore channel list", value="`{0}show`\n>>> show ignore channel list".format(prefix), inline=False)
	# 			await ctx.send(embed=embed,delete_after=120)

	@commands.hybrid_command(aliases=["botinfo","bi"], with_app_command=True)
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
			(Lang["bot_online-time"],f"{uptime.days} days", True),
			#(Lang["bot_Ram"], f"{mem_usage:,.1f} / {mem_total:,.0f} MiB ({mem_of_total:.0f}%)", True),
			(Lang["bot_Guilds"], f"{len(self.bot.guilds)}", True),
			(Lang["bot_Users"], f"{len(self.bot.users)}", True)
		]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		#print(uptime)
		await ctx.send(embed=embed)


	@commands.hybrid_command(aliases=["memberinfo", "ui", "mi"], with_app_command=True)
	async def userinfo(self, ctx: commands.Context, target: Optional[Member]):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		target = target or ctx.author
		target_avatar = target.guild_avatar if target.guild_avatar else target.display_avatar or target.default_avatar
		info_data = get_user_guild_stats(target.id, ctx.guild.id)
		contribution = info_data.get('total') or 0
		last_message_time = info_data.get('last_message') or "defined"
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

	@commands.hybrid_command(aliases=["avatar"], with_app_command=True)
	async def useravatar(self, ctx: commands.Context, target: discord.Member):
		target = target or ctx.author
		target_avatar = target.guild_avatar if target.guild_avatar else target.display_avatar or target.default_avatar
		embed = Embed(title=f"{target} Avatar",
					  colour=target.colour,
					  timestamp=datetime.utcnow())

		embed.set_image(url=target_avatar.url)
		await ctx.send(embed=embed)
#
	#@commands.command()
	#async def stream(self,ctx):
	#	for i in ctx.guild.members:
	#		get_data = get_user_guild_stats(i.id, ctx.guild.id)
	#		if get_data != None:
	#			if get_data.get('stream_total_time') != None:
	#				stream_time = get_data.get('stream_total_time')
	#				s_time = time.strftime("%H:%M:%S", time.gmtime(int(stream_time)))
	#				await ctx.send(f"{i.name} {s_time}")
	#		else:
	#			pass
	#		#await ctx.send(f"{i.name} {stream_time}")
	#	await ctx.send("done")

	@commands.hybrid_command(aliases=["Spotify","SPOTIFY"], with_app_command=True)
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
	@commands.hybrid_command(with_app_command=True)
	async def who(self, ctx: commands.Context, find: int):
		try:
			target = await self.bot.fetch_user(find)
		except:
			await ctx.reply(f"can't find user by this ID")
			return

		embed = Embed(title="?犖靽⊥",
					  colour=ctx.author.colour,
					  timestamp=datetime.utcnow())
		target_avatar = target.avatar.url if target.avatar else target.default_avatar.url
		if target_avatar:
			embed.set_thumbnail(url=target_avatar)

		fields = [("??", f"**{target}**", True),
				  ("ID", target.id, True),
				  ("Bot?", target.bot, True),
				  ("Avatar", f'[Avatar link]({target_avatar})'if target_avatar else 'None',True),
				  #("???, str(target.status).title(), True),
				  #("??", f"{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'} {target.activity.name if target.activity else ''}", True),
				  ("?萄遣??", target.created_at.strftime("%d/%m/%Y %H:%M:%S"), True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)
	@commands.hybrid_command(aliases=["ri"], with_app_command=True)
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
			await ctx.send("Please provide a role.")
			return
		empty = True
		for member in ctx.message.guild.members:
			if role in member.roles:
				await ctx.send("{0.mention} {0.name}: {0.id}".format(member))
				empty = False
		if empty:
			await ctx.send("no one has {}".format(role.mention))
		
	@commands.hybrid_command(aliases=["guildinfo", "si", "gi"], with_app_command=True)
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
				  (Lang["gi_region"], ctx.guild.region, True),
				  (Lang["gi_Member-count"], len(ctx.guild.members), True),
				  #(Lang["gi_Got-BAN"], len(await ctx.guild.bans()), True),
				  (Lang["gi_created_at"], format_local_time(ctx.guild.created_at, guild_tz, "%d/%m/%Y %H:%M:%S"), True),
				  (Lang["gi_Human"], len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
				  (Lang["gi_Bot"], len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
				  (Lang["gi_statuses"], f"? {statuses[0]} ?? {statuses[1]} ? {statuses[2]} ??{statuses[3]}", True),
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

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meta(bot))


