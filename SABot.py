import discord
import asyncio
import os
import requests
import time
import watcher
from discord.ext import commands, tasks
from bs4 import BeautifulSoup


class sabot:
    def __init__(self):
        # Get Token
        self.token_path = os.path.dirname(
            os.path.abspath(__file__)) + "/.token"
        with open(self.token_path, "r", encoding="utf-8") as t:
            self.token = t.read().split()[0]
        print("Token_Key : ", self.token)
        t.close()

        # Bot Settings
        self.game = discord.Game("!command")
        self.prefix = '!'
        self.wt = watcher.watcher()
        self.debug = False
        self.lt = {}


'''for guild in guilds:
            self.live_game_tracker_on[guild.id] = True'''

setup = sabot()
bot = commands.Bot(command_prefix=setup.prefix,
                   status=discord.Status.online, activity=setup.game)

# Bot events


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    print("Guild List : {}".format(str(bot.guilds)))
    setup.wt.init_summoner_list(bot.guilds)
    for guild in bot.guilds:
        setup.lt[guild.id] = True
    live_game_tracker.start()


@bot.event
async def on_guild_join(guild):
    print("SAbot joined at {} ({})".format(guild.name, guild.id))
    await guild.system_channel.send(embed=discord.Embed(title="SABot is now ONLINE =D"))
    setup.wt.init_summoner_list(bot.guilds)
    print("[Live_game_tracker]Restart live_game_tracker")
    live_game_tracker.restart()


@bot.event
async def on_guild_remove(guild):
    print("SAbot removed at {} ({})".format(guild.name, guild.id))
    path = os.path.dirname(os.path.abspath(__file__)) + \
        "/.summoner_list_" + str(guild.id)
    os.remove(path)
    print("{} was removed.".format(path))
    setup.wt.init_summoner_list(bot.guilds)
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
    print("[{}, {}] {} : {}".format(time.strftime('%c', time.localtime(
        time.time())), ctx.guild.name, ctx.author, ctx.message.content))

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
    print("[{}, {}] {} : {}".format(time.strftime('%c', time.localtime(
        time.time())), ctx.guild.name, ctx.author, ctx.message.content))
    await ctx.send(embed=discord.Embed(title="Check available commands : https://github.com/Jungyu-Choi/SABot"))


@bot.command()
async def users(ctx):
    print("[{}, {}] {} : {}".format(time.strftime('%c', time.localtime(
        time.time())), ctx.guild.name, ctx.author, ctx.message.content))
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
    print("[{}, {}] {} : {}".format(time.strftime('%c', time.localtime(
        time.time())), ctx.guild.name, ctx.author, ctx.message.content))

    if not args:
        await ctx.send(embed=discord.Embed(title="Check available commands : https://github.com/Jungyu-Choi/SABot"))
        return

    name = " ".join(args[1:])

    if args[0] == 'nick' and len(args) > 1:
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

    elif args[0] == 'match' and len(args) > 1:
        content = preview_current_game(name, lt=False)
        if content is None:
            await ctx.send(embed=discord.Embed(title="{} 님은 현재 게임중이 아닙니다.".format(name)))
            return
        await ctx.send(content=content)

    elif args[0] == 'add' and len(args) > 1:
        d = setup.wt.edit_summoner_list(str(ctx.guild.id), True, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == 'remove' and len(args) > 1:
        d = setup.wt.edit_summoner_list(str(ctx.guild.id), False, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == 'start' and len(args) > 0:
        setup.wt.init_riot_api()

        if setup.lt[ctx.guild.id] is True:
            await ctx.send(embed=discord.Embed(title="Live-game tracker is already working."))
            return
        elif setup.wt.riot_api_status() == 403:
            await ctx.send(embed=discord.Embed(title="Couldn't start Live-game tracker. Invaild Riot API key."))
            return
        try:
            live_game_tracker.start()
        except RuntimeError:
            live_game_tracker.restart()

        setup.lt[ctx.guild.id] = True
        print("[{}] [Live_game_tracker] {} live_game_tracker was started. ".format(
            time.strftime('%c', time.localtime(time.time())), ctx.guild.name))
        await ctx.send(embed=discord.Embed(title="Live-game tracker was started."))

    elif args[0] == 'stop' and len(args) > 0:
        if setup.lt[ctx.guild.id] is False:
            await ctx.send(embed=discord.Embed(title="Live-game tracker was already stopped."))
            return
        setup.lt[ctx.guild.id] = False
        print("[{}] [Live_game_tracker] {} live_game_tracker was stopped. ".format(
            time.strftime('%c', time.localtime(time.time())), ctx.guild.name))
        await ctx.send(embed=discord.Embed(title="Live-game tracker was stopped."))

    elif args[0] == 'list' and len(args) > 0:
        names = ''
        for name in setup.wt.get_summoner_list(ctx.guild.id):
            names += name
        await ctx.send(embed=discord.Embed(title="Live-game tracker Users", description=names))

    else:
        await ctx.send(embed=discord.Embed(title="Check available commands : https://github.com/Jungyu-Choi/SABot"))


@tasks.loop(seconds=60.0)
async def live_game_tracker():
    if setup.wt.riot_api_status() == 403:
        print("[{}] [Live_game_tracker] error 403 Forbidden : Check your riot_api_key !!!".format(
            time.strftime('%c', time.localtime(time.time()))))

        for guild in bot.guilds:
            await guild.system_channel.send(embed=discord.Embed(title="Riot API has expired. Live-game tracker will stopped until fixes."))
            await guild.system_channel.send(embed=discord.Embed(title="Live-game tracker was stopped."))
            setup.lt[guild.id] = False

        live_game_tracker.stop()

        print("[{}] [Live_game_tracker] live_game_tracker was stopped. ".format(
            time.strftime('%c', time.localtime(time.time()))))
        return

    for guild in bot.guilds:
        if setup.lt[guild.id] is False:
            continue
        setup.wt.is_match_ended(guild)
        for summonerName in setup.wt.get_summoner_list(str(guild.id)):
            content = preview_current_game(
                summonerName.rstrip('\n'), guild)
            if type(content) is str:
                await guild.system_channel.send(content=content)


def preview_current_game(name, guild=None, lt=True):
    d = setup.wt.live_match(name, guild, lt)
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
                " | "+str(d[1][i]['avarage'])+"% | "+str(d[1][i]['wins']
                                                         ) + " wins | "+str(d[1][i]['losses'])+" losses \n"
    content += "Red Team\n"
    for i in range(5, 10):
        if d[1][i]['tier'] == 'unranked':
            content += d[1][i]['championId']+" | " + \
                d[1][i]['summonerName']+" | "+d[1][i]['tier']+"\n"
        else:
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+" "+d[1][i]['rank'] + \
                " | "+str(d[1][i]['avarage'])+"% | "+str(d[1][i]['wins']
                                                         ) + " wins | "+str(d[1][i]['losses'])+" losses \n"
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


bot.run(setup.token)
