import discord, asyncio, os, requests, time
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
import watcher
#Get Token
token_path = os.path.dirname(os.path.abspath(__file__)) + "/.token"
t = open(token_path, "r", encoding="utf-8")
token = t.read().split()[0]
print("Token_Key : ", token)

#Bot Settings
game = discord.Game("상태창 메세지")
prefix = '!'
bot = commands.Bot(command_prefix = prefix, status = discord.Status.online, activity = game)
wt = watcher.watcher()

#Bot events
@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    bot.loop.create_task(live_game_tracker())
    
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None and after.channel is not member.guild.afk_channel:
        embed = discord.Embed(title = member.name + " 님이 " + after.channel.name + " 보이스 채널에 접속했습니다.")
        await member.guild.system_channel.send(embed = embed)
    if after.channel is member.guild.afk_channel:
        embed = discord.Embed(title = member.name + " 님이 개인적인 시간을 보내러 갔어요. ㅎㅎ;")
        await member.guild.system_channel.send(embed = embed)

#Bot commands
@bot.command()
async def joined(ctx, *, member: discord.VoiceChannel):
    await ctx.send("{0} joined on {0.joined_at}".format(member))
@bot.command()
async def users(ctx):
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
async def l(ctx):
    args = ctx.message.content[len(prefix+"l "):].split(' ')
    name = ' '.join(args[1:len(args)])
    if args[0] == 'nick' and len(args) > 1:
        req = requests.get('https://www.op.gg/summoner/userName=' + name)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        tmp = str(soup.find_all('meta', {'name': 'description'}))
        result = tmp[tmp.find('="')+2:tmp.find('" name')].split(' / ')
        if len(result) < 4:
            await ctx.send(embed = discord.Embed(title = "등록되지 않은 소환사입니다. 오타를 확인 후 다시 검색해주세요."))
            return
        embed =  discord.Embed()
        embed.set_author(name = result[0])
        embed.add_field(name = result[1]+" / "+result[2], value = result[3])
        await ctx.send(embed = embed)
    elif args[0] == 'currentGame' and len(args) > 1:
        await ctx.send(content = preview_current_game(name))
    elif args[0] == 'add' and len(args) > 1:
        d = wt.edit_summoner_list(True, name)
        await ctx.send(embed = discord.Embed(title = d))
    elif args[0] == 'remove' and len(args) > 1:
        d = wt.edit_summoner_list(False, name)
        await ctx.send(embed = discord.Embed(title = d))
    else:
        await ctx.send(embed = discord.Embed(title = "!l nick [summonerName]\n\
                                                    !l currentGame [summonerName]\n\
                                                    ex) !l nick hide on bush\n\n\
                                                    LOL live-game-tracker\n\
                                                    !l add [summonerName]\n\
                                                    !l remove [summonerName]"))


async def live_game_tracker():
    while True:
        print("live_game is traking... at "+ time.strftime('%c', time.localtime(time.time())))
        print("summoner list : ", wt.get_summoner_list())
        for guild in bot.guilds:
            for summonerName in wt.get_summoner_list():
                content = preview_current_game(summonerName)
                if content is not None:
                    await guild.system_channel.send(content = content)
        await asyncio.sleep(60)

def preview_current_game(name):
    d = wt.live_match(name)
    if type(d) is str:
        return d
    elif d is None:
        return
    content = "```ini\n["+str(d[0]['map'])+" | "+d[0]['gameMode']+" | "+str(int(d[0]['gameLength']/60))+":"+str(d[0]['gameLength']%60)+"]\n"
    content += "Blue Team\n"
    for i in range(0, 5):
        if d[1][i]['tier'] == 'unranked':
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+"\n"
        else:
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+" "+d[1][i]['rank']+" | "+str(d[1][i]['avarage'])+"% | "+str(d[1][i]['wins'])+" wins | "+str(d[1][i]['losses'])+" losses \n"
    content += "Red Team\n"
    for i in range(5, 10):
        if d[1][i]['tier'] == 'unranked':
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+"\n"
        else:
            content += d[1][i]['championId']+" | "+d[1][i]['summonerName']+" | "+d[1][i]['tier']+" "+d[1][i]['rank']+" | "+str(d[1][i]['avarage'])+"% | "+str(d[1][i]['wins'])+" wins | "+str(d[1][i]['losses'])+" losses \n"
    content += "```"
    return content


bot.run(token)
