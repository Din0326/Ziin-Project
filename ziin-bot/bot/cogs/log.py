import re
from datetime import datetime, timedelta

import discord
from bot.core.classed import Cog_Extension
from bot.services.guild_settings import (get_guild_settings, get_log_settings,
                                         update_guild_settings)
from bot.services.user_stats import (add_stream_total_seconds,
                                     add_user_voice_total_hours,
                                     get_user_guild_stats,
                                     get_user_voice_channel_stats,
                                     upsert_stream_end, upsert_stream_start,
                                     upsert_user_voice_join,
                                     upsert_user_voice_leave)
from bot.utils.guild_context import get_lang_pack
from discord import Embed
from discord.ext import commands

delete_count = 0
last_audit_log_id = 0

def data_Check_language(data):
	return get_lang_pack(data.get("Language"))

class Log(Cog_Extension):
	
####蝢斤??湔
	@commands.Cog.listener()
	async def on_guild_update(self, before: str, after: str):
		data = get_guild_settings(after.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		log = get_log_settings(after.id)
		guildUpdate = log.get('guildUpdate')
		fields = None
		if Guild_ID == None:
			return
		guildchannel = self.bot.get_channel(Guild_ID)

		async for entry in after.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			embed = Embed(description=Lang["gu_title"],
						  timestamp=datetime.utcnow())
			embed.set_author(name=f"{entry.user.name}#{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))

			if before.system_channel != after.system_channel:
				fields = [(Lang["gu_system_channel"], Lang["gu_update_text"].format(after.system_channel,before.system_channel), False)]
			if before.afk_channel != after.afk_channel:
				fields = [(Lang["gu_afk_channel"], Lang["gu_update_text"].format(after.afk_channel,before.afk_channel), False)]
			if before.afk_timeout != after.afk_timeout:
				fields = [(Lang["gu_afk_timeout"], Lang["gu_update_text"].format(after.afk_timeout,before.afk_timeout), False)]
			if before.region != after.region:
				fields = [(Lang["gu_region"], Lang["gu_update_text"].format(after.region,before.region), False)]
			if before.name != after.name:
				fields = [(Lang["gu_name"], Lang["gu_update_text"].format(after.name,before.name), False)]
				update_guild_settings(after.id, {'Name': after.name})
			if before.icon != after.icon:
				fields = [(Lang["gu_icon"], Lang["gu_update_text"].format(after.icon_url,before.icon_url), False)]
			if before.owner != after.owner:
				fields = [(Lang["gu_owner"], Lang["gu_update_text"].format(after.owner,before.owner), False)]
			if before.description != after.description:
				fields = [("description", f"??Now: **{after.description}**\n??Was: **{before.description}**", False)]
			if before.mfa_level != after.mfa_level:
				fields = [("mfa_level", f"??Now: **{str(after.mfa_level)}**\n??Was: **{str(before.mfa_level)}**", False)]
			if before.verification_level != after.verification_level:
				fields = [("verification_level", f"??Now: **{str(after.verification_level)}**\n??Was: **{str(before.verification_level)}**", False)]
			if before.default_notifications != after.default_notifications:
				fields = [("default_notifications", f"??Now: **{str(after.default_notifications)}**\n??Was: **{str(before.default_notifications)}**", False)]
			if before.premium_tier != after.premium_tier:
				fields = [("premium_tier", f"??Now: **Level {after.premium_tier}**\n??Was: **Level {before.premium_tier}**", False)]
			if before.explicit_content_filter != after.explicit_content_filter:
				fields = [("explicit_content_filter", f"??Now: **{after.explicit_content_filter}**\n??Was: **{before.explicit_content_filter}**", False)]
			#if before. != after.:
			#	fields = [("", f"??Now: **{after.}**\n??Was: **{before.}**", False)]
			if fields != None:
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
			if guildUpdate == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)
	
####?駁? ?萄遣 ?芷
	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel: discord.TextChannel):
		testmsg = self.bot.get_channel(737830510952185878)
		action_user = self.bot.user.avatar.url
		data = get_guild_settings(channel.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		log = get_log_settings(channel.guild.id)
		channelCreate = log.get('channelCreate')
		guildchannel = self.bot.get_channel(Guild_ID)
		if Guild_ID == None:
			return
		channel_list=[{"code":"text","name":Lang["gc_text_create"]},
		  {"code":"voice","name":Lang["gc_voice_create"]},
		  {"code":"news","name":Lang["gc_news_create"]}]
		async for entry in channel.guild.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			for text in channel_list:
				if str(channel.type) == text['code']:
					embed = Embed(description=text['name'].format(channel.mention),
							  timestamp=datetime.utcnow())
					embed.set_author(name=f"{entry.user.name}###{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))
					embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
					fields = [(Lang["gc_name"], channel, False),
							  (Lang["gc_id"], f"``{channel.id}``",False)]
					for name, value, inline in fields:
						embed.add_field(name=name, value=value, inline=inline)
			if channelCreate == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel: discord.TextChannel):
		action_user = self.bot.user.avatar.url
		testmsg = self.bot.get_channel(737830510952185878)
		data = get_guild_settings(channel.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		guild_tz = data.get('TimeZone')
		log = get_log_settings(channel.guild.id)
		channelDelete = log.get('channelDelete')
		guildchannel = self.bot.get_channel(Guild_ID)
		if Guild_ID == None:
			return
		channel_list=[{"code":"text","name":Lang["gc_text_delete"]},
		  {"code":"voice","name":Lang["gc_voice_delete"]},
		  {"code":"news","name":Lang["gc_news_create"]}]
		async for entry in channel.guild.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			for text in channel_list:
				if str(channel.type) == text['code']:
					embed = Embed(description=text['name'].format(channel),
							  timestamp=datetime.utcnow())
					embed.set_author(name=f"{entry.user.name}###{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))
					embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
					fields = [(Lang["gc_name"], channel, False),
							  (Lang["gc_id"], f"``{channel.id}``",False),
							  (Lang["gc_created_at"], (channel.created_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"),False)]
					for name, value, inline in fields:
						embed.add_field(name=name, value=value, inline=inline)
			if channelDelete == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)

	@commands.Cog.listener()
	async def on_channel_update(self, before: str, after: str):
		data = get_guild_settings(after.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		log = get_log_settings(after.id)
		channelUpdate = log.get('channelUpdate')
		fields = None
		if Guild_ID == None:
			return
		guildchannel = self.bot.get_channel(Guild_ID)

		async for entry in after.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			embed = Embed(description=Lang["gu_title"],
						  timestamp=datetime.utcnow())
			embed.set_author(name=f"{entry.user.name}#{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))

			if before.name != after.name:
				fields = [("Name", f"??Now: **{after.name}**\n??Was: **{before.name}**", False)]
			#if before. != after.:
			#	fields = [("", f"??Now: **{after.}**\n??Was: **{before.}**", False)]
			if fields != None:
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
			if channelUpdate == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)
####頨怠?蝯??萄遣 ?芷
	@commands.Cog.listener()
	async def on_guild_role_create(self, role: discord.Role):
		testmsg = self.bot.get_channel(737830510952185878)
		action_user = self.bot.user.avatar.url
		data = get_guild_settings(role.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		log = get_log_settings(role.guild.id)
		RoleCreate = log.get('RoleCreate')
		guildchannel = self.bot.get_channel(Guild_ID)
		if Guild_ID == None:
			return
		async for entry in role.guild.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			embed = Embed(description=Lang["ru_create"],
							  colour=role.colour,
							  timestamp=datetime.utcnow())
	
			embed.set_author(name=f"{entry.user.name}#{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))
			embed.add_field(name=Lang["ru_name"],value=role.name,inline=False)
			embed.add_field(name=Lang["ru_id"],value=f"``{role.id}``",inline=False)
			embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
			if RoleCreate == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)
	@commands.Cog.listener()
	async def on_guild_role_delete(self, role: discord.Role):
		testmsg = self.bot.get_channel(737830510952185878)
		action_user = self.bot.user.avatar.url
		data = get_guild_settings(role.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		log = get_log_settings(role.guild.id)
		RoleDelete = log.get('RoleDelete')
		guildchannel = self.bot.get_channel(Guild_ID)
		if Guild_ID == None:
			return
		async for entry in role.guild.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			action_user = self.bot.user.avatar.url
			embed = Embed(description=Lang["ru_delete"],
							  colour=role.colour,
							  timestamp=datetime.utcnow())
	
			embed.set_author(name=f"{entry.user.name}#{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))
			embed.add_field(name=Lang["ru_name"],value=role.name,inline=False)
			embed.add_field(name=Lang["ru_reason"],value=entry.reason,inline=False)
			embed.add_field(name=Lang["ru_id"],value=f"``{role.id}``",inline=False)
			embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
			if RoleDelete == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)
	@commands.Cog.listener()
	async def on_guild_role_update(self, before: str, after: str):
		testmsg = self.bot.get_channel(737830510952185878)
		action_user = self.bot.user.avatar.url
		data = get_guild_settings(after.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('guild_log_id')
		log = get_log_settings(after.guild.id)
		RoleUpdate = log.get('RoleUpdate')
		guildchannel = self.bot.get_channel(Guild_ID)
		if Guild_ID == None:
			return
		if before.position != after.position or before.hoist != after.hoist:
			return
		async for entry in after.guild.audit_logs(limit=1):
			icon_user = entry.user.avatar or entry.user.default_avatar
			embed = Embed(description=Lang["ru_update"].format(after.name),
							  colour=after.colour,
							  timestamp=datetime.utcnow())
	
			embed.set_author(name=f"{entry.user.name}#{entry.user.discriminator} ({entry.user.display_name})",icon_url=(icon_user.url))
			if before.name != after.name:
				embed.add_field(name=Lang["ru_name"],value=f"Now: {after.name}\nWas: {before.name}",inline=False)
			if before.colour != after.colour:
				embed.add_field(name=Lang["ru_colour"],value=f"Now: {after.colour}\nWas: {before.colour}",inline=False)
			if before.permissions != after.permissions:
				diff = list(set(after.permissions).difference(set(before.permissions)))
				for changed_perm in diff:
					embed.add_field(name=Lang["ru_permissions"],value=f"{changed_perm[0]} => {changed_perm[1]}",inline=False)
			embed.add_field(name=Lang["ru_id"],value=f"``{after.id}``",inline=False)
			embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
			if RoleUpdate == "on" and guildchannel is not None:
				await guildchannel.send(embed=embed)

####? ????	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member):
		action_user = self.bot.user.avatar.url
		data = get_guild_settings(member.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('ID')
		Member_ID = data.get('member_log_id')
		guild_tz = data.get('TimeZone')
		if Member_ID == None:
			return
		memberchannel = self.bot.get_channel(Member_ID)
		log = get_log_settings(member.guild.id)
		Add = log.get('MemberAdd')
		icon_user = member.avatar or member.default_avatar
		embed = Embed(title=Lang["mu_join"],
					  colour=member.colour,
					  timestamp=datetime.utcnow())
		embed.set_author(name=f"{member.name}#{member.discriminator} ({member.display_name})",icon_url=(icon_user.url))
		embed.set_thumbnail(url=icon_user.url)
		embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')

		fields = [(Lang["mu_mention"], member.mention, True),
				  (Lang["mu_id"], member.id, True),
				  (Lang["mu_bot"], member.bot, True),
				  (Lang["mu_created_at"], (member.created_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
				  (Lang["mu_joined_at"], (member.joined_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		if Add == "on" and memberchannel is not None:
			await memberchannel.send(embed=embed)
	@commands.Cog.listener()
	async def on_member_remove(self, member: discord.Member):
		bot_user = self.bot.user.avatar.url
		data = get_guild_settings(member.guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('ID')
		Member_ID = data.get('member_log_id')
		guild_tz = data.get('TimeZone')
		if Member_ID == None:
			return
		memberchannel = self.bot.get_channel(Member_ID)
		log = get_log_settings(member.guild.id)
		Remove = log.get('MemberRemove')
		icon_user = member.avatar or member.default_avatar
		async for entry in member.guild.audit_logs(limit=1):
			action_user = entry.user.avatar or entry.user.default_avatar
			if entry.action == discord.AuditLogAction.kick and entry.target == member:
				embed = Embed(title=Lang["mu_kick"],
							  colour=member.colour,
							  timestamp=datetime.utcnow())
				embed.set_author(name=f"{member.name}#{member.discriminator} ({member.display_name})",icon_url=(icon_user.url))
				embed.set_thumbnail(url=icon_user.url)
				embed.set_footer(icon_url=(action_user.url),text=f'{entry.user}')
		
				fields = [(Lang["mu_mention"], member.mention, True),
						  (Lang["mu_id"], member.id, True),
						  (Lang["mu_bot"], member.bot, True),
						  (Lang["mu_created_at"], (member.created_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_joined_at"], (member.joined_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_leaved_at"], (datetime.now() + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_operator"], entry.user.mention,True)]
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
			elif entry.action == discord.AuditLogAction.ban and entry.target == member:
				embed = Embed(title=Lang["mu_ban"],
							  colour=member.colour,
							  timestamp=datetime.utcnow())
				embed.set_author(name=f"{member.name}#{member.discriminator} ({member.display_name})",icon_url=(icon_user.url))
				embed.set_thumbnail(url=icon_user.url)
				embed.set_footer(icon_url=(action_user),text=f'{entry.user}')
		
				fields = [(Lang["mu_mention"], member.mention, True),
						  (Lang["mu_id"], member.id, True),
						  (Lang["mu_bot"], member.bot, True),
						  (Lang["mu_created_at"], (member.created_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_joined_at"], (member.joined_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_leaved_at"], (datetime.now() + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_operator"], entry.user.mention,True)]
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
			else:
				embed = Embed(title=Lang["mu_leave"],
							  colour=member.colour,
							  timestamp=datetime.utcnow())
				embed.set_author(name=f"{member.name}#{member.discriminator} ({member.display_name})",icon_url=(icon_user.url))
				embed.set_thumbnail(url=icon_user.url)
				embed.set_footer(icon_url=self.bot.user.avatar.url,text=f'{self.bot.user}')
		
				fields = [(Lang["mu_mention"], member.mention, True),
						  (Lang["mu_id"], member.id, True),
						  (Lang["mu_bot"], member.bot, True),
						  (Lang["mu_created_at"], (member.created_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_joined_at"], (member.joined_at + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
						  (Lang["mu_leaved_at"], (datetime.now() + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True)]
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
			if Remove == "on" and memberchannel is not None:
				await memberchannel.send(embed=embed)

####? 撠??圾撠?	#@commands.Cog.listener()
#	 async def on_member_ban(self, guild, member):
	#	bot_user = f"{self.bot.user.avatar.url}.png"
	#	data = get_guild_settings(guild.id)
	#	Lang = data_Check_language(data)
	#	Guild_ID = data.get('ID')
	#	Member_ID = data.get('member_log_id')
	#	if Member_ID == None:
	#		return
	#	memberchannel = self.bot.get_channel(Member_ID)
	#	log = get_log_settings(guild.id)
	#	Remove = log.get('MemberRemove')
	#	icon_user = member.avatar or member.default_avatar
	#	async for entry in guild.audit_logs(limit=1):
	#		action_user = entry.user.avatar or entry.user.default_avatar
	#		if entry.action == discord.AuditLogAction.ban and entry.target == member:
	#			embed = Embed(title=Lang["mu_ban"],
	#						  timestamp=datetime.utcnow())
	#			embed.set_author(name=f"{member.name}#{member.discriminator} ({member.display_name})",icon_url=(icon_user.url))
	#			embed.set_thumbnail(url=member.avatar.url)
	#			embed.set_footer(icon_url=(action_user.url),text=f'{entry.user}')
	#	
	#			fields = [(Lang["mu_id"], member.id, True),
	#					  (Lang["mu_bot"], member.bot, True),
	#					  (Lang["mu_created_at"], member.created_at.strftime("%d-%m-%Y %H:%M:%S"), True),
	#					  (Lang["mu_leaved_at"], datetime.now().strftime("%d-%m-%Y %H:%M:%S"), True),
	#					  (Lang["mu_operator"], entry.user.mention,False)]
	#	
	#			for name, value, inline in fields:
	#				embed.add_field(name=name, value=value, inline=inline)
	#		if Remove == "on" and memberchannel is not None:
	#			await memberchannel.send(embed=embed)
#
	@commands.Cog.listener()
	async def on_member_unban(self, guild: str, user: discord.Member):
		bot_user = self.bot.user.avatar.url
		data = get_guild_settings(guild.id)
		Lang = data_Check_language(data)
		Guild_ID = data.get('ID')
		Member_ID = data.get('member_log_id')
		guild_tz = data.get('TimeZone')
		if Member_ID == None:
			return
		memberchannel = self.bot.get_channel(Member_ID)
		log = get_log_settings(guild.id)
		Unban = log.get('MemberUnban')
		icon_user = user.avatar or user.default_avatar
		async for entry in guild.audit_logs(limit=1):
			action_user = entry.user.avatar or entry.user.default_avatar
			embed = Embed(title=Lang["mu_unban"],
						  timestamp=datetime.utcnow())
			embed.set_author(name=f"{user.name}#{user.discriminator}",icon_url=(icon_user.url))
			embed.set_thumbnail(url=icon_user.url)
			embed.set_footer(icon_url=(action_user.url),text=f'{entry.user}')
	
			fields = [(Lang["mu_mention"], f"{user.name}#{user.discriminator}", True),
					  (Lang["mu_id"], user.id, True),
					  (Lang["mu_bot"], user.bot, True),
					  (Lang["mu_unbanned_at"], (datetime.utcnow() + timedelta(hours=int(guild_tz))).strftime("%d-%m-%Y %H:%M:%S"), True),
					  (Lang["mu_operator"], entry.user.mention,False)]
	
			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)
			if Unban == "on" and memberchannel is not None:
				await memberchannel.send(embed=embed)

####??湔 (頨怠?蝯蝔?
	@commands.Cog.listener()
	async def on_member_update(self, before: str, after: str):
		globalmsg = self.bot.get_channel(739986227964543126)
		globalupdate = self.bot.get_channel(739986122297442375)
		testmsg = self.bot.get_channel(737830510952185878)
		if before.display_name != after.display_name:
			data = get_guild_settings(before.guild.id)
			Lang = data_Check_language(data)
			Guild_ID = data.get('ID')
			Member_ID = data.get('member_log_id')
			if Member_ID == None:
					return
			log = get_log_settings(before.guild.id)
			memberchannel = self.bot.get_channel(Member_ID)
			Nick = log.get('MemberUpdate')
			async for entry in before.guild.audit_logs(limit=1):
				icon_user = after.avatar or after.default_avatar
				action_user = entry.user.avatar or entry.user.default_avatar
				embed = Embed(description=Lang["mu_nick_update"].format(after.mention),
							  colour=after.colour,
							  timestamp=datetime.utcnow())
	
				embed.set_author(name=f"{after.name}#{after.discriminator} ({after.display_name})",icon_url=(icon_user.url))
	
				fields = [(Lang["mu_nick_before"], before.display_name, False),
						  (Lang["mu_nick_after"], after.display_name, False)]
				embed.set_footer(icon_url=(action_user.url),text=f'{entry.user}')

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				if Nick == "on" and memberchannel is not None: #din
						await memberchannel.send(embed=embed)

		#頨怠?蝯???		elif before.roles != after.roles:
			data = get_guild_settings(before.guild.id)
			Lang = data_Check_language(data)
			Guild_ID = data.get('ID')
			Member_ID = data.get('member_log_id')
			if Member_ID == None:
					return
			log = get_log_settings(before.guild.id)
			Role = log.get('MemberUpdate')
			memberchannel = self.bot.get_channel(Member_ID)
			async for entry in before.guild.audit_logs(limit=1):
				if entry.action == discord.AuditLogAction.member_role_update:
					icon_user = after.avatar or after.default_avatar
					action_user = entry.user.avatar or entry.user.default_avatar
					embed = Embed(description=Lang["mu_role_update"].format(after.mention),
								  colour=after.colour,
								  timestamp=datetime.utcnow())
					if len(after.roles) > len(before.roles):
						arole = entry.changes.after.roles[0]
						fields = [(Lang["mu_role_add"], f"{arole}", False)]
					else:
						drole = entry.changes.before.roles[0]
						fields = [(Lang["mu_role_del"], f"{drole}", False)]					
		
					embed.set_author(name=f"{after.name}#{after.discriminator} ({after.display_name})",icon_url=(icon_user.url))
					embed.set_footer(icon_url=(action_user.url),text=f'{entry.user}')
	
					for name, value, inline in fields:
						embed.add_field(name=name, value=value, inline=inline)
					if Role == "on" and memberchannel is not None:
						if before.guild == self.bot.get_guild(Guild_ID): #din
							await memberchannel.send(embed=embed)

#####??
	@commands.Cog.listener()
	async def on_message_edit(self, before: str, after: str):
		globalmsg = self.bot.get_channel(739986227964543126)
		testmsg = self.bot.get_channel(737830510952185878)
		action_user = self.bot.user.avatar.url
		if not after.author.bot:
			data = get_guild_settings(before.guild.id)
			Guild_ID = data.get('ID')
			Msg_ID = data.get('message_log_id')
			ignore_list = data.get('ignore_channel')
			log = get_log_settings(before.guild.id)
			Edit = log.get('messageUpdate')
			if before.content != after.content and Msg_ID != None:
				msgchannel = self.bot.get_channel(Msg_ID)
				icon_user = after.author.avatar or after.author.default_avatar
				embed = Embed(description=f"message edit in {after.channel.mention} ",
							  colour=after.author.colour,
							  timestamp=datetime.utcnow())

				embed.set_author(name=f"{after.author.name}#{after.author.discriminator} ({after.author.display_name})",icon_url=(icon_user.url))
				embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
	
				fields = [("old", before.content, False),
						  ("new", after.content, False)]

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				if Edit == "on" and msgchannel is not None and str(after.channel.id) not in ignore_list:
					if before.guild == self.bot.get_guild(Guild_ID): #din
						await msgchannel.send(embed=embed)
	@commands.Cog.listener()
	async def on_message_delete(self, message: str):
		globalmsg = self.bot.get_channel(739986227964543126)
		testmsg = self.bot.get_channel(737830510952185878)
		action_user = self.bot.user.avatar.url
		data = get_guild_settings(message.guild.id)
		Guild_ID = data.get('ID')
		Msg_ID = data.get('message_log_id')
		ignore_list = data.get('ignore_channel')
		log = get_log_settings(message.guild.id)
		Del = log.get('messageDelete')
		if Msg_ID == None:
			return
		msgchannel = self.bot.get_channel(Msg_ID)
		counter = 1 
		global delete_count
		global last_audit_log_id
		deleter = message.author
		async for entry in message.guild.audit_logs(limit=1):
			if entry.action == discord.AuditLogAction.message_delete: #
				if entry.extra.channel == message.channel:
					if entry.target == message.author:
						if (entry.extra.count - delete_count) != 0 or entry.id != last_audit_log_id:
							last_audit_log_id = entry.id
							delete_count = entry.extra.count
							deleter = entry.user.mention
						else:
							deleter = message.author.mention
					else:
						deleter = message.author.mention
				else:
					deleter = message.author.mention
			else:
				deleter = message.author.mention
		if message.attachments and len(message.attachments) >= 1 and counter == 1:
			icon_user = message.author.avatar or message.author.default_avatar
			embed = Embed(description=f"message deleted in {message.channel.mention} ",
						  colour=message.author.colour,
						  timestamp=datetime.utcnow())
			embed.set_thumbnail(url=f"{message.author.avatar.url}.png")
			embed.set_image(url=message.attachments[0].url)
			embed.set_author(name=f"{message.author.name}#{message.author.discriminator} ({message.author.display_name})",icon_url=(icon_user.url))
			embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
			
			if not message.content:
				fields = [("Delete By", deleter, False),
						  ("Image", message.attachments[0].url, False)]
						  
			elif message.content: 
				fields = [("Content", message.content, True),
						  ("Delete By", deleter, False),
						  ("Image", message.attachments[0].url, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if Del == "on" and msgchannel is not None and str(message.channel.id) not in ignore_list:
				if message.guild == self.bot.get_guild(Guild_ID): #din
					await msgchannel.send(embed=embed)
					counter += 1

		elif not message.author.bot and counter == 1:
			a = re.findall(r"(?P<url>https?://[^\s]+)", message.content)
			b = 'jpg','png','gif'
			if len(a) >= 1:
				for x in range(len(a)):
					if 'jpg' in a[x-1].lower() or 'png' in a[x-1].lower() or 'gif' in a[x-1].lower():
							icon_user = message.author.avatar or message.author.default_avatar
							embed = Embed(description=f"message deleted in {message.channel.mention} ",
										  colour=message.author.colour,
										  timestamp=datetime.utcnow())
							
							embed.set_image(url=a[x-1])
							embed.set_author(name=f"{message.author.name}#{message.author.discriminator} ({message.author.display_name})",icon_url=(icon_user.url))
							embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
				
							fields = [("Content", message.content, False),
									  ("Delete By", deleter, False)
									 ]
				
							for name, value, inline in fields:
								embed.add_field(name=name, value=value, inline=inline)
					else:
						icon_user = message.author.avatar or message.author.default_avatar
						embed = Embed(description=f"message deleted in {message.channel.mention} ",
									  colour=message.author.colour,
									  timestamp=datetime.utcnow())
						
						embed.set_author(name=f"{message.author.name}#{message.author.discriminator} ({message.author.display_name})",icon_url=(icon_user.url))
						embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
			
						fields = [("Content", message.content, False),
								  ("Delete By", deleter, False)
								 ]
			
						for name, value, inline in fields:
							embed.add_field(name=name, value=value, inline=inline)
					if Del == "on" and msgchannel is not None and str(message.channel.id) not in ignore_list:
						if message.guild == self.bot.get_guild(Guild_ID): #din
							await msgchannel.send(embed=embed)
							counter += 1
						
			else:
				icon_user = message.author.avatar or message.author.default_avatar
				embed = Embed(description=f"message deleted in {message.channel.mention} ",
							  colour=message.author.colour,
							  timestamp=datetime.utcnow())
				
				embed.set_author(name=f"{message.author.name}#{message.author.discriminator} ({message.author.display_name})",icon_url=(icon_user.url))
				embed.set_footer(icon_url=(action_user),text=f'{self.bot.user}')
	
				fields = [("Content", message.content, False),
						  ("Delete By", deleter, False)
						 ]
	
				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				if Del == "on" and msgchannel is not None and str(message.channel.id) not in ignore_list:
					if message.guild == self.bot.get_guild(Guild_ID): #din
						await msgchannel.send(embed=embed)
						counter += 1

#####隤
	@commands.Cog.listener()
	async def on_voice_state_update(self, member: discord.Member, before: str, after: str):
		timestr = "%d-%m-%Y %H:%M:%S"
		data = get_guild_settings(member.guild.id)
		Guild_ID = data.get('ID')
		Voice_ID = data.get('voice_log_id')
		guild_tz = data.get('TimeZone')
		voicechannel = self.bot.get_channel(Voice_ID)
		log = get_log_settings(member.guild.id)
		Join = log.get('voiceChannelJoin')
		Leave = log.get('voiceChannelLeave')
		Update = log.get('voiceStateUpdate')
		Switch = log.get('voiceChannelSwitch')
		dt_format = (datetime.utcnow() + timedelta(hours=int(guild_tz))).strftime(timestr)
		if member.bot:
			return

		def _calc_hours_from_session(session):
			if not session:
				return None
			join_value = session.get("Join")
			leave_value = session.get("Leave")
			if not join_value or not leave_value:
				return None
			try:
				return round((datetime.strptime(leave_value, timestr) - datetime.strptime(join_value, timestr)).seconds / 3600, 1)
			except Exception:
				return None

		if not before.channel and after.channel:
			upsert_user_voice_join(member.id, after.channel.guild.id, after.channel.id, dt_format)
			if Join == "on" and voicechannel is not None:
				await voicechannel.send(f"> {dt_format} < **{member.name}** joined __{after.channel.name}__")

		if before.channel and not after.channel:
			upsert_user_voice_leave(member.id, before.channel.guild.id, before.channel.id, dt_format)
			session = get_user_voice_channel_stats(member.id, before.channel.guild.id, before.channel.id)
			hours = _calc_hours_from_session(session)
			if hours is not None:
				add_user_voice_total_hours(member.id, before.channel.guild.id, hours)
			if Leave == "on" and voicechannel is not None:
				await voicechannel.send(f"> {dt_format} < **{member.name}** left __{before.channel.name}__")
			
		if before.channel and after.channel:
			if before.channel.id != after.channel.id:
				upsert_user_voice_leave(member.id, before.channel.guild.id, before.channel.id, dt_format)
				session = get_user_voice_channel_stats(member.id, before.channel.guild.id, before.channel.id)
				hours = _calc_hours_from_session(session)
				if hours is not None:
					add_user_voice_total_hours(member.id, before.channel.guild.id, hours)
				upsert_user_voice_join(member.id, after.channel.guild.id, after.channel.id, dt_format)
				if Join == "on" and voicechannel is not None:
					await voicechannel.send(
						f"> {dt_format} < **{member.name}** moved from __{before.channel.name}__ to __{after.channel.name}__"
					)
			else:
				if Update == "on" and voicechannel is not None:
					#if member.voice.self_stream:
					#	await susu_voice_log.send(f"> {timestr} < **{member.name}** streaming at __{before.channel.name}__ ?")
					#	self.current_streamers.append(member.id)
					if before.self_stream == False and after.self_stream != False:
						await voicechannel.send(f"> {dt_format} < **{member.name}** streaming at __{before.channel.name}__ ?")
						upsert_stream_start(member.id, before.channel.guild.id, dt_format)
					elif before.self_stream == True and after.self_stream != True:
						await voicechannel.send(f"> {dt_format} < **{member.name}** stopped streaming")
						upsert_stream_end(member.id, before.channel.guild.id, dt_format)
						stats = get_user_guild_stats(member.id, before.channel.guild.id)
						start = stats.get("stream_start_time")
						end = stats.get("stream_end_time")
						if start and end:
							stream_total = (datetime.strptime(end, timestr) - datetime.strptime(start, timestr)).seconds
							add_stream_total_seconds(member.id, before.channel.guild.id, stream_total)
					elif before.self_mute == False and after.self_mute != False:
						await voicechannel.send(f"> {dt_format} < **{member.name}** muted")
					elif before.self_mute == True and after.self_mute != True:
						await voicechannel.send(f"> {dt_format} < **{member.name}** unmuted")
					elif before.self_deaf == False and after.self_deaf != False:
						await voicechannel.send(f"> {dt_format} < **{member.name}** deafened")
					elif before.self_deaf == True and after.self_deaf != True:
						await voicechannel.send(f"> {dt_format} < **{member.name}** undeafened")
					#else:
					#	for streamer in self.current_streamers:
					#		if member.id == streamer:
					#			if not member.voice.self_stream:
					#				await susu_voice_log.send(f"> {timestr} < **{member.name}** stopped streaming")
					#				self.current_streamers.remove(member.id)
					#			break
		if member.guild.id == 563946360424890368:
			voicechannel = self.bot.get_channel(793848940793561105)
			if not before.channel and after.channel:
				await voicechannel.send(f"> {dt_format} < **{member.name}** joined __{after.channel.name}__")

			if before.channel and not after.channel:
				await voicechannel.send(f"> {dt_format} < **{member.name}** left __{before.channel.name}__")

			if before.channel and after.channel:
				if before.channel.id != after.channel.id:
					await voicechannel.send(
						f"> {dt_format} < **{member.name}** moved from __{before.channel.name}__ to __{after.channel.name}__"
					)
				else:
					if before.self_stream == False and after.self_stream != False:
						await voicechannel.send(f"> {dt_format} < **{member.name}** streaming at __{before.channel.name}__ ?")
					elif before.self_stream == True and after.self_stream != True:
						await voicechannel.send(f"> {dt_format} < **{member.name}** stopped streaming")
					elif before.self_mute == False and after.self_mute != False:
						await voicechannel.send(f"> {dt_format} < **{member.name}** muted")
					elif before.self_mute == True and after.self_mute != True:
						await voicechannel.send(f"> {dt_format} < **{member.name}** unmuted")
					elif before.self_deaf == False and after.self_deaf != False:
						await voicechannel.send(f"> {dt_format} < **{member.name}** deafened")
					elif before.self_deaf == True and after.self_deaf != True:
						await voicechannel.send(f"> {dt_format} < **{member.name}** undeafened")


#####??霈
	#@commands.Cog.listener()
	#async def on_user_update(self, before, after):
	#	if before.name != after.name:
	#		embed = Embed(title="??霈",
	#					  colour=after.colour,
	#					  timestamp=datetime.utcnow())

	#		fields = [("old", before.name, False),
	#				  ("new", after.name, False)]

	#		for name, value, inline in fields:
	#			embed.add_field(name=name, value=value, inline=inline)

	#		await userchannel.send(embed=embed)
	#	if before.discriminator != after.discriminator:
	#		embed = Embed(title="Discriminator change",
	#					  colour=after.colour,
	#					  timestamp=datetime.utcnow())

	#		fields = [("Before", before.discriminator, False),
	#				  ("After", after.discriminator, False)]

	#		for name, value, inline in fields:
	#			embed.add_field(name=name, value=value, inline=inline)

	#		await channel.send(embed=embed)
	#	if before.avatar.url != after.avatar.url:
	#		embed = Embed(title="?剛票霈",
	#					  description="銝?舀???喲??航???",
	#					  colour=after.colour,
	#					  timestamp=datetime.utcnow())

	#		embed.set_thumbnail(url=before.avatar.url)
	#		embed.set_image(url=after.avatar.url)

	#		await channel.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Log(bot))




