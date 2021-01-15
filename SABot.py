import discord, asyncio, os, requests, time
import watcher
from PIL import Image
from io import BytesIO
from discord.ext import commands, tasks
from bs4 import BeautifulSoup


class sabot:
    def __init__(self):
        # Get Token
        self.token_path = os.path.dirname(os.path.abspath(__file__)) + "/.token"
        with open(self.token_path, "r", encoding="utf-8") as t:
            self.token = t.read().split()[0]
        print("Token_Key : ", self.token)
        t.close()

        # Bot Settings
        self.game = discord.Game("!command")
        self.prefix = "!"
        self.wt = watcher.watcher()
        self.lt = {}


setup = sabot()
bot = commands.Bot(
    command_prefix=setup.prefix, status=discord.Status.online, activity=setup.game
)

# Bot events


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    print("Guild List : {}".format(str(bot.guilds)))
    setup.wt.load_summoner_list(bot.guilds)
    for guild in bot.guilds:
        setup.lt[guild.id] = True
    live_game_tracker.start()


@bot.event
async def on_guild_join(guild):
    print(
        "[{}]SAbot joined at {} ({})".format(
            time.strftime("%c", time.localtime(time.time())), guild.name, guild.id
        )
    )
    setup.wt.load_summoner_list(bot.guilds)
    setup.lt[guild.id] = False
    try:
        await guild.system_channel.send(
            embed=discord.Embed(title="SABot is now ONLINE =D")
        )
    except discord.errors.Forbidden:
        print("(error code: 50013): Missing Permissions")
        await guild.leave()
        return
    print("[Live_game_tracker]Restart live_game_tracker")
    live_game_tracker.restart()


@bot.event
async def on_guild_remove(guild):
    print(
        "[{}]SAbot removed at {} ({})".format(
            time.strftime("%c", time.localtime(time.time())), guild.name, guild.id
        )
    )
    setup.wt.delete_guild(guild.id)
    setup.wt.load_summoner_list(bot.guilds)
    del setup.lt[guild.id]
    print("[Live_game_tracker]Restart live_game_tracker")
    live_game_tracker.restart()


# Bot commands


@bot.command()
async def debug_leave_all_guilds(ctx):
    if ctx.author.id == 279204767472025600:
        for guild in bot.guilds:
            await guild.leave()


@bot.command()
async def command(ctx):
    print(
        "[{}, {}] {} : {}".format(
            time.strftime("%c", time.localtime(time.time())),
            ctx.guild.name,
            ctx.author,
            ctx.message.content,
        )
    )
    await ctx.send(
        embed=discord.Embed(
            title="Check available commands : https://github.com/Jungyu-Choi/SABot"
        )
    )


