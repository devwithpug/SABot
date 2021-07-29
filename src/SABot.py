import discord, asyncio, os, watcher, utils
from PIL import Image
from io import BytesIO
from discord.ext import commands, tasks
from utils import log, logErr


class sabot:
    def __init__(self):
        
        # Get Token
        self.token = utils.get_config()['bot_token_key']
        log("bot_token_key : {}".format(self.token[:4]+''.join('X' if c.isalpha() or c.isdigit() else c for c in self.token[4:])))

        # Bot Settings
        self.game = discord.Game("Online")
        self.prefix = "!"
        self.wt = watcher.watcher()
        self.lt = {}

os.chdir(os.path.dirname(os.path.abspath(__file__)))
setup = sabot()
bot = commands.Bot(
    command_prefix=setup.prefix, status=discord.Status.online, activity=setup.game
)

# Bot events


@bot.event
async def on_ready():
    
    log("We have logged in as {}".format(bot.user))
    log("Guild List : {}".format(str(bot.guilds)))
    
    setup.wt.load_summoner_list(bot.guilds)
    for guild in bot.guilds:
        setup.lt[guild.id] = True
    live_game_tracker.start()


@bot.event
async def on_guild_join(guild):
    
    log("SABot joined new guild.", guild)
    
    setup.wt.load_summoner_list(bot.guilds)
    setup.lt[guild.id] = False

    try:
        await guild.system_channel.send(
            embed=discord.Embed(title="SABot is now ONLINE =D")
        )
    except discord.errors.Forbidden:
        logErr("(error code: 50013): Missing Permissions", guild)
        await guild.leave()
        return

    log("Restart live_game_tracker", guild)
    live_game_tracker.restart()


@bot.event
async def on_guild_remove(guild):
    
    log("SABot was removed on this guild.", guild)
    
    setup.wt.delete_guild(guild.id)
    setup.wt.load_summoner_list(bot.guilds)
    del setup.lt[guild.id]
    
    log("Restart live_game_tracker", guild)
    live_game_tracker.restart()


# Bot commands

@bot.command()
async def command(ctx):

    log("{0.author} : {0.message.content}".format(ctx), ctx.guild)

    await ctx.send(
        embed=discord.Embed(
            title="Check available commands : https://github.com/devwithpug/SABot"
        )
    )


