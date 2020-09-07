from riotwatcher import LolWatcher, ApiError
import pandas as pd
import os

class watcher:
    #Get riot_api_key
    token_path = os.path.dirname(os.path.abspath(__file__)) + "/.riot_api_key"
    t = open(token_path, "r", encoding="utf-8")
    riot_api_key = t.read().split()[0]
    print("riot_api_key : ", riot_api_key)

    my_region = 'kr'

    lol_watcher = LolWatcher(riot_api_key)

    latest = lol_watcher.data_dragon.versions_for_region(my_region)
    champ_version = latest['n']['champion']
    static_champ_list = lol_watcher.data_dragon.champions(champ_version, False, 'ko_KR')

    def match_list(self, summonerName = str):
        me = watcher.lol_watcher.summoner.by_name(watcher.my_region, summonerName)
        match = watcher.lol_watcher.match.matchlist_by_account(watcher.my_region, me['accountId'])
        last_match = match['matches'][0]
        match_detail = watcher.lol_watcher.match.by_id(watcher.my_region, last_match['gameId'])

        participants = []
        for row in match_detail['participants']:
            participants_row = {}
            participants_row['championId'] = row['championId']
            participants_row['spell1Id'] = row['spell1Id']
            participants_row['spell2Id'] = row['spell2Id']
            participants_row['win'] = row['stats']['win']
            participants_row['kills'] = row['stats']['kills']
            participants_row['deaths'] = row['stats']['deaths']
            participants_row['assists'] = row['stats']['assists']
            participants.append(participants_row)

        df = pd.DataFrame(participants)
        print(df)

    def live_match(self, summonerName = str):
        me = watcher.lol_watcher.summoner.by_name(watcher.my_region, summonerName)
        match_info = []
        match = watcher.lol_watcher.spectator.by_summoner(watcher.my_region, me['id'])
        match_data = {}
        match_data['gameId'] = match['gameId']
        match_data['gameType'] = match['gameType']
        match_data['gameStartTime'] = match['gameStartTime']
        match_data['mapId'] = match['mapId']
        match_data['gameLength'] = match['gameLength']
        match_data['platformId'] = match['platformId']
        match_data['gameMode'] = match['gameMode']
        match_data['gameQueueConfigId'] = match['gameQueueConfigId']
        match_info.append(match_data)

        df = pd.DataFrame(match_info)
        

        participants = []
        for row in match['participants']:
            participants_row = {}
            participants_row['championId'] = row['championId']
            participants_row['summonerName'] = row['summonerName']
            participants_row['summonerId'] = row['summonerId']
            participants_row['spell1Id'] = row['spell1Id']
            participants_row['spell2Id'] = row['spell2Id']
            participants.append(participants_row)
    
        champ_dict = {}
        for champ in watcher.static_champ_list['data']:
            row = watcher.static_champ_list['data'][champ]
            champ_dict[row['key']] = row['name']
        for row in participants:
            row['championId'] = champ_dict[str(row['championId'])]

        df = pd.DataFrame(participants)
        return df














