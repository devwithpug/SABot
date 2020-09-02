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

#Bot initialization
@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    await ctx.send("logged in")
@bot.command()
async def joined(ctx, *, member: discord.VoiceChannel):
    await ctx.send("{0} joined on {0.joined_at}".format(member))
@bot.command()
async def test(ctx):
    await ctx.send("hello")
@bot.command()
async def hello(ctx):
    await ctx.send("hiiiiii")

bot.run(token)
