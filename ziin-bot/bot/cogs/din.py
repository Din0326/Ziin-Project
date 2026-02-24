import typing
from datetime import date, datetime, timedelta
from typing import Optional

import discord
from bot.core.classed import Cog_Extension
from bot.services.guild_settings import update_guild_settings
from bot.utils.guild_context import get_ctx_lang_tz
from discord import Member
from discord.ext import commands
from discord.ext.commands import Greedy, has_permissions


class Din(Cog_Extension):
	async def dinID(ctx: commands.Context):
		if ctx.author.id == 371871742916034561:
			return True
		else:
			await ctx.send("Only Din can use this command.", delete_after=10)

	#@commands.command(hidden=True)
	#@commands.check(dinID)
	#async def ss(self,ctx):
	#	with open('keyword.json', 'r', encoding='utf-8-sig') as tfile:
	#		tdata = json.load(tfile)
	#		val = '4'
	#	keys = [k for k, v in tdata.items() if v == 'hi']
	#	await ctx.send(tdata.items())
	#	await ctx.send(keys)
	@commands.hybrid_command(with_app_command=True)
	@commands.check(dinID)
	async def renick(self, ctx: commands.Context):
		for i in ctx.guild.members:
			await ctx.send(i)
			member = self.bot.get_guild.get_member(i.id)
			await member.edit(nick=None)


	@commands.hybrid_command(with_app_command=True)
	@commands.check(dinID)
	async def din_steal(self, ctx: commands.Context, emoji: discord.PartialEmoji):
		emoji_bytes = await emoji.read()
		await ctx.guild.create_custom_emoji(name=emoji.name,image=emoji_bytes)
		await ctx.send(emoji)

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_ua(self, ctx: commands.Context, target: int):
		target = await self.bot.fetch_user(target)
		target_icon = target.avatar
		await ctx.send(target_icon.url)
		#embed = Embed(title=f"{target} Avatar",
		#			  timestamp=datetime.utcnow())
#
		#embed.set_image(url=target.avatar.url)
		#await ctx.send(embed=embed)

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_sl(self, ctx: commands.Context, *, lang: str):
		if lang.lower() == "tw": 
			update_guild_settings(ctx.guild.id, {"Language": "zh-TW"})
			await ctx.send("隤?閮剔蔭撌脫?寧 **蝜?銝剜?**")
		elif lang.lower() == "en": 
			update_guild_settings(ctx.guild.id, {"Language": "English"})
			await ctx.send("Language change to **English**")

	@commands.hybrid_command(with_app_command=True)
	@commands.check(dinID)
	async def din_p(self, ctx: commands.Context, *, new_prefix: str):
		Lang , guild_tz = get_ctx_lang_tz(ctx)
		if len(new_prefix) <= 3: 
			update_guild_settings(ctx.guild.id, {"Prefix": new_prefix})
			await ctx.send(Lang["prefix_new"].format(new_prefix))
		else:
			await ctx.send(Lang["prefix_max"])

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_tz(self, ctx: commands.Context, *, utc_time: int):
		if 12 >= utc_time >= -12:
			update_guild_settings(ctx.guild.id, {"TimeZone": utc_time})
			if utc_time >= 0:
				await ctx.send(f"??撌脰身蝵桃 **UTC+{utc_time}**")
			else:
				await ctx.send(f"??撌脰身蝵桃 **UTC{utc_time}**")
		else:
			await ctx.send("隢撓?交迤蝣摻TC?? **12** ~ **-12**")

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_send(self, ctx: commands.Context, *, msg: str):
		ChannelID = int(msg.split( )[0])
		text = msg.split( )[1]
		textchannel = self.bot.get_channel(ChannelID)
		await textchannel.send(text)


	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_dm(self, ctx: commands.Context, *, msg: str):
		dmID = int(msg.split( )[0])
		dmmsg = msg.split( )[1]
		dmmember = self.bot.get_user(dmID)
		await dmmember.send(dmmsg)

