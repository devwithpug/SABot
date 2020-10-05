from riotwatcher import LolWatcher, ApiError
import pandas as pd
import os
import time
import requests


class watcher:
    def __init__(self):
        # Get riot_api_key
        token_path = os.path.dirname(
            os.path.abspath(__file__)) + "/.riot_api_key"
        with open(token_path, "r", encoding="utf-8") as t:
            self.riot_api_key = t.read().split()[0]
        print("riot_api_key : ", self.riot_api_key)

        self.my_region = 'kr'

        self.lol_watcher = LolWatcher(self.riot_api_key)

        latest = self.lol_watcher.data_dragon.versions_for_region(
            self.my_region)
        champ_version = latest['n']['champion']
        self.static_champ_list = self.lol_watcher.data_dragon.champions(
            champ_version, False, 'ko_KR')
        self.queues = requests.get(
            'http://static.developer.riotgames.com/docs/lol/queues.json').json()
        self.live_game_id = {}
        self.ended_game_id_temp = {}

    def init_summoner_list(self, guilds):
        print("[Live_game_tracker]Initializing summoner_list ...")
        self.summoner_list_path = [os.path.dirname(
            os.path.abspath(__file__)) + "/.summoner_list_"+str(guild.id) for guild in guilds]
        self.summoner_list = {}
        self.summoner_list_temp = {}
        for path in self.summoner_list_path:
            try:
                f = open(path, "r", encoding="utf-8")
            except FileNotFoundError:
                f = open(path, "w", encoding="utf-8")
                f.close()
                print(
                    "Your own summoner_list not found. new file created at {}".format(path))
                f = open(path, "r", encoding="utf-8")
            self.set_summoner_list(f, path[path.find('list_')+5:])
            f.close()
        print("[Live_game_tracker]Done")

    def get_path(self, paths, guild_id):
        for path in paths:
            if guild_id in path:
                return path

    def set_summoner_list(self, file, guild_id):
        """Create list variable for summoner list

        Args:
            file (os.IO File): .summoner_list file
            guild_id (str): discord.Guild.id
        """
        self.summoner_list[guild_id] = file.readlines()
        self.summoner_list_temp[guild_id] = [
            name.rstrip() for name in self.summoner_list[guild_id]]

    def get_summoner_list(self, guild_id):
        """Return specific guilds summoner list

        Args:
            guild_id (str): discord.Guild.id

        Returns:
            List: SummonerName list
        """
        return self.summoner_list[str(guild_id)]

    def edit_summoner_list(self, guild_id, add, summonerName):
        """Operation that add or remove summonerName in summoner_list

        Args:
            guild_id (str): discord.Guild.id
            add (Bool): True is add, False is remove.
            summonerName (str): Summoner's name to add or remove.

        Returns:
            str: Operation result
        """
        if add:
            if summonerName in self.summoner_list_temp[guild_id]:
                return "이미 등록된 소환사 입니다."
            else:
                try:
                    self.summoner_list[guild_id].append(summonerName+"\n")
                except BaseException as err:
                    print("ERROR OCCURED! \n", err)
                    return "ERROR OCCURED"
                self.summoner_list_temp[guild_id] = [name.rstrip()
                                                     for name in self.summoner_list[guild_id]]
                with open(self.get_path(self.summoner_list_path, guild_id), "w", encoding="utf-8") as f:
                    f.writelines(self.summoner_list[guild_id])
                print(summonerName+" Added at " +
                      time.strftime('%c', time.localtime(time.time())))
                return "등록 성공"
        elif not add:
            try:
                self.summoner_list[guild_id].remove(summonerName+"\n")
            except ValueError:
                print("Error : SummonerName is not in the list \n")
                return "목록에 없는 소환사입니다. !l list를 입력하여 확인하세요."
            self.summoner_list_temp[guild_id] = [name.rstrip()
                                                 for name in self.summoner_list[guild_id]]
            with open(self.get_path(self.summoner_list_path, guild_id), "w", encoding="utf-8") as f:
                f.writelines(self.summoner_list[guild_id])
            print(summonerName+" Removed at " +
                  time.strftime('%c', time.localtime(time.time())))
            return "삭제 성공"

    def test_riot_api(self, name='hide on bush'):
        try:
            self.lol_watcher.summoner.by_name(self.my_region, name)
        except (ApiError, Exception) as err:
            return err.response.status_code
        return 200

    def live_match(self, summonerName, guild_id=None):
        """Call Riot API to receive live_match information.

        Args:
            summonerName (str): Summoner's name
            guild_id (str): discord.Guild.id

        Returns:
            dict: live_match data
        """
        try:
            me = self.lol_watcher.summoner.by_name(
                self.my_region, summonerName)
        except (ApiError, Exception) as err:
            print(err)
            if err.response.status_code == 429:
                print("error 429 Rate limit exceeded")
                return "`잠시 후에 다시 시도하세요.`"
            elif err.response.status_code == 404:
                print("error 404 Data not found")
                return "`ERROR! 등록되지 않은 소환사입니다. : "+summonerName+"`"
            elif err.response.status_code == 403:
                print("error 403 Forbidden")
                return
            elif err.response.status_code == 503:
                print("ERROR 503 : Riot API Server is now offline.")
                return
            else:
                print(err)
                return "`ERROR OCCURED`"
        data = []
        try:
            match = self.lol_watcher.spectator.by_summoner(
                self.my_region, me['id'])
        except (ApiError, Exception) as err:
            if err.response.status_code == 429:
                print("error 429 Rate limit exceeded")
                return "`잠시 후에 다시 시도하세요.`"
            elif err.response.status_code == 404:
                return
            elif err.response.status_code == 403:
                print("error 403 Forbidden")
                return
            elif err.response.status_code == 503:
                print("ERROR 503 : Riot API Server is now offline.")
                return
            else:
                print(err)
                return "`ERROR OCCURED`"

        match_data = {}

        if guild_id is not None:
            try:
                self.live_game_id[guild_id]
            except KeyError:
                self.live_game_id[guild_id] = []
                self.ended_game_id_temp[guild_id] = None
            if match['gameId'] in self.live_game_id[guild_id]:
                try:
                    self.lol_watcher.match.by_id(
                        self.my_region, match['gameId'])
                except (ApiError, Exception) as err:
                    if err.response.status_code == 404:
                        return
                    elif err.response.status_code == 503:
                        return
                    else:
                        print(
                            "Error occured at live_game_tracker. All of live_game_id data has been deleted.")
                        print(err)
                        self.live_game_id[guild_id].clear()
                        self.ended_game_id_temp[guild_id] = None
                        return
                print("[{}] [Live_game_tracker] Live game ended : {}".format(
                    time.strftime('%c', time.localtime(time.time())), match['gameId']))
                self.ended_game_id_temp[guild_id] = match['gameId']
                self.live_game_id[guild_id].remove(match['gameId'])
                return

            else:
                if match['gameId'] == self.ended_game_id_temp[guild_id]:
                    return

                self.live_game_id[guild_id].append(match['gameId'])

                print("[{}] [Live_game_tracker] New live game added : {}".format(
                    time.strftime('%c', time.localtime(time.time())), match['gameId']))
                print("[Live_game_tracker]Current tracking live_game_id list : " +
                      str(self.live_game_id[guild_id]))

        match_data['gameId'] = match['gameId']
        match_data['gameType'] = match['gameType']
        match_data['gameStartTime'] = match['gameStartTime']
        match_data['mapId'] = match['mapId']
        match_data['gameLength'] = match['gameLength']
        match_data['platformId'] = match['platformId']
        try:
            for queues in self.queues:
                if queues['queueId'] == match['gameQueueConfigId']:
                    match_data['map'] = queues['map']
                    match_data['gameMode'] = queues['description']
        except KeyError:
            match_data['map'] = match['gameMode']
            match_data['gameMode'] = match['gameType']

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
            row = self.lol_watcher.league.by_summoner(
                self.my_region, participant['summonerId'])
            print(row)
            if len(row) != 0:
                participants[i]['tier'] = row[-0]['tier']
                participants[i]['rank'] = row[-0]['rank']
                participants[i]['leaguePoints'] = row[-0]['leaguePoints']
                participants[i]['wins'] = row[-0]['wins']
                participants[i]['losses'] = row[-0]['losses']
                participants[i]['avarage'] = round(
                    row[-0]['wins']/(row[-0]['wins']+row[-0]['losses'])*100, 2)
            else:
                participants[i]['tier'] = "unranked"

            i += 1

        df = pd.DataFrame(participants)
        print(df)
        return data
