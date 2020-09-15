import discord
import asyncio
import os
import requests
import time
import watcher
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
# Get Token
token_path = os.path.dirname(os.path.abspath(__file__)) + "/.token"
with open(token_path, "r", encoding="utf-8") as t:
    token = t.read().split()[0]
print("Token_Key : ", token)
t.close()

# Bot Settings
game = discord.Game("!command")
prefix = '!'
bot = commands.Bot(command_prefix=prefix,
                   status=discord.Status.online, activity=game)
wt = watcher.watcher()


# Bot events


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    wt.init_summoner_list(bot.guilds)
    live_game_tracker.start()


@bot.event
async def on_guild_join(guild):
    print("SAbot joined at {} ({})".format(guild.name, guild.id))
    await guild.system_channel.send(embed=discord.Embed(title="SABot is now ONLINE =D"))
    wt.init_summoner_list(bot.guilds)
    print("[Live_game_tracker]Restart live_game_tracker")
    live_game_tracker.restart()


@bot.event
async def on_guild_remove(guild):
    print("SAbot removed at {} ({})".format(guild.name, guild.id))
    path = os.path.dirname(os.path.abspath(__file__)) + \
        "/.summoner_list_" + str(guild.id)
    os.remove(path)
    print("{} was removed.".format(path))
    print("[Live_game_tracker]Restart live_game_tracker")
    live_game_tracker.restart()


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None and after.channel is not member.guild.afk_channel:
        if member.nick is not None:
            embed = discord.Embed(title=member.nick + " 님이 " +
                                  after.channel.name + " 보이스 채널에 접속했습니다.")
        else:
            embed = discord.Embed(title=member.name + " 님이 " +
                                  after.channel.name + " 보이스 채널에 접속했습니다.")
        await member.guild.system_channel.send(embed=embed)
    if after.channel is member.guild.afk_channel:
        if member.nick is not None:
            embed = discord.Embed(title=member.nick +
                                  " 님이 개인적인 시간을 보내러 갔어요. ㅎㅎ;")
        else:
            embed = discord.Embed(title=member.name +
                                  " 님이 개인적인 시간을 보내러 갔어요. ㅎㅎ;")
        await member.guild.system_channel.send(embed=embed)

# Bot commands


@bot.command()
async def alarm(ctx):

    await ctx.send(embed=discord.Embed(title="(d) : Day, (h) : Hour, (m) : Minute").set_author(name="알람) 타입 설정"))

    def check_type(m):
        return m.content == 'd' or m.content == 'h' or m.content == 'm' and m.channel == ctx.channel

    def check_value(m):
        return is_int(m.content) and m.channel == ctx.channel

    def check_confirm(m):
        return m.content == 'y' or m.content == 'n' and m.channel == ctx.channel

    try:
        alarm_type = await bot.wait_for('message', timeout=30.0, check=check_type)
    except asyncio.TimeoutError:
        await ctx.send(embed=discord.Embed(title="Timeout : Try again."))
        return

    await ctx.send(embed=discord.Embed(title="희망하는 숫자를 입력하시오").set_author(name="알람) 시간 설정"))

    try:
        alarm_value = await bot.wait_for('message', timeout=30.0, check=check_value)
    except asyncio.TimeoutError:
        await ctx.send(embed=discord.Embed(title="Timeout : Try again."))
        return

    await ctx.send(embed=discord.Embed(title="(y) : 확인, (n) : 취소").set_author(name="알람) {} {} 후에 알림".format(alarm_value.content, alarm_type.content)))

    try:
        alarm_confirm = await bot.wait_for('message', timeout=30.0, check=check_confirm)
    except asyncio.TimeoutError:
        await ctx.send(embed=discord.Embed(title="Timeout : Try again."))
        return

    if alarm_confirm.content == 'n':
        await ctx.send(embed=discord.Embed(title="Alarm canceled"))
        return

    await alarm_init(ctx, alarm_type.content, int(alarm_value.content))


@bot.command()
async def command(ctx):
    await ctx.send(embed=discord.Embed(title="Check available commands : https://github.com/Jungyu-Choi/SABot"))


