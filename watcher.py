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

    def live_match(self, summonerName = str):
        me = self.lol_watcher.summoner.by_name(self.my_region, summonerName)
        data = []
        match = self.lol_watcher.spectator.by_summoner(self.my_region, me['id'])
        match_data = {}
        match_data['gameId'] = match['gameId']
        match_data['gameType'] = match['gameType']
        match_data['gameStartTime'] = match['gameStartTime']
        match_data['mapId'] = match['mapId']
        match_data['gameLength'] = match['gameLength']
        match_data['platformId'] = match['platformId']
        match_data['gameMode'] = match['gameMode']
        match_data['gameQueueConfigId'] = match['gameQueueConfigId']
        data.append(match_data)

        participants = []
        for row in match['participants']:
            participants_row = {}
            participants_row['championId'] = row['championId']
            participants_row['summonerName'] = row['summonerName']
            participants_row['summonerId'] = row['summonerId']
            participants.append(participants_row)
        champ_dict = {}
        for champ in self.static_champ_list['data']:
            row = self.static_champ_list['data'][champ]
            champ_dict[row['key']] = row['name']
        for row in participants:
            row['championId'] = champ_dict[str(row['championId'])]
        data.append(participants)
        i = 0
        for participant in data[1]:
            row = self.lol_watcher.league.by_summoner(self.my_region, participant['summonerId'])
            if len(row) != 0:
                participants[i]['tier'] = row[0]['tier']
                participants[i]['rank'] = row[0]['rank']
                participants[i]['leaguePoints'] = row[0]['leaguePoints']
                participants[i]['wins'] = row[0]['wins']
                participants[i]['losses'] = row[0]['losses']
            else:
                participants[i]['tier'] = "unranked"
                participants[i]['rank'] = " "
                participants[i]['leaguePoints'] = " "
                participants[i]['wins'] = " "
                participants[i]['losses'] = " "
                
            i += 1
        
        df = pd.DataFrame(participants)
        print(df)
        return data