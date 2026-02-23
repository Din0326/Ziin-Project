import random
from datetime import datetime, timedelta

import discord
from bot.core.classed import Cog_Extension
from bot.services.user_stats import get_user_guild_stats
from discord.ext import commands

gamingChannel = {}

class Flash(Cog_Extension):
	async def dinID(ctx: commands.Context):
		if ctx.author.id == 371871742916034561:
			return True
		else:
			await ctx.send("Only Din can use this command.", delete_after=10)
	

	@commands.Cog.listener()
	async def on_message(self, msg: str):
		if msg.channel == self.bot.get_channel(1072183683160756284):
			await msg.publish()
			await msg.add_reaction("<:monkeyflash:1072838226580099112>")

	@commands.check(dinID)
	@commands.hybrid_command(with_app_command=True)
	async def fkick(self, ctx: commands.Context, dateline: str):
		#loading = await ctx.send('霈?葉...')
		dateline = f"{dateline} 00:00:00"
		dateline_dt = datetime.strptime(dateline,"%d/%m/%Y %H:%M:%S")
		join_today = 0
		zero_message = 0
		pass_message = 0
		miss_message = 0
		breaked = 0
		total = 0
		loading = await ctx.send('霈?葉...')
		failed = []
		failed_db = []
		for target in ctx.guild.members:
			try:
				info_data = get_user_guild_stats(target.id, ctx.guild.id)
			except:
				breaked += 1
				total +=1
				failed_db.append(target.id)
				continue
			if info_data == None:
				join_dt = datetime.strptime((target.joined_at + timedelta(hours=8)).strftime("%d/%m/%Y %H:%M:%S"),"%d/%m/%Y %H:%M:%S")
				if join_dt.day == datetime.now().day:
					#await ctx.send('隞予?')
					join_today += 1
				else:
					try:
						await target.kick()
					except:
						failed.append(target.id)
					zero_message += 1
			else:
				try:
					last_message_time = info_data.get('last_message')
					target_dt = datetime.strptime(last_message_time,"%d/%m/%Y %H:%M:%S")
				except:
					breaked += 1
					total +=1
					print(target.id)
					continue
				if target_dt >= dateline_dt:
					pass_message += 1
					#await ctx.send(f"?芣迫?亦: {dateline}\n?敺?甈∠閮?? {last_message_time}\n??")
				else:
					miss_message += 1
					try:
						await target.kick()
					except:
						failed.append(target.id)
			total += 1
			if random.randint(1,100) > 90:
				print(f"total:{total}\n隞予?:{join_today}\n瘝閮??{zero_message}\n餈??扳??潸?:{pass_message}\n餈??抒?潸?:{miss_message}----{breaked}")
			await ctx.send(f"隞予?:{join_today}\n瘝閮??{zero_message}\n餈??扳??潸?:{pass_message}\n餈??抒?潸?:{miss_message}----{breaked}")
			await loading.edit(content="Done")
	
	@commands.Cog.listener()
	async def on_voice_state_update(self, member: discord.Member, before: str, after: str):
		if member.guild.id != 1072173579229200404:
			return
		if before.channel and str(before.channel.id) in gamingChannel.keys():
			if not before.channel.members:
				gamingChannel.pop(str(before.channel.id))
				await before.channel.edit(name='頠??駁?',user_limit=0)

	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member):
		if member.guild.id == 1072173579229200404:
			member_channel = self.bot.get_channel(1072175214324105298)
			await member_channel.send(f"{member.mention} joined {member.guild}.")

	@commands.Cog.listener()
	async def on_member_remove(self, member: discord.Member):
		if member.guild.id == 1072173579229200404:
			member_channel = self.bot.get_channel(1072175214324105298)
			await member_channel.send(f"{member} ||{member.id}|| left {member.guild}.")

	@commands.check(dinID)
	@commands.hybrid_command(with_app_command=True)
	async def adddd(self, ctx: commands.Context):
		Remsg = await self.bot.get_channel(1072181968676069396).fetch_message(1072222608478699570)
		await Remsg.add_reaction("?")
		await Remsg.add_reaction("?")
		await Remsg.add_reaction("?")
		await Remsg.add_reaction("?")
		await Remsg.add_reaction("?")

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: str):
		#頨怠?蝯?????		role_msg = await self.bot.get_channel(1072181968676069396).fetch_message(1072222608478699570)
		if payload.message_id == 1072222608478699570:
			#銵冽?撠??澈??id
			reaction_role = {
				"?" : 1072220703316779059,
				"?" : 1072192352405434368,
				"?" : 1072193106742628383,
				"?" : 1072191846144561322,
				"?" : 1072709271046860800
			}
			roleID = reaction_role[payload.emoji.name]
			user_role = self.bot.get_guild(payload.guild_id).get_role(roleID)
			reaction_user = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
			if reaction_user.get_role(1072220703316779059) or payload.emoji.name == "?":
				await reaction_user.add_roles(user_role)
			else:
				await role_msg.remove_reaction(payload.emoji.name,reaction_user)


	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload: str):
		#頨怠?蝯?????		role_msg = await self.bot.get_channel(1072181968676069396).fetch_message(1072222608478699570)
		if payload.message_id == 1072222608478699570:
			#銵冽?撠??澈??id
			reaction_role = {
				"?" : 1072220703316779059,
				"?" : 1072192352405434368,
				"?" : 1072193106742628383,
				"?" : 1072191846144561322,
				"?" : 1072709271046860800
			}
			roleID = reaction_role[payload.emoji.name]
			user_role = self.bot.get_guild(payload.guild_id).get_role(roleID)
			reaction_user = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

			await reaction_user.remove_roles(user_role)
			if payload.emoji.name == "?":
				for reaction in reaction_role.keys():
					try:
						await role_msg.remove_reaction(reaction,reaction_user)
					except:
						pass

					# 鈭箸憭芸?撠敺芰??憭芷 ?銝末
				#for reaction in role_msg.reactions:
				#	users = []
				#	async for user in reaction.users():
				#		users.append(user.id)
				#	if reaction_user.id in users:
				#		await role_msg.remove_reaction(reaction.emoji,reaction_user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Flash(bot))