@bot.command()
async def users(ctx):
    embed = discord.Embed()
    embed.set_author(name=ctx.guild.name+" Member list")
    embed.set_thumbnail(url=ctx.guild.icon_url)
    value = str()
    for member in ctx.guild.members:
        if member.nick:
            value += member.name + " / " + member.nick + "\n"
        else:
            value += member.name + " / " + "None" + "\n"
    embed.add_field(name="Name / Nickname", value=value, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def l(ctx, *args):

    if args[0] == 'nick' and len(args) > 1:
        name = " ".join(args[1:])
        req = requests.get('https://www.op.gg/summoner/userName=' + name)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        tmp = str(soup.find_all('meta', {'name': 'description'}))
        result = tmp[tmp.find('="')+2:tmp.find('" name')].split(' / ')

        if len(result) < 4:
            await ctx.send(embed=discord.Embed(title="등록되지 않은 소환사입니다. 오타를 확인 후 다시 검색해주세요."))
            return

        embed = discord.Embed()
        embed.set_author(name=result[0])
        embed.add_field(name=result[1]+" / "+result[2], value=result[3])

        await ctx.send(embed=embed)

    elif args[0] == 'currentGame' and len(args) > 1:
        name = " ".join(args[1:])
        await ctx.send(content=preview_current_game(name))

    elif args[0] == 'add' and len(args) > 1:
        name = " ".join(args[1:])
        d = wt.edit_summoner_list(str(ctx.guild.id), True, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == 'remove' and len(args) > 1:
        name = " ".join(args[1:])
        d = wt.edit_summoner_list(str(ctx.guild.id), False, name)
        await ctx.send(embed=discord.Embed(title=d))

    else:
        await ctx.send(embed=discord.Embed(title="Check available commands : https://github.com/Jungyu-Choi/SABot"))


@tasks.loop(seconds=60.0)
async def live_game_tracker():
    for guild in bot.guilds:
        print("[Live_game_tracker]guild id : ", guild.id)
        print("[Live_game_tracker]live_game is traking... at " +
              time.strftime('%c', time.localtime(time.time())))
        print("[Live_game_tracker]summoner list : ",
              wt.get_summoner_list(str(guild.id)))
        for summonerName in wt.get_summoner_list(str(guild.id)):
            content = preview_current_game(summonerName, str(guild.id))
            if content is not None:
                await guild.system_channel.send(content=content)


def preview_current_game(name, guild_id=None):
    d = wt.live_match(name, guild_id)
    if type(d) is str:
        return d
    elif d is None:
        return
    content = "```ini\n["+str(d[0]['map'])+" | "+d[0]['gameMode']+" | "+str(
        int(d[0]['gameLength']/60))+":"+str(d[0]['gameLength'] % 60)+"]\n"
    content += "Blue Team\n"
    for i in range(0, 5):
        if d[1][i]['tier'] == 'unranked':
            content += d[1][i]['championId']+" | " + \
                d[1][i]['summonerName']+" | "+d[1][i]['tier']+"\n"
        else:
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+" "+d[1][i]['rank'] + \
                " | "+str(d[1][i]['avarage'])+"% | "+str(d[1][i]['wins']) + \
                " wins | "+str(d[1][i]['losses'])+" losses \n"
    content += "Red Team\n"
    for i in range(5, 10):
        if d[1][i]['tier'] == 'unranked':
            content += d[1][i]['championId']+" | " + \
                d[1][i]['summonerName']+" | "+d[1][i]['tier']+"\n"
        else:
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+" "+d[1][i]['rank'] + \
                " | "+str(d[1][i]['avarage'])+"% | "+str(d[1][i]['wins']) + \
                " wins | "+str(d[1][i]['losses'])+" losses \n"
    content += "```"
    return content


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


async def alarm_init(ctx, type, value):
    """Creating a alarm with type, value

    Args:
        ctx (discord.Context): user context
        type (str): d - Day, h - Hour, m - Minute
        value (int): waiting value
    """
    if type == 'd':
        await ctx.send(embed=discord.Embed(title="Alarm set to "+str(value)+" day(s) after."))
        await asyncio.sleep(value*60*60*24)
        await ctx.send(embed=discord.Embed(title="Alarm!!!"))
        await ctx.send(ctx.author.mention)
    elif type == 'h':
        await ctx.send(embed=discord.Embed(title="Alarm set to "+str(value)+" hour(s) after."))
        await asyncio.sleep(value*60*60)
        await ctx.send(embed=discord.Embed(title="Alarm!!!"))
        await ctx.send(ctx.author.mention)
    elif type == 'm':
        await ctx.send(embed=discord.Embed(title="Alarm set to "+str(value)+" minute(s) after."))
        await asyncio.sleep(value*60)
        await ctx.send(embed=discord.Embed(title="Alarm!!!"))
        await ctx.send(ctx.author.mention)
    else:
        await ctx.send("ERROR OCCURED")


def has_nick(author):
    """if user has nickname, return nick ; else return user's name

    Args:
        author (discord.Message.author): Discord user
    """
    if author.nick:
        return author.nick
    else:
        return author.name


bot.run(token)
