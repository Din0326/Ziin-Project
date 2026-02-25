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
			#儲存最後一次訊息紀錄
			data = get_guild_settings(msg.guild.id)
			guild_tz = data.get('TimeZone') or 0
			msg_time = format_local_time(msg.created_at, guild_tz, "%d/%m/%Y %H:%M:%S")
			upsert_user_guild_last_message(msg.author.id, msg.guild.id, msg_time)

####	  自動存檔
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Msgs(bot))
