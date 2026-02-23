import random
import re
import time
from datetime import datetime, timedelta
import discord
from bot.core.classed import Cog_Extension
from bot.services.guild_settings import get_guild_settings
from bot.services.user_stats import upsert_user_guild_last_message
from bot.utils.timezone import format_local_time
from discord.ext import commands
class Msgs(Cog_Extension):

	async def imgc(self, msg: str):
		din = self.bot.get_user(371871742916034561)
		timestr = time.strftime("%m%d_%H:%M:%S")
		imchannel = self.bot.get_channel(753407077778456726)
		msginfo = (f'Time: {timestr} From {msg.guild}-{msg.channel.mention} By {msg.author.mention}\nJump to >>> {msg.jump_url} <<<')
		msginfoD = (f'Time: {timestr} From {msg.guild}-{msg.channel.mention} By ||{msg.author.name}||\nJump to >>> {msg.jump_url} <<<')
		if msg.author != din:
			await imchannel.send(msginfo)
			await imchannel.send(msg.content)
		else:
			await imchannel.send(msginfoD)
			await imchannel.send(msg.content)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: str):
		if payload.member.bot:
			return
		if payload.guild_id == 489008089840877568:
			guild = self.bot.get_guild(payload.guild_id)
			ch = self.bot.get_channel(payload.channel_id)
			msg = await ch.fetch_message(payload.message_id)
			if payload.emoji.id == 706505677450903652:
				for i in msg.reactions:
					if i.emoji.id == 706505677450903652:
						user_list = []
						async for y in i.users():
							user_list.append(y.id)
						if self.bot.user.id in user_list:
							if i.count >= 6:
								for channel in guild.text_channels:
									public = [489011156837597204,489013738058547210,712683884717801575]
									if channel.id in public:
										def _check(message):
											return message.author == payload.member
										try:
											await channel.purge(limit=30,check=_check)
										except:
											pass
#
	@commands.Cog.listener()
	async def on_message(self, msg: str):	
		if str(msg.channel.type) != "private":
			#??????綽?????????
			data = get_guild_settings(msg.guild.id)
			guild_tz = data.get('TimeZone') or 0
			msg_time = format_local_time(msg.created_at, guild_tz, "%d/%m/%Y %H:%M:%S")
			upsert_user_guild_last_message(msg.author.id, msg.guild.id, msg_time)
####	 	????怨?謒?			#??????頦?
			if msg.channel.id == 903081545311617034 and msg.author != self.bot.user:
				if msg.author.id == 458165526363897856:
					return
				con = msg.content
				await msg.delete()
				await msg.channel.send(con)
				#await msg.delete()
				#susu?Ｘ?
				if msg.channel.id == 625729755991506986 and msg.author != self.bot.user:
					if msg.content.lower() == 'matt':
						ava = self.bot.get_user(166901140162740224).avatar.url
						mat = [f"{ava}", "matt", "hello"]
						random_mat = random.choice(mat)
						await msg.channel.send(random_mat)
				keys_List = ['蝚香','?⊥香','?⊿?','?香','蝚?']
				if msg.content in keys_List and msg.author != self.bot.user:
					await msg.channel.send("蝚香")
				#if msg.content in tdata.keys() and msg.author != self.bot.user:
			#flash?Ｘ?
			if msg.guild.id == 489008089840877568 and msg.author != self.bot.user:
				risky = ['nitro','discord','gift','@everyone','free','??孕','game','test']
				#if 'http://steancomunnity.ru/'in msg.content.lower() or 'discord nitro for free' in msg.content.lower():
				#	await msg.author.ban(reason="??????")
				#	await msg.channel.send(f'{msg.author.mention}???????賹?: ?瞏捍蹓選?啾垓???\n||ID : {msg.author.id}|| \nR.I.P. \n{msg.author.joined_at.strftime("%Y-%m-%d")} ~ {date.today()}')
				#elif '.ru/' in msg.content.lower():
				#	admin = msg.guild.get_role(489009209044631553)
				#	if 'new/?partner=' in msg.content.lower() and 'token=' in msg.content.lower():
				#		await msg.author.ban(reason="??????")
				#		await msg.channel.send(f'{msg.author.mention}???????賹?: ?瞏捍蹓選?啾垓???\n||ID : {msg.author.id}|| \nR.I.P. \n{msg.author.joined_at.strftime("%Y-%m-%d")} ~ {date.today()}')
				#	else:
				#		await msg.channel.send(f"{admin.mention} check message.")
				count = 0
				url = True
				for keyword in risky:
					urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',msg.content.lower())
					if urls and url:
						count += 1
						url = False
					if keyword in msg.content.lower():
						count += 1
				if count >= 3:
					await msg.add_reaction(":thinking1:706505677450903652")	

