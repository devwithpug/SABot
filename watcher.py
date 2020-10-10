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
        """Get summoner's name from .summoner_list

        Args:
            guilds ([Guild]): discord.Guild
        """
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
        try:
            self.lol_watcher.summoner.by_name(self.my_region, summonerName)
        except (ApiError, Exception) as err:
            if err.response.status_code == 404:
                return "등록되지 않은 소환사입니다. 오타를 확인 해주세요."
            else:
                return "ERROR OCCURED"
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

    def riot_api_status(self):
        try:
            self.lol_watcher.lol_status.shard_data(self.my_region)
        except (ApiError, Exception) as err:
            return err.response.status_code
        return 200

    def is_match_ended(self, guild):
        """Check the live_game was ended

        Args:
            guild (Guild()): discord.Guild
        """
        try:
            self.live_game_id[guild.id]
        except KeyError:
            return

        matches = self.live_game_id[guild.id]
        for game in matches:
            try:
                self.lol_watcher.match.by_id(self.my_region, game)
            except (ApiError, Exception):
                continue
            self.live_game_id[guild.id].remove(game)
            print("[{}][Live_game_tracker][{}] Live game ended : {}".format(
                time.strftime('%c', time.localtime(time.time())), guild.name, game))

    def live_match(self, summonerName, guild=None, lt=True):
        """Call Riot API to receive live_match information.

        Args:
            summonerName (str): Summoner's name
            guild (Guild()): discord.Guild

        Returns:
            dict: live_match data
        """
        try:
            me = self.lol_watcher.summoner.by_name(
                self.my_region, summonerName)
        except (ApiError, Exception) as err:
            print(err)
            if err.response.status_code == 404 and not lt:
                return "`ERROR! 등록되지 않은 소환사입니다. : "+summonerName+"`"
            if err.response.status_code == 403 and not lt:
                return "`Riot API ERROR`"
            elif err.response.status_code == 404 and lt:
                self.edit_summoner_list(str(guild.id), False, summonerName)
                return "`Live-tracker 오류 발생\n\
                    소환사 [{}]의 닉네임이 변경되었거나 오류가 발생했습니다.\n\
                    [!l add 소환사명] 명령어를 이용하여 다시 등록하시기 바랍니다.`".format(summonerName)
            else:
                return
        data = []
        try:
            match = self.lol_watcher.spectator.by_summoner(
                self.my_region, me['id'])
        except (ApiError, Exception) as err:
            if err.response.status_code == 404:
                return
            else:
                print(err)
                return

        match_data = {}

        if guild is not None:
            try:
                self.live_game_id[guild.id]
            except KeyError:
                self.live_game_id[guild.id] = []
                self.ended_game_id_temp[guild.id] = None
            if match['gameId'] in self.live_game_id[guild.id]:
                try:
                    self.lol_watcher.match.by_id(
                        self.my_region, match['gameId'])
                except (ApiError, Exception) as err:
                    if err.response.status_code == 404 or\
                            err.response.status_code == 403 or\
                            err.response.status_code == 503 or\
                            err.response.status_code == 504:
                        return
                    else:
                        print(
                            "[{}]Error occured at live_game_tracker. All of live_game_id data has been deleted.".format(time.strftime('%c', time.localtime(time.time()))))
                        print(err)
                        self.live_game_id[guild.id].clear()
                        self.ended_game_id_temp[guild.id] = None
                        return
                print("[{}][Live_game_tracker][{}] Live game ended : {}".format(
                    time.strftime('%c', time.localtime(time.time())), guild.name, match['gameId']))
                self.ended_game_id_temp[guild.id] = match['gameId']
                self.live_game_id[guild.id].remove(match['gameId'])
                return
            else:
                if match['gameId'] == self.ended_game_id_temp[guild.id]:
                    return

                self.live_game_id[guild.id].append(match['gameId'])

                print("[{}][Live_game_tracker][{}] New live game added : {}".format(
                    time.strftime('%c', time.localtime(time.time())), guild.name, match['gameId']))
                print("[{}][Live_game_tracker][{}]Current tracking live_game_id list : {}".format(
                    time.strftime('%c', time.localtime(time.time())), guild.name, str(self.live_game_id[guild.id])))

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

            if len(row) != 0:
                ranked_solo_index = 0
                for league in row:
                    if league['queueType'] == "RANKED_SOLO_5x5":
                        break
                    else:
                        ranked_solo_index += 1

                participants[i]['tier'] = row[ranked_solo_index]['tier']
                participants[i]['rank'] = row[ranked_solo_index]['rank']
                participants[i]['leaguePoints'] = row[ranked_solo_index]['leaguePoints']
                participants[i]['wins'] = row[ranked_solo_index]['wins']
                participants[i]['losses'] = row[ranked_solo_index]['losses']
                participants[i]['avarage'] = round(
                    row[ranked_solo_index]['wins']/(row[ranked_solo_index]['wins']+row[ranked_solo_index]['losses'])*100, 2)
            else:
                participants[i]['tier'] = "unranked"

            i += 1

        df = pd.DataFrame(participants)
        print(df)
        return data
