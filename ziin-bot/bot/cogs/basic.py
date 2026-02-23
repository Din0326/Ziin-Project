import datetime
import random
import time
from datetime import datetime, timedelta
#from gtts import gTTS
#from requests import get
from typing import Optional

import discord
import requests
from bot.core.classed import Cog_Extension
from bot.utils.i18n import t_ctx
from discord import Embed, Role
from discord.ext import commands
from discord.utils import get

#from googletrans import Translator




delete_count = 0
last_audit_log_id = 0
api_key = "5e5231bc30957e7119295f62b8e290ec"
base_url = "http://api.openweathermap.org/data/2.5/weather?"


class Basic(Cog_Extension):
	@commands.hybrid_command(aliases=['slots', 'bet'], with_app_command=True)
	@commands.cooldown(1,30,commands.BucketType.user)
	async def slot(self, ctx: commands.Context):
		""" Roll the slot machine """
		emojis = "????????????????"
		a = random.choice(emojis)
		b = random.choice(emojis)
		c = random.choice(emojis)

		slotmachine = f"**[ {a} {b} {c} ]\n{ctx.author.name}**,"

		if a == b == c:
			await ctx.send(t_ctx(ctx, "slot_win3", slotmachine))
		elif (a == b) or (a == c) or (b == c):
			await ctx.send(t_ctx(ctx, "slot_win2", slotmachine))
		else:
			await ctx.send(t_ctx(ctx, "slot_lose", slotmachine))

			
	@commands.hybrid_command(aliases=['rm','getrolemember'], with_app_command=True)
	async def rolemember(self, ctx: commands.Context, target: Optional[Role]):
		target = target or ctx.author.top_role
		in_role_member = []

		for i in range(len(target.members)):
			in_role_member.append(target.members[i].mention)
		ans = ','.join(in_role_member)

		embed = Embed(title="Role Members",
					  colour=target.colour,
					  timestamp=datetime.utcnow())
	
		fields = [("Name", target, True),
				  ("Total", len(target.members),True),
				  ("Member",ans,False)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)
		
	@commands.hybrid_command(with_app_command=True)
	async def ping(self, ctx: commands.Context):
		await ctx.send(t_ctx(ctx, "ping", round(self.bot.latency * 1000)))

	@commands.hybrid_command(aliases=["tc"], with_app_command=True)
	async def converter(self, ctx: commands.Context, *, args: str):
		#if args.split(f"\n")[0] != :
		#	return
		gmttime = eval(args.split(f"\n")[0])
		if gmttime >= 0:
			des = f"+{gmttime}"
		else:
			des = gmttime
		embed = Embed(title="Time Converter",
					description=f"Convert from UTC{des}",
					colour=ctx.author.colour,
					timestamp=datetime.utcnow())
		for i in range(len(args.split(f"\n")) - 1):
			if args.split(f"\n")[0] > "0":
				tran_time = datetime.strptime(args.split(f"\n")[1+i], "%Y-%m-%d %H:%M:%S") + timedelta(hours=int(gmttime))
			elif args.split(f"\n")[0] < "0":
				tran_time = datetime.strptime(args.split(f"\n")[1+i], "%Y-%m-%d %H:%M:%S") - timedelta(hours=int(args.split(f"\n")[0][1:]))
			elif args.split(f"\n")[0] == "0":
				tran_time = datetime.strptime(args.split("\n",1)[1+i], "%Y-%m-%d %H:%M:%S")
			unix_time = time.mktime(tran_time.timetuple())
			embed.add_field(name=str(args.split(f"\n")[1+i]),value=f"unix > `{str(int(unix_time))}`",inline=True)
		await ctx.send(embed=embed)



	@commands.hybrid_command(hidden=True, with_app_command=True)
	async def tran(self, ctx: commands.Context, *, args: str):
		#translator = Translator()
		#await ctx.send(translator)
		#entts = (translator.translate(msg, dest='en').text)
		#await ctx.send("1")
		#await ctx.send(ctx.guild.default_role.mention)
		gmt = args.split(" ")[0][1:] if int(args.split(" ")[0]) <= 0 else args.split(" ")[0]
		tt = args.split(" ",1)[1]
		if gmt != "0":
			tran_time = datetime.strptime(args.split(" ",1)[1], "%Y-%m-%d %H:%M:%S") - timedelta(hours=int(gmt))
		else:
			tran_time = datetime.strptime(args.split(" ",1)[1], "%Y-%m-%d %H:%M:%S")
		unix_time = time.mktime(tran_time.timetuple())
		#await ctx.send(type(unix_time))
		await ctx.send(f"<t:{int(unix_time)}:F>")
			

	@commands.hybrid_command(with_app_command=True)
	async def echo(self, ctx: commands.Context, *, msg: str):
		await ctx.message.delete()
		await ctx.channel.send(msg)

	@commands.hybrid_command(with_app_command=True)
	async def pick(self, ctx: commands.Context, *, args: str):
		answer = random.choice((args.split(' ')))
		await ctx.send(answer)

	@commands.hybrid_command(with_app_command=True)
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
			voice = await channel.connect()
			print(f"The bot has connected to {channel}\n")
	
	@commands.hybrid_command(with_app_command=True)
	async def leave(self, ctx: commands.Context):
		channel = ctx.message.author.voice.channel
		voice = get(self.bot.voice_clients, guild=ctx.guild)
	
		if voice and voice.is_connected():
			await voice.disconnect()
			print(f"The bot has left {channel}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Basic(bot))