####	 ????殉朵?
			if 'https://' in msg.content.lower() and 'jpg' in msg.content.lower() and msg.author != self.bot.user:
				await self.imgc(msg)
			if 'https://' in msg.content.lower() and 'png' in msg.content.lower() and msg.author != self.bot.user:
				await self.imgc(msg)
			if 'https://' in msg.content.lower() and 'gif' in msg.content.lower() and msg.author != self.bot.user:
				await self.imgc(msg)
			if 'https://' in msg.content.lower() and 'mp4' in msg.content.lower() and msg.author != self.bot.user:
				await self.imgc(msg)
			if 'https://' in msg.content.lower() and 'mkv' in msg.content.lower() and msg.author != self.bot.user:
				await self.imgc(msg)
			if 'https://' in msg.content.lower() and 'mov' in msg.content.lower() and msg.author != self.bot.user:
				await self.imgc(msg)
	
			if msg.attachments and len(msg.attachments) >= 1:
				timestr = time.strftime("%m%d_%H:%M:%S")
				din = self.bot.get_user(371871742916034561)
				imchannel = self.bot.get_channel(753407077778456726)
				msginfo = (f'Time: {timestr} From {msg.guild}-{msg.channel.mention} By {msg.author.mention}\nJump to >>> {msg.jump_url} <<<')
				msginfoD = (f'Time: {timestr} From {msg.guild}-{msg.channel.mention} By ||{msg.author.name}||\nJump to >>> {msg.jump_url} <<<')
				if msg.author != din:
					await imchannel.send(msginfo)
					for x in range(len(msg.attachments)):
						await imchannel.send(msg.attachments[x-1].url)
					#await msg.attachments[x-1].save(fp=f"C:\\789\\imgur\\{timestr}_{msg.attachments[x-1].id}.png")
					#print (f'Save {timestr}_{msg.attachments[x-1].id}.png')
				else:
					await imchannel.send(msginfoD)
					for x in range(len(msg.attachments)):
						await imchannel.send(msg.attachments[x-1].url)
		else:
			if msg.content == "z!link":
				user = self.bot.get_user(371871742916034561)
				user_img = user.avatar or user.default_avatar
				embed = discord.Embed(title=f"{self.bot.user.name} ???ｇ????綜等?!", url="https://discord.com/oauth2/authorize?client_id=1433679331284090931&permissions=8&integration_type=0&scope=bot+applications.commands",timestamp=datetime.utcnow())
				embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
				embed.set_thumbnail(url=self.bot.user.avatar.url)
				embed.set_footer(icon_url=(user_img.url),text=f'{user}')
				fields = [("Owner????????????澈???", "**dinnn._o??????????z!**\n\n???ｇ?ot???秋撮??????????????輯撒?og?賹?  \n???ｇ???ｇ???隞遴? z!help ?方??蝔?????祇??遴???選???祇????ｇ??? [Support Server](https://discord.gg/EtQX9RB9Xr)", True)]
		
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
				await msg.channel.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Msgs(bot))