#### ?擃???隞?	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_n(self, ctx: commands.Context, member: discord.Member, *, nick: str):
		await member.edit(nick=nick)
		await ctx.send(f'{member.mention} ?梁迂撌脫?寧 __{nick}__')

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_m(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
		await member.edit(reason=reason,mute= True)
		await ctx.send(f'{member.mention} ??慦賡???')

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_um(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
		await member.edit(reason=reason,mute= False)
		await ctx.send(f'{member.mention} ??雿?甈?')

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_b(self, ctx: commands.Context, user : discord.Member, *, reason: typing.Optional[str] = None):
		await user.ban(reason=reason)
		await ctx.send(f'{user.mention}?甇餃\n||ID : {user.id}|| \nR.I.P. \n{user.joined_at.strftime("%Y-%m-%d")} ~ {date.today()}')

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_ub(self, ctx: commands.Context, target: int, *, reason: typing.Optional[str] = None):
		user = self.bot.get_user(target)
		await ctx.guild.unban(user, reason=reason)
		await ctx.send(f'{user.name}#{user.discriminator} unbanned')
		

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_k(self, ctx: commands.Context, target: discord.Member, *, reason: typing.Optional[str] = None):
		await target.kick(reason=reason)
		await ctx.send(f"{target.mention} kicked.")

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_c(self, ctx: commands.Context, targets: Greedy[Member], limit: Optional[int] = 1):
		def _check(message):
			return not len(targets) or message.author in targets
		if 0 < limit <= 500:
			async with ctx.channel.typing():
				await ctx.message.delete()
				deleted = await ctx.channel.purge(limit=limit, after=datetime.utcnow()-timedelta(days=14),
												  check=_check)

			await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after=5)
		else:
			await ctx.send("銝甈⊥?憭?00???粹?")

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_inv(self, ctx: commands.Context, *, serverid:int):
		channelid = self.bot.get_guild(serverid).channels[10].id
		channel = self.bot.get_channel(channelid)
		link = await channel.create_invite()
		await ctx.send(link)

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_get(self, ctx: commands.Context):
		users = len(self.bot.users)
		guilds = len(self.bot.guilds)
		await ctx.send(f"user : {users}\nguild : {guilds}")

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@commands.check(dinID)
	async def din_lg(self, ctx: commands.Context, *, serverid:int):
		guild = self.bot.get_guild(serverid)
		await self.bot.get_guild(serverid).leave()
		await ctx.send(f"leave {guild}")

	#@commands.command(hidden=True)
	#@commands.check(dinID)
	#async def checknick(self, ctx):
	#	for i in ctx.guild.member:
	#		if i.nick.startswith()

	@commands.hybrid_command(hidden=True, with_app_command=True)
	@has_permissions(ban_members = True)
	async def din_rc(self, ctx: commands.Context):
		if ctx.guild.id == 804604858090127360:
			#guild = ctx.guild
			boost = ctx.guild.get_role(805074449668898878)
			vip = ctx.guild.get_role(855376997429673985)
			await ctx.send("start")
			for i in ctx.guild.members:
				if boost not in i.roles:
					if vip not in i.roles:
						count = 0
						for x in i.roles:
							if 38 <= x.position and x.name not in ["BOT","Manager","Trial Mod","Bot Manager","Moderator","Quarantine","Statbot","Dev","First God-Like","God-Like","Lexa","Streamer"] and count == 0:
								await ctx.send(f"!!! {i.mention}  //  {x}")
								count = 1
							#else:
							#	if 38 <= x.position and x.name not in ["BOT","Manager","Trial Mod","Bot Supreme Leader","Moderator"]:
							#		await ctx.send(f"!!! {i.mention}  //  {x}")
					else:
						count == 0
						for x in i.roles:
							if 38 <= x.position and x.name not in ["BOT","Manager","Trial Mod","Bot Manager","Moderator","Quarantine","Statbot","Dev","First God-Like","God-Like","Lexa","Streamer"] and count == 0:
								await ctx.send(f"!!! {i.mention}  //  {x} // {vip}")
								count = 1
							else:
								if x.id == 855376997429673985:
									await ctx.send(f"!!! {i.mention} // {vip}")
									count = 1
	@commands.hybrid_command(hidden=True, with_app_command=True)
	@has_permissions(ban_members = True)
	async def din_nickc(self, ctx: commands.Context):
		if ctx.guild.id == 804604858090127360:
			#guild = ctx.guild
			boost = ctx.guild.get_role(805074449668898878)
			vip = ctx.guild.get_role(855376997429673985)
			await ctx.send("start")
			for i in ctx.guild.members:
				if i.nick != None:
					if boost not in i.roles:
						await ctx.send(i.mention)
			await ctx.send("done")
	@commands.hybrid_command(hidden=True, with_app_command=True)
	@has_permissions(ban_members = True)
	async def din_vvc(self, ctx: commands.Context):
		if ctx.guild.id == 804604858090127360:
			#guild = ctx.guild
			boost = ctx.guild.get_role(805074449668898878)
			vip = ctx.guild.get_role(855376997429673985)
			await ctx.send("start")
			for i in ctx.guild.members:
				if boost not in i.roles and vip in i.roles:
						await ctx.send(f"!!! {i.mention} // {vip}")

			await ctx.send("done")
#

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Din(bot))
