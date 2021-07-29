import pandas as pd
import os, requests, utils, wrapper
from pymongo.mongo_client import MongoClient
from utils import log, logErr


class watcher:
    def __init__(self):

        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        credentials = utils.get_config().credentials
        font = utils.get_config().font

        # Get riot_api_key
        self.riot_api_key = credentials['riot_api_key']
        log("riot_api_key : {}".format(self.riot_api_key[:5]+''.join('X' if c.isalpha() or c.isdigit() else c for c in self.riot_api_key[5:])))

        # Get mongoDB cluster address
        self.cluster = credentials['mongodb_cluster']
        log("mongoDB cluster : {}".format(self.cluster[:11]+''.join('X' if c.isalpha() or c.isdigit() else c for c in self.cluster[11:])))

        self.font_name = font['name']
        print("!!")
        print(self.font_name)
        self.guild_region = {}
        self.db = MongoClient(self.cluster).get_database("sabot")
        self.guild = self.db["Guild"]
        self.user = self.db["User"]
        self.champ_version = None
        self.update_ddragon_data()
        self.live_game_id = {}
        self.ended_game_temp = {}

    def init_riot_api(self):
        with open(".riot_api_key", "r", encoding="utf-8") as t:
            self.riot_api_key = t.readline()
        log("riot_api_key initialized to : {}".format(self.riot_api_key))

    def is_setup_already(self, guild):
        return self.guild.count_documents({"_id": guild.id})

    def update_ddragon_data(self):
        url = "https://ddragon.leagueoflegends.com/realms/kr.json"
        self.latest = requests.get(url).json()

        if self.champ_version is None:
            log("Data Dragon v{} loaded".format(self.latest["n"]["champion"]))
            self.champ_version = self.latest["n"]["champion"]

        elif self.champ_version != self.latest["n"]["champion"]:
            log("Data Dragon was updated from {} to {}".format(self.champ_version, self.latest['n']['champion']))
            self.champ_version = self.latest["n"]["champion"]

        url = (
            "https://ddragon.leagueoflegends.com/cdn/"
            + self.latest["v"]
            + "/data/en_US/"
        )
        self.static_champ_list = requests.get(url + "champion.json").json()
        self.static_spell_list = requests.get(url + "summoner.json").json()

    def setup(self, region, guild):
        if self.guild.count_documents({"_id": guild.id}):
            self.guild.update_one(
                {"_id": guild.id},
                {"$set": {"guild_name": guild.name, "region": region}},
            )
        else:
            self.guild.insert(
                {"_id": guild.id, "guild_name": guild.name, "region": region}
            )

    def delete_guild(self, guild_id):
        try:
            self.guild.delete_one({"_id": guild_id})
            self.user.delete_many({"guild_id": guild_id})
        except Exception as err:
            logErr(err)

    def load_summoner_list(self, guilds):
        """Create list variable for summoner list and guilds region

        Args:
            file (os.IO File): .summoner_list file
            guild_id (str): discord.Guild.id
        """

        guild_id_list = [g["_id"] for g in self.guild.find()]
        self.user_list = {}

        for guild in guilds:
            if not guild.id in guild_id_list:
                self.guild.insert_one(
                    {"_id": guild.id, "guild_name": guild.name, "region": "kr"}
                )
                log("new db documents was inserted", guild)

            self.guild_region[guild.id] = self.guild.find_one({"_id": guild.id})[
                "region"
            ]
            self.user_list[guild.id] = [
                n["user_name"] for n in self.user.find({"guild_id": guild.id})
            ]

    def get_summoner_list(self, guild_id):
        """Return specific guilds summoner list

        Args:
            guild_id (int): discord.Guild.id

        Returns:
            List: SummonerName list
        """
        return self.user_list[guild_id]

    def edit_summoner_list(self, guild, add, summonerName):
        """Operation that add or remove summonerName in summoner_list

        Args:
            guild_id (int): discord.Guild.id
            add (Bool): True is add, False is remove.
            summonerName (str): Summoner's name to add or remove.

        Returns:
            str: Operation result
        """
    
        region = self.guild_region[guild.id]
        locale = self.get_locale(region)    

        if add:
            url = "https://{}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}".format(
                self.guild_region[guild.id], summonerName
            )
            response = requests.get(url, headers={"X-Riot-Token": self.riot_api_key})
            if response.status_code != 200:
                if response.status_code == 404:
                    return locale['invalid_summoner_name']
                else:
                    return locale['error']

            if summonerName in self.user_list[guild.id]:
                return locale['exists_summoner_name']
            else:
                try:
                    self.user.insert_one(
                        {"guild_id": guild.id, "user_name": summonerName}
                    )
                except Exception as err:
                    logErr(err)
                    return locale['db_error']
                self.user_list[guild.id].append(summonerName)
                log("New summoner was added : {}".format(summonerName), guild)

                return locale['success_added']

        elif not add:
            try:
                self.user_list[guild.id].remove(summonerName)
            except ValueError:
                return locale['summoner_not_in_list']
            self.user.delete_one({"guild_id": guild.id, "user_name": summonerName})
            log("Summoner was removed : {}".format(summonerName), guild)
            
            return locale['success_removed']

    def riot_api_status(self):
        url = "https://kr.api.riotgames.com/lol/status/v4/platform-data"
        response = requests.get(url, headers={"X-Riot-Token": self.riot_api_key})
        return response.status_code

    def remove_ended_match(self, guild):
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
            response = self.is_match_ended(guild, game)

            if response.status_code == 200:
                log("Live game was ended : {}".format(game), guild)
                self.live_game_id[guild.id].remove(game)
                self.add_ended_game_temp(guild, game)

    def add_ended_game_temp(self, guild, matchId):
        try:
            self.ended_game_temp[guild.id].append(matchId)
        except KeyError:
            self.ended_game_temp[guild.id] = []
            self.ended_game_temp[guild.id].append(matchId)
        else:
            if len(self.ended_game_temp[guild.id]) > 10:
                self.ended_game_temp[guild.id].pop(0)

    def is_match_ended(self, guild, match):
        url = "https://{}.api.riotgames.com/lol/match/v4/matches/{}".format(
            self.guild_region[guild.id], match
        )
        response = requests.get(url, headers={"X-Riot-Token": self.riot_api_key})
        return response

    def search_summoner(self, guild, name):
        url = (
            "https://{}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}".format(
                self.guild_region[guild.id], name
            )
        )
        response = requests.get(url, headers={"X-Riot-Token": self.riot_api_key})
        return response

    def get_guild_region(self, guild):
        return self.guild_region[guild.id]

    def get_locale(self, region):
        config = utils.get_locale_config()
        locale = config.locale['en']

        if region in config.locale:
            locale = config.locale[region]
        return locale

    def search_live_match(self, guild, summonerId, dup=True):
        url = "https://{}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{}".format(
            self.guild_region[guild.id], summonerId
        )
        response = requests.get(url, headers={"X-Riot-Token": self.riot_api_key})
        if response.status_code == 200 and dup:
            try:
                matchId = response.json()["gameId"]
                if (
                    matchId in self.live_game_id[guild.id]
                    or matchId in self.ended_game_temp[guild.id]
                ):
                    return False
                else:
                    return True
            except KeyError:
                return True
        elif response.status_code == 200 and not dup:  # l match
            return True
        else:
            return False

    def load_live_match_data(self, guild, match, lt=True):
        """Call Riot API to receive live_match information.

        Args:
            guild (Guild()): discord.Guild
            match: response.json()

        Returns:
            dict: live_match data
        """

        region = self.guild_region[guild.id]
        locale = self.get_locale(region)

        url = "https://{}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{}".format(
            region, match
        )
        response = requests.get(url, headers={"X-Riot-Token": self.riot_api_key})
        if response.status_code != 200:
            return
        elif response.status_code == 404:
            return

        queues = requests.get(locale['queues']).json()
        maps = requests.get(locale['maps']).json()
        
        match = response.json()

        data = {}

        if lt:
            try:
                self.live_game_id[guild.id]
            except KeyError:
                self.live_game_id[guild.id] = []

            # When match was already in self.live_game_id
            if match["gameId"] in self.live_game_id[guild.id]:
                return
            else:
                response = self.is_match_ended(guild, match["gameId"])
                # If the match was ended
                if response.status_code != 404:
                    return

                self.live_game_id[guild.id].append(match["gameId"])

                log("New live match was added : {}".format(match["gameId"]), guild)
                log("Current tracking match list : {}".format(str(self.live_game_id[guild.id])), guild)

        data['match_data'] = wrapper.get_match_data(match, queues, maps)
        data['participants'] = wrapper.get_participants(match, self.static_champ_list, self.static_spell_list)

        for i, participant in zip(range(10), data['participants']):
            url = "https://{}.api.riotgames.com/lol/league/v4/entries/by-summoner/{}".format(
                region, participant["summonerId"]
            )
            row = requests.get(url, headers={"X-Riot-Token": self.riot_api_key}).json()

            wrapper.update_participants(i, data['participants'], row)

        df = pd.DataFrame(data['participants'])
        print(df)

        return wrapper.draw_image(self.latest, data, locale, self.font_name)
