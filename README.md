# SABot
## Dicord Bot for League of Legends match auto tracker

## Features:

1. Search Summoners statistics in `League of Legends.`
2. `Auto-notifications` provide when summoner starts a match, and provide information of participations.

## Commands:
    *General commands
        !help
        !commands

    *LOL Search-informations
        !l match 'SummonerName' // live match info

    *LOL live-match-tracker
        !l setup
        !l add 'SummonerName'
        !l remove 'SummonerName'
        !l list
        !l start    // start live-match-tracker
        !l stop     // stop live-match-tracker

## How to set up your own bot:

Discord token file : `.token` in your directory with `SABot.py`

Riot API key file : `.riot_api_key` in your directory with `SABot.py`

mongoDB Cluster Code file : `.mongodb` in your directory with `SABot.py`
>mongodb+srv://admin:<password>@cluster0.9ycx5.mongodb.net/Cluster0?retryWites=true&w=majority
   
   
Run `SABot.py` and type `!setup` to your Discord server.

###OSError: cannot open resource // getfont()
>SABot will open fonts(NanumGothic.ttf) from your OS. This font supports Korean.   
To change this settings, `watcher.py` line 427: will helps.




## API Reference:
* `discord.py` (https://github.com/Rapptz/discord.py)
* `Riot API` (https://developer.riotgames.com/apis)
* `Riot-Watcher` (https://github.com/pseudonym117/Riot-Watcher)