@bot.command()
async def l(ctx, *args):
    print(
        "[{}, {}] {} : {}".format(
            time.strftime("%c", time.localtime(time.time())),
            ctx.guild.name,
            ctx.author,
            ctx.message.content,
        )
    )
    if not args:
        await ctx.send(
            embed=discord.Embed(
                title="Check available commands : https://github.com/Jungyu-Choi/SABot"
            )
        )
        return

    if args[0] == "setup" and len(args) > 0:

        def check_confirm(m):
            return m.content == "y" or m.content == "n" and m.channel == ctx.channel

        def select_region(m):
            return (
                m.content == "br1"
                or m.content == "eun1"
                or m.content == "euw1"
                or m.content == "jp1"
                or m.content == "kr"
                or m.content == "la1"
                or m.content == "la2"
                or m.content == "la2"
                or m.content == "na1"
                or m.content == "oc1"
                or m.content == "tr1"
                or m.content == "ru"
                and m.channel == ctx.channel
            )

        if setup.wt.is_setup_already(ctx.guild):
            await ctx.send(
                embed=discord.Embed(
                    title="Your discord server was already setup. Would you like to reset it?",
                    description="'y' : Yes 'n' : No",
                ).set_author(name="Live tracker Setup")
            )
            try:
                confirm = await bot.wait_for(
                    "message", timeout=30.0, check=check_confirm
                )
            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(title="Timeout : Try again."))
                return
            if confirm.content == "n":
                return
            setup.wt.delete_guild(ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(
                title="Choose your League Of Legends region",
                description="'br1', 'eun1', 'euw1', 'jp1', 'kr', 'la1', 'la2', 'na1', 'oc1', 'tr1', 'ru'",
            ).set_author(name="Live tracker Setup")
        )
        try:
            region = await bot.wait_for("message", timeout=30.0, check=select_region)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title="Timeout : Try again."))
            return
        await ctx.send(
            embed=discord.Embed(
                title="Confirm this setup?",
                description="region : " + region.content + "\n'y' : Yes 'n' : No",
            ).set_author(name="Live tracker Setup")
        )
        try:
            confirm = await bot.wait_for("message", timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title="Timeout : Try again."))
            return
        if confirm.content == "n":
            return

        setup.wt.setup(region.content, ctx.guild)
        setup.wt.load_summoner_list(bot.guilds)
        setup.lt[ctx.guild.id] = True
        try:
            live_game_tracker.start()
        except RuntimeError:
            live_game_tracker.restart()

        await ctx.send(
            embed=discord.Embed(title="Live tracker was setup successfully.")
        )
        return

    if not setup.wt.is_setup_already(ctx.guild):
        await ctx.send(
            embed=discord.Embed(title="'!l setup'").set_author(
                name="You have to setup SABot first!"
            )
        )
        return

    name = " ".join(args[1:])

    if args[0] == "match" and len(args) > 1:
        content = preview_current_game(name, ctx.guild, lt=False)
        if content is None:
            await ctx.send(
                embed=discord.Embed(title="{} is not in the match.".format(name))
            )
            return
        elif content[0] == "403":
            await ctx.send(content=content)
        elif content[0] == "200":
            with BytesIO() as image_binary:
                content[1].save(image_binary, "PNG")
                image_binary.seek(0)
                await ctx.send(file=discord.File(fp=image_binary, filename="image.PNG"))

    elif args[0] == "add" and len(args) > 1:
        d = setup.wt.edit_summoner_list(ctx.guild.id, True, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == "remove" and len(args) > 1:
        d = setup.wt.edit_summoner_list(ctx.guild.id, False, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == "start" and len(args) == 1:
        setup.wt.init_riot_api()

        if setup.lt[ctx.guild.id] is True:
            await ctx.send(
                embed=discord.Embed(title="Live-game tracker is already working.")
            )
            return
        elif setup.wt.riot_api_status() == 403:
            await ctx.send(
                embed=discord.Embed(
                    title="Couldn't start Live-game tracker. Invaild Riot API key."
                )
            )
            return
        try:
            live_game_tracker.start()
        except RuntimeError:
            live_game_tracker.restart()

        setup.lt[ctx.guild.id] = True
        print(
            "[{}] [Live_game_tracker] {} live_game_tracker was started. ".format(
                time.strftime("%c", time.localtime(time.time())), ctx.guild.name
            )
        )
        await ctx.send(embed=discord.Embed(title="Live-game tracker was started."))

    elif args[0] == "stop" and len(args) == 1:
        if setup.lt[ctx.guild.id] is False:
            await ctx.send(
                embed=discord.Embed(title="Live-game tracker was already stopped.")
            )
            return
        setup.lt[ctx.guild.id] = False
        print(
            "[{}] [Live_game_tracker] {} live_game_tracker was stopped. ".format(
                time.strftime("%c", time.localtime(time.time())), ctx.guild.name
            )
        )
        await ctx.send(embed=discord.Embed(title="Live-game tracker was stopped."))

    elif args[0] == "list" and len(args) == 1:
        region = setup.wt.guild_region[ctx.guild.id]
        names = ""
        for name in setup.wt.get_summoner_list(ctx.guild.id):
            names += name
        await ctx.send(
            embed=discord.Embed(
                title="Region : " + region, description=names
            ).set_author(name="Live tracker user list")
        )

    else:
        await ctx.send(
            embed=discord.Embed(
                title="Check available commands : https://github.com/Jungyu-Choi/SABot"
            )
        )


@tasks.loop(seconds=60.0)
async def live_game_tracker():
    if setup.wt.riot_api_status() == 403:
        print(
            "[{}] [Live_game_tracker] error 403 Forbidden : Check your riot_api_key !!!".format(
                time.strftime("%c", time.localtime(time.time()))
            )
        )

        for guild in bot.guilds:
            await guild.system_channel.send(
                embed=discord.Embed(
                    title="Riot API has expired. Live-game tracker will stopped until fixes."
                )
            )
            await guild.system_channel.send(
                embed=discord.Embed(title="Live-game tracker was stopped.")
            )
            setup.lt[guild.id] = False

        live_game_tracker.stop()

        print(
            "[{}] [Live_game_tracker] live_game_tracker was stopped. ".format(
                time.strftime("%c", time.localtime(time.time()))
            )
        )
        return

    for guild in bot.guilds:
        if setup.lt[guild.id] is False:
            continue
        setup.wt.is_match_ended(guild)
        for summonerName in setup.wt.get_summoner_list(guild.id):
            content = preview_current_game(summonerName.rstrip("\n"), guild)
            if content is None:
                continue
            elif content[0] == "403":
                await guild.system_channel.send(content=content)
            elif content[0] == "200":
                with BytesIO() as image_binary:
                    content[1].save(image_binary, "PNG")
                    image_binary.seek(0)
                    await guild.system_channel.send(
                        file=discord.File(fp=image_binary, filename="image.png")
                    )


def preview_current_game(name, guild, lt=True):
    content = setup.wt.live_match(name, guild, lt)

    if type(content) is Image.Image:
        return ["200", content]
    elif type(content) is str:
        return ["403", content]
    else:
        return


bot.run(setup.token)