@bot.command()
async def l(ctx, *args):

    log("{0.author} : {0.message.content}".format(ctx), ctx.guild)

    if not args:
        await ctx.send(
            embed=discord.Embed(
                title="Check available commands : https://github.com/devwithpug/SABot"
            )
        )
        return

    if args[0] == "setup" and len(args) > 0:

        def check_confirm(m):
            return m.content == "y" or m.content == "n" and m.channel == ctx.channel

        def select_region(m):
            regions = ["br1", "eun1", "euw1", "jp1", "kr", "la1", "la2", "na1", "oc1", "tr1", "ru"]
            return m.content in regions and m.channel == ctx.channel

        await ctx.send(
            embed=discord.Embed(
                title="Type 'y' to start setup",
                description="'y' : Yes 'n' : No",
            ).set_author(name="Live tracker Setup")
        )
        try:
            confirm = await bot.wait_for("message", timeout=30.0, check=check_confirm)
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
    locale = get_locale(ctx.guild)

    if args[0] == "match" and len(args) > 1:

        response = setup.wt.search_summoner(ctx.guild, name)

        # match found
        if response.status_code == 200 and setup.wt.search_live_match(
            ctx.guild, response.json()["id"], False
        ):

            embed = discord.Embed(
                title=locale['match_found'],
                description=locale['loading'],
                colour=discord.Colour.green(),
            )
            await ctx.send(embed=embed, delete_after=0.5)

            content = setup.wt.load_live_match_data(
                ctx.guild, response.json()["id"], False
            )

            if type(content) is Image.Image:
                with BytesIO() as image_binary:
                    content.save(image_binary, "PNG")
                    image_binary.seek(0)
                    await ctx.send(
                        file=discord.File(fp=image_binary, filename="image.png")
                    )
            elif type(content) is str:
                await ctx.send(content=content)

    elif args[0] == "add" and len(args) > 1:
        d = setup.wt.edit_summoner_list(ctx.guild, True, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == "remove" and len(args) > 1:
        d = setup.wt.edit_summoner_list(ctx.guild, False, name)
        await ctx.send(embed=discord.Embed(title=d))

    elif args[0] == "start" and len(args) == 1:
        setup.wt.init_riot_api()

        if setup.lt[ctx.guild.id] is True:
            await ctx.send(
                embed=discord.Embed(title=locale['tracker_started_already'])
            )
            return
        elif setup.wt.riot_api_status() == 403:
            await ctx.send(
                embed=discord.Embed(
                    title=locale['tracker_failed']
                )
            )
            return
        try:
            live_game_tracker.start()
        except RuntimeError:
            live_game_tracker.restart()

        setup.lt[ctx.guild.id] = True

        log("live_game_tracker was started", ctx.guild)
        
        await ctx.send(embed=discord.Embed(title=locale['tracker_started']))

    elif args[0] == "stop" and len(args) == 1:
        if setup.lt[ctx.guild.id] is False:
            await ctx.send(
                embed=discord.Embed(title=locale['tracker_stopped_already'])
            )
            return
        setup.lt[ctx.guild.id] = False

        log("live_game_tracker was stopped", ctx.guild)

        await ctx.send(embed=discord.Embed(title=locale['tracker_stopped']))

    elif args[0] == "list" and len(args) == 1:
        region = setup.wt.guild_region[ctx.guild.id]
        names = ""
        for name in setup.wt.get_summoner_list(ctx.guild.id):
            names += name + "\n"
        await ctx.send(
            embed=discord.Embed(
                title=locale['region'] + " : " + region, description=names
            ).set_author(name=locale['tracker_list'])
        )

    else:
        await ctx.send(
            embed=discord.Embed(
                title="Check available commands : https://github.com/devwithpug/SABot"
            )
        )


@tasks.loop(seconds=60.0)
async def live_game_tracker():
    # There is possibility of some errors during API requests.
    if setup.wt.riot_api_status() == 403:
        logErr("403 Forbidden, Riot API token key was expired or It might be Riot API server error")
        return

    setup.wt.update_ddragon_data()

    for guild in bot.guilds:
        if setup.lt[guild.id] is False:
            continue
        
        setup.wt.remove_ended_match(guild)
        locale = get_locale(guild)

        for summonerName in setup.wt.get_summoner_list(guild.id):
            response = setup.wt.search_summoner(guild, summonerName)
            if response.status_code == 200 and setup.wt.search_live_match(
                guild, response.json()["id"]
            ):
                embed = discord.Embed(
                    title=locale['match_found'],
                    description=locale['loading'],
                    colour=discord.Colour.green(),
                )
                await guild.system_channel.send(embed=embed, delete_after=1.0)

                # match found
                content = setup.wt.load_live_match_data(guild, response.json()["id"])

                if type(content) is Image.Image:
                    with BytesIO() as image_binary:
                        content.save(image_binary, "PNG")
                        image_binary.seek(0)
                        await guild.system_channel.send(
                            file=discord.File(fp=image_binary, filename="image.png")
                        )
                elif type(content) is str:
                    await guild.system_channel.send(content=content)
                else:
                    continue


def preview_current_game(name, guild, lt=True):
    response = setup.wt.search_summoner(guild, name)
    if response.status_code == 200 and setup.wt.search_live_match(
        guild, response.json()["id"], False
    ):
        content = setup.wt.load_live_match_data(guild, response.json()["id"], lt)

        if type(content) is Image.Image:
            return ["200", content]
        elif type(content) is str:
            return ["403", content]
        else:
            return


def get_locale(guild):
    config = utils.get_locale_config()
    locale = config.locale['en']
    region = setup.wt.get_guild_region(guild)

    if region in config.locale:
        locale = config.locale[region]

    return locale


if __name__ == "__main__":
    
    bot.run(setup.token)
