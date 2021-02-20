# SABot
## Dicord Bot for League of Legends match auto tracker

![SABot](https://user-images.githubusercontent.com/69145799/108334673-853a4400-7215-11eb-96c6-7a3d6872e4eb.png)

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
>mongodb+srv://admin:(your_db_password)@cluster0.9ycx5.mongodb.net/Cluster0?retryWites=true&w=majority

Run `SABot.py` and type `!setup` to your Discord server.



## API Reference:
* `discord.py` (https://github.com/Rapptz/discord.py)
* `Riot API` (https://developer.riotgames.com/apis)
* `Riot-Watcher` (https://github.com/pseudonym117/Riot-Watcher)
