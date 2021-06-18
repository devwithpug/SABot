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

#### You need to install python packages with pip:
```
discord.py, asyncio, Pillow, pymongo, pandas
```

#### And, you need to create token files:

Discord token file : `.token` in your directory with `SABot.py`

Riot API key file : `.riot_api_key` in your directory with `SABot.py`

mongoDB Cluster Code file : `.mongodb` in your directory with `SABot.py`
>mongodb+srv://admin:(your_db_password)@cluster0.9ycx5.mongodb.net/Cluster0?retryWites=true&w=majority

Finally,   

Run `SABot.py` and type `!l setup` to your Discord server.

## How to localization:

You can modify the file `locale.yaml` to make changes easily.

For information such as game modes and maps, check the link below provided by Riot Games.

[gameModes.json](https://static.developer.riotgames.com/docs/lol/gameModes.json)
[maps.json](https://static.developer.riotgames.com/docs/lol/maps.json)

```yaml
locale: {
  en: {
    tracker_failed: Couldn't start Live-game tracker. Invaild Riot API key.,
    tracker_started: Live-game tracker was started.,
    tracker_stopped: Live-game tracker was stopped.,
    tracker_started_already: Live-game tracker is already working.,
    tracker_stopped_already: Live-game tracker was already stopped.,
    region: Region,
    tracker_list: Live-game tracker Summoner List,
    match_found: New match has been found!,
    loading: Loading data...,

    blue_team: Blue Team,
    red_team: Red Team,
    name: Name,
    tier: Tier,
    ratio: Ratio,
    wins:  Wins,
    losses: Losses,

    invalid_summoner_name: This summoner is not registered. Please check spelling.,
    exists_summoner_name: This summoner was already added in your channel.,
    error: Error occured!,
    db_error: Database Error Occurred.,
    success_added: Summoner have successfully registered.,
    success_removed: Summoner have successfully removed.,
    summoner_not_in_list: Summoner not listed. Enter `!l list` to confirm.,
  },
```


# API Reference:
* `discord.py` (https://github.com/Rapptz/discord.py)
* `Riot API` (https://developer.riotgames.com/apis)
