# SABot : DiscordBot
## Invite SABot to your own Discord Channel:

Inviting `SABot` to your Discord Channel, you don't need to set up a `SABot` files.
And you just need to use the commands below.

SABot Permission that must be provided : `Send Messages, Embed Links`

[Invite SABot to your Discord Server](https://discord.com/api/oauth2/authorize?client_id=749632311208706073&permissions=2048&scope=bot)

####To use live tracker features, You need to Setup live tracker with your league of legends region. Invite SABot to your discord server and just type `!l setup`

개발중이라 정상적으로 작동하지 않을 수 있습니다..
혹시나 이용중 오류가 발생하시거나, 의견이 있으시면 
디스코드 `퍼그#8744` 통해서 메세지 보내주세요. 감사합니다!

## How to set up your own bot:

Discord token file : `.token` in your directory with `SABot.py`

Riot API key file : `.riot_api_key` in your directory with `SABot.py`

Run `SABot.py`. That's it!

Live-game-tracker data file `.summoner_list` will saved in your directory with `SABot.py`

## Features:

1. `Auto-notificiation` when user connects to voice channel.
2. Preview all of users `info` in your Discord Guild(Server).
3. Search Summoners statistics in `League of Legends.`
4. `Auto-notifications` when Summoner starts a game, and provide information of participations.
5. LOL live-game-tracker loops `every one minute`.
6. Set alarm to specific user.

## Commands:
    *General commands
        !help
        !commands

    *Set alarm
        !alarm

    *LOL Search-informations
        !l nick 'SummonerName'
        !l match 'summonerName' // live match info

    *LOL live-game-tracker
        !l setup
        !l add 'SummonerName'
        !l remove 'SummonerName'
        !l list
        !l start    // start live-game-tracker
        !l stop     // stop live-game-tracker

## API Reference:
* `discord.py` (https://github.com/Rapptz/discord.py)
* `Riot API` (https://developer.riotgames.com/apis)
* `Riot-Watcher` (https://github.com/pseudonym117/Riot-Watcher)
