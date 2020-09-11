from riotwatcher import LolWatcher, ApiError
import pandas as pd
import os, time, requests


class watcher:
    #Get riot_api_key
    token_path = os.path.dirname(os.path.abspath(__file__)) + "/.riot_api_key"
    t = open(token_path, "r", encoding="utf-8")
    riot_api_key = t.read().split()[0]
    print("riot_api_key : ", riot_api_key)
    
    #Get summoner_list
    summoner_list_path = os.path.dirname(os.path.abspath(__file__)) + "/.summoner_list"
    try:
        f = open(summoner_list_path, "r", encoding="utf-8")
    except FileNotFoundError:
        f = open(summoner_list_path, "w", encoding="utf-8")
        f.close()
        print("summoner_list not found. new file created(.summoner_list)")
        f = open(summoner_list_path, "r", encoding="utf-8")
    summoner_list = f.readlines()
    summoner_list_temp = [name.rstrip() for name in summoner_list]
    f.close()

    my_region = 'kr'

    lol_watcher = LolWatcher(riot_api_key)

    latest = lol_watcher.data_dragon.versions_for_region(my_region)
    champ_version = latest['n']['champion']
    static_champ_list = lol_watcher.data_dragon.champions(champ_version, False, 'ko_KR')
    queues = requests.get('http://static.developer.riotgames.com/docs/lol/queues.json').json()
    live_game_id = []
    
    def get_summoner_list(self):
        return self.summoner_list_temp

    def edit_summoner_list(self, add, summonerName):
        if add:
            if summonerName in self.summoner_list_temp:
                return "이미 등록된 소환사 입니다."
            else:
                try:
                    self.summoner_list.append(summonerName+"\n")
                except BaseException as err:
                    print("ERROR OCCURED! \n", err)
                    return "ERROR OCCURED : Check your console !!!"
                self.summoner_list_temp = [name.rstrip() for name in self.summoner_list]
                with open(self.summoner_list_path, "w", encoding="utf-8") as f:
                    f.writelines(self.summoner_list)
                print(summonerName+" Added at "+ time.strftime('%c', time.localtime(time.time())))
                return "등록 성공"
        elif not add:
            try:
                self.summoner_list.remove(summonerName+"\n")
            except ValueError as err:
                print("ERROR OCCURED! \n", err)
                return "ERROR OCCURED : Check your console !!!"
            self.summoner_list_temp = [name.rstrip() for name in self.summoner_list]
            with open(self.summoner_list_path, "w", encoding="utf-8") as f:
                f.writelines(self.summoner_list)
            print(summonerName+" Removed at "+ time.strftime('%c', time.localtime(time.time())))
            return "삭제 성공"

    def live_match(self, summonerName = str):
        try:
            me = self.lol_watcher.summoner.by_name(self.my_region, summonerName)
        except ApiError as err:
            if err.response.status_code == 429:
                print("error 429 Rate limit exceeded")
                return "`{}초 후에 다시 시도하세요.`".format(err.headers['Retry-After'])
            elif err.response.status_code == 404:
                print("error 404 Data not found")
                return "`ERROR! 등록되지 않은 소환사입니다. : "+summonerName+"`"
            elif err.response.status_code == 403:
                print("error 403 Forbidden : Check your riot_api_key !!!")
                return "`ERROR 403 Forbidden : Check your riot_api_key !!!`"
            else:
                print("error "+ err.response.status_code)
                return "`ERROR OCCURED : Check your console !!!`"
        data = []
        try:
            match = self.lol_watcher.spectator.by_summoner(self.my_region, me['id'])
        except ApiError as err:
            if err.response.status_code == 429:
                print("error 429 Rate limit exceeded")
                return "`{}초 후에 다시 시도하세요.`".format(err.headers['Retry-After'])
            elif err.response.status_code == 404:
                print("error 404 Data not found : "+summonerName)
                return
        match_data = {}

        if not match['gameId'] in self.live_game_id:
            self.live_game_id.append(match['gameId'])
            print("new live game added : ", match['gameId'])
            print("Current tracking live_game_id list : "+ str(self.live_game_id))
        else:
            for gameId in self.live_game_id:
                try:
                    m = self.lol_watcher.match.by_id(self.my_region, gameId)
                except ApiError as err:
                    if err.response.status_code == 200:
                        print("live-game ended / ", match['gameId'])
                        self.live_game_id.remove(gameId)
                    elif err.response.status_code == 403:
                        print("error 403 Forbidden : Check your riot_api_key !!!")
                return
        

        match_data['gameId'] = match['gameId']
        match_data['gameType'] = match['gameType']
        match_data['gameStartTime'] = match['gameStartTime']
        match_data['mapId'] = match['mapId']
        match_data['gameLength'] = match['gameLength']
        match_data['platformId'] = match['platformId']
        for queues in self.queues:
            if queues['queueId'] == match['gameQueueConfigId']:
                match_data['map'] = queues['map']
                match_data['gameMode'] = queues['description']
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
                participants[i]['avarage'] = round(row[0]['wins']/(row[0]['wins']+row[0]['losses'])*100, 2)
            else:
                participants[i]['tier'] = "unranked"
                
            i += 1
        
        df = pd.DataFrame(participants)
        print(df)
        return data