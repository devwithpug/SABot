# SABot : DiscordBot
## How to set up:

Discord token file : `.token` in your directory with `SABot.py`

Riot API key file : `.riot_api_key` in your directory with `SABot.py`

Run `SABot.py`. That's it!

Live-game-tracker data file `.summoner_list` will saved in your directory with `SABot.py`

## Features:

1. `Auto-notificiation` when user connects to voice channel.
2. Preview all of users `info` in your Discord Guild(Server).
3. Search Summoners statistics in `League of Legends.`
4. Auto-notifications when Summoner starts a game, and provide information of participations.
5. Set alarm to specific user.

## Commands:
    *General commands
        !help
        !commands

    *Set alarm
        !alarm

    *LOL Search-informations
        !l nick 'SummonerName'
        !l currentGame 'summonerName'

    *LOL live-game-tracker
        !l add 'SummonerName'
        !l remove 'SummonerName'

## API Reference:
* `discord.py` (https://github.com/Rapptz/discord.py)
* `Riot API` (https://developer.riotgames.com/apis)
* `Riot-Watcher` (https://github.com/pseudonym117/Riot-Watcher)
