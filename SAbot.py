import discord
import asyncio
import os
from discord.ext import commands

#Get token
token_path = os.path.dirname(os.path.abspath(__file__)) + "/.token"
t = open(token_path, "r", encoding="utf-8")
token = t.read().split()[0]
print("Token_Key : ", token)

#Bot Settings
token = "NzQ5NjMyMzExMjA4NzA2MDcz.X0uzfg.5g976c8ed9rTxV4YTUFM0CWTXLs"
game = discord.Game("상태창 메세지")
bot = commands.Bot(command_prefix = "!", status = discord.Status.online, activity = game)

#Bot initialization
@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

@bot.command()
async def test(ctx):
    await ctx.send("hello")

bot.run(token)