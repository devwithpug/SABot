import discord
import asyncio
import os
from discord.ext import commands

#Get Token
token_path = os.path.dirname(os.path.abspath(__file__)) + "/.token"
t = open(token_path, "r", encoding="utf-8")
token = t.read().split()[0]
print("Token_Key : ", token)

#Bot Settings
game = discord.Game("상태창 메세지")
bot = commands.Bot(command_prefix = "!", status = discord.Status.online, activity = game)

#Bot events
@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None and after.channel is member.guild.afk_channel:
        embed = discord.Embed(title = member.name + " 님이 " + after.channel.name + " 보이스 채널에 접속했습니다.")
        await member.guild.system_channel.send(embed = embed)
    if after.channel is not None and after.channel is member.guild.afk_channel:
        embed = discord.Embed(title = member.name + " 님이 개인적인 시간을 보내러 갔어요. ㅎㅎ;")
        await member.guild.system_channel.send(embed = embed)

#Bot commands
@bot.command()
async def joined(ctx, *, member: discord.VoiceChannel):
    await ctx.send("{0} joined on {0.joined_at}".format(member))
@bot.command()
async def debug(ctx):
    embed = discord.Embed()
    embed.set_author(name = ctx.guild.name+" Member list")
    embed.set_thumbnail(url=ctx.guild.icon_url)
    value = str()
    for member in ctx.guild.members:
        if member.nick:
            value += member.name + " / " + member.nick + "\n"
        else:
            value += member.name + " / " + "None" + "\n"
    embed.add_field(name = "Name / Nickname", value = value, inline = False)
    await ctx.send(embed = embed)
@bot.command()
async def hello(ctx):
    await ctx.send("hiiiiii")
@bot.command()
async def 엔딩곡(ctx):
    for channel in ctx.guild.text_channels:
        if channel.name == "노래":
            await channel.send(content = '_play 용과같이 바보같이')
            await ctx.send('_play 용과같이 바보같이')
    
bot.run(token)
