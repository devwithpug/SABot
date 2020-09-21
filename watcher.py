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
            riot_api_key = t.read().split()[0]
        print("riot_api_key : ", riot_api_key)

        self.my_region = 'kr'

        self.lol_watcher = LolWatcher(riot_api_key)

        latest = self.lol_watcher.data_dragon.versions_for_region(
            self.my_region)
        champ_version = latest['n']['champion']
        self.static_champ_list = self.lol_watcher.data_dragon.champions(
            champ_version, False, 'ko_KR')
        self.queues = requests.get(
            'http://static.developer.riotgames.com/docs/lol/queues.json').json()
        self.live_game_id = {}

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
        return self.summoner_list_temp[guild_id]

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
                    return "ERROR OCCURED : Check your console !!!"
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
            except ValueError as err:
                print("ERROR OCCURED! \n", err)
                return "ERROR OCCURED : Check your console !!!"
            self.summoner_list_temp[guild_id] = [name.rstrip()
                                                 for name in self.summoner_list[guild_id]]
            with open(self.get_path(self.summoner_list_path, guild_id), "w", encoding="utf-8") as f:
                f.writelines(self.summoner_list[guild_id])
            print(summonerName+" Removed at " +
                  time.strftime('%c', time.localtime(time.time())))
            return "삭제 성공"

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
        except ApiError as err:
            if err.response.status_code == 429:
                print("error 429 Rate limit exceeded")
                return "`잠시 후에 다시 시도하세요.`"
            elif err.response.status_code == 404:
                print("error 404 Data not found")
                return "`ERROR! 등록되지 않은 소환사입니다. : "+summonerName+"`"
            elif err.response.status_code == 403:
                print("error 403 Forbidden : Check your riot_api_key !!!")
                return "`ERROR 403 Forbidden : Check your riot_api_key !!!`"
            else:
                print("error " + err.response.status_code)
                return "`ERROR OCCURED : Check your console !!!`"
        data = []
        try:
            match = self.lol_watcher.spectator.by_summoner(
                self.my_region, me['id'])
        except ApiError as err:
            if err.response.status_code == 429:
                print("error 429 Rate limit exceeded")
                return "`잠시 후에 다시 시도하세요.`"
            elif err.response.status_code == 404:
                return
            elif err.response.status_code == 403:
                print("error 403 Forbidden : Check your riot_api_key !!!")
                return "`ERROR 403 Forbidden : Check your riot_api_key !!!`"
            else:
                print("error " + err.response.status_code)
                return "`ERROR OCCURED : Check your console !!!`"

        match_data = {}

        if guild_id is not None:
            try:
                self.live_game_id[guild_id]
            except KeyError:
                self.live_game_id[guild_id] = []
            if not match['gameId'] in self.live_game_id[guild_id]:
                self.live_game_id[guild_id].append(match['gameId'])
                print("[Live_game_tracker]new live game added : ", match['gameId'])
                print("[Live_game_tracker]Current tracking live_game_id list : " +
                      str(self.live_game_id[guild_id]))
            else:
                for gameId in self.live_game_id[guild_id]:
                    try:
                        self.lol_watcher.match.by_id(self.my_region, gameId)
                    except ApiError as err:
                        if err.response.status_code == 200:
                            print(
                                "[Live_game_tracker]live-game ended / ", match['gameId'])
                            self.live_game_id[guild_id].remove(gameId)
                        elif err.response.status_code == 403:
                            print(
                                "error 403 Forbidden : Check your riot_api_key !!!")
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
            row = self.lol_watcher.league.by_summoner(
                self.my_region, participant['summonerId'])
            if len(row) != 0:
                participants[i]['tier'] = row[-1]['tier']
                participants[i]['rank'] = row[-1]['rank']
                participants[i]['leaguePoints'] = row[-1]['leaguePoints']
                participants[i]['wins'] = row[-1]['wins']
                participants[i]['losses'] = row[-1]['losses']
                participants[i]['avarage'] = round(
                    row[-1]['wins']/(row[-1]['wins']+row[-1]['losses'])*100, 2)
            else:
                participants[i]['tier'] = "unranked"

            i += 1

        df = pd.DataFrame(participants)
        print(df)
        return data
