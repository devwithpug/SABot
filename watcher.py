from pymongo.mongo_client import MongoClient
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import os, time, requests
from PIL import Image, ImageDraw, ImageFont
from urllib import request
from io import BytesIO


class watcher:
    def __init__(self):

        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Get riot_api_key
        with open(".riot_api_key", "r", encoding="utf-8") as t:
            self.riot_api_key = t.read().split()[0]
        print("riot_api_key : ", self.riot_api_key)

        # Get mongoDB cluster address
        with open(".mongodb", "r", encoding="utf-8") as t:
            self.cluster = t.read().split()[0]
        print("[mongoDB]", self.cluster)

        self.guild_region = {}
        self.locale_dict = {
            "br1": "pt_BR",
            "eun1": "en_GB",
            "euw1": "en_GB",
            "jp1": "ja_JP",
            "kr": "ko_KR",
            "la1": "es_MX",
            "la2": "es_AR",
            "na1": "en_US",
            "oc1": "en_AU",
            "tr1": "tr_TR",
            "ru": "ru_RU",
        }
        self.lol_watcher = LolWatcher(self.riot_api_key)
        self.db = MongoClient(self.cluster).get_database("sabot")
        self.guild = self.db["Guild"]
        self.user = self.db["User"]
        self.queues = requests.get(
            "http://static.developer.riotgames.com/docs/lol/queues.json"
        ).json()
        self.champ_version = ""
        self.update_ddragon_data()
        self.live_game_id = {}

    def init_riot_api(self):
        with open(".riot_api_key", "r", encoding="utf-8") as t:
            self.riot_api_key = t.read().split()[0]
        print("Init riot_api_key : ", self.riot_api_key)
        self.lol_watcher = LolWatcher(self.riot_api_key)

    def is_setup_already(self, guild):
        return self.guild.count_documents({"_id": guild.id})

    def update_ddragon_data(self):
        url = "https://ddragon.leagueoflegends.com/realms/kr.json"
        self.latest = requests.get(url).json()
        if self.champ_version != self.latest["n"]["champion"]:
            print(
                "[{}][Live_game_tracker]Data Dragon version was updated to {} from {}".format(
                    time.strftime("%c", time.localtime(time.time())),
                    self.latest["n"]["champion"],
                    self.champ_version,
                )
            )
            self.champ_version = self.latest["n"]["champion"]

            url = (
                "https://ddragon.leagueoflegends.com/cdn/"
                + self.latest["v"]
                + "/data/en_US/summoner.json"
            )
            self.static_spell_list = requests.get(url).json()

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
            print(err)

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
                print("new db documents was inserted, id : ", guild.id)

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

    def edit_summoner_list(self, guild_id, add, summonerName):
        """Operation that add or remove summonerName in summoner_list

        Args:
            guild_id (int): discord.Guild.id
            add (Bool): True is add, False is remove.
            summonerName (str): Summoner's name to add or remove.

        Returns:
            str: Operation result
        """
        if add:
            try:
                self.lol_watcher.summoner.by_name(
                    self.guild_region[guild_id], summonerName
                )
            except (ApiError, Exception) as err:
                if err.response.status_code == 404:
                    return "등록되지 않은 소환사입니다. 오타를 확인 해주세요."
                else:
                    return "ERROR OCCURED"

            if summonerName in self.user_list[guild_id]:
                return "이미 등록된 소환사 입니다."
            else:
                try:
                    self.user.insert_one(
                        {"guild_id": guild_id, "user_name": summonerName}
                    )
                except Exception as err:
                    print(err)
                    return "DB ERROR"
                self.user_list[guild_id].append(summonerName)
                print(
                    summonerName
                    + " Added at "
                    + time.strftime("%c", time.localtime(time.time()))
                )
                return "등록 성공"
        elif not add:
            try:
                self.user_list[guild_id].remove(summonerName)
            except ValueError:
                print("Error : SummonerName is not in the list \n")
                return "목록에 없는 소환사입니다. !l list를 입력하여 확인하세요."
            self.user.delete_one({"guild_id": guild_id, "user_name": summonerName})
            print(
                summonerName
                + " Removed at "
                + time.strftime("%c", time.localtime(time.time()))
            )
            return "삭제 성공"

    def riot_api_status(self):
        try:
            self.lol_watcher.lol_status.shard_data("kr")
        except (ApiError, Exception) as err:
            print(err)
            try:
                return err.response.status_code
            except AttributeError as err:
                print(err)
                return False
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
                self.lol_watcher.match.by_id(self.guild_region[guild.id], game)
            except (ApiError, Exception):
                continue
            self.live_game_id[guild.id].remove(game)
            print(
                "[{}][Live_game_tracker][{}]Live game ended : {}".format(
                    time.strftime("%c", time.localtime(time.time())), guild.name, game
                )
            )

    def live_match(self, summonerName, guild, lt=True):
        """Call Riot API to receive live_match information.

        Args:
            summonerName (str): Summoner's name
            guild (Guild()): discord.Guild

        Returns:
            dict: live_match data
        """
        try:
            me = self.lol_watcher.summoner.by_name(
                self.guild_region[guild.id], summonerName
            )
        except (ApiError, Exception) as err:
            print(err)
            if err.response.status_code == 404 and not lt:
                return "`ERROR! 등록되지 않은 소환사입니다. : " + summonerName + "`"
            if err.response.status_code == 403 and not lt:
                return "`Riot API ERROR`"
            elif err.response.status_code == 404 and lt:
                self.edit_summoner_list(guild.id, False, summonerName)
                return "`Live-tracker 오류 발생\n\
                    소환사 [{}]의 닉네임이 변경되었거나 오류가 발생했습니다.\n\
                    [!l add 소환사명] 명령어를 이용하여 다시 등록하시기 바랍니다.`".format(
                    summonerName
                )
            else:
                return
        data = []
        try:
            match = self.lol_watcher.spectator.by_summoner(
                self.guild_region[guild.id], me["id"]
            )
        except (ApiError, Exception) as err:
            if err.response.status_code == 404:
                return
            else:
                print(err)
                return

        match_data = {}

        if lt:
            try:
                self.live_game_id[guild.id]
            except KeyError:
                self.live_game_id[guild.id] = []
            if match["gameId"] in self.live_game_id[guild.id]:
                try:
                    self.lol_watcher.match.by_id(
                        self.guild_region[guild.id], match["gameId"]
                    )
                except (ApiError, Exception) as err:
                    if (
                        err.response.status_code == 404
                        or err.response.status_code == 403
                        or err.response.status_code == 503
                        or err.response.status_code == 504
                        or err.response.status_code == 429
                    ):
                        return
                    else:
                        print(
                            "[{}]Unusual error occured at live_game_tracker".format(
                                time.strftime("%c", time.localtime(time.time()))
                            )
                        )
                        print(err)
                print(
                    "[{}][Live_game_tracker][{}]Live game ended : {}".format(
                        time.strftime("%c", time.localtime(time.time())),
                        guild.name,
                        match["gameId"],
                    )
                )
                self.live_game_id[guild.id].remove(match["gameId"])
                return
            else:
                try:
                    self.lol_watcher.match.by_id(
                        self.guild_region[guild.id], match["gameId"]
                    )
                except (ApiError, Exception) as err:
                    if err.response.status_code == 404:
                        pass
                    else:
                        return
                else:
                    return

                self.live_game_id[guild.id].append(match["gameId"])

                print(
                    "[{}][Live_game_tracker][{}]New live game added : {}".format(
                        time.strftime("%c", time.localtime(time.time())),
                        guild.name,
                        match["gameId"],
                    )
                )
                print(
                    "[{}][Live_game_tracker][{}]Current tracking live_game_id list : {}".format(
                        time.strftime("%c", time.localtime(time.time())),
                        guild.name,
                        str(self.live_game_id[guild.id]),
                    )
                )

        static_champ_list = self.lol_watcher.data_dragon.champions(
            self.champ_version, False, self.locale_dict[self.guild_region[guild.id]]
        )

        match_data["gameId"] = match["gameId"]
        match_data["gameType"] = match["gameType"]
        match_data["mapId"] = match["mapId"]
        match_data["gameLength"] = match["gameLength"]

        try:
            for queues in self.queues:
                if queues["queueId"] == match["gameQueueConfigId"]:
                    match_data["map"] = queues["map"]
                    match_data["gameMode"] = queues["description"]
        except KeyError:
            match_data["map"] = match["gameMode"]
            match_data["gameMode"] = match["gameType"]

        data.append(match_data)

        participants = []
        for row in match["participants"]:
            participants_row = {}
            participants_row["championId"] = row["championId"]
            participants_row["summonerName"] = row["summonerName"]
            participants_row["summonerId"] = row["summonerId"]
            participants_row["sp1"] = row["spell1Id"]
            participants_row["sp2"] = row["spell2Id"]
            participants.append(participants_row)
        champ_dict = {}
        spell_dict = {}
        for champ in static_champ_list["data"]:
            row = static_champ_list["data"][champ]
            champ_dict[row["key"]] = row["id"]
        for spell in self.static_spell_list["data"]:
            row = self.static_spell_list["data"][spell]
            spell_dict[row["key"]] = row["id"]
        for row in participants:
            try:
                row["championId"] = champ_dict[str(row["championId"])]
            except KeyError:
                row["championId"] = "NULL"
            row["sp1"] = spell_dict[str(row["sp1"])]
            row["sp2"] = spell_dict[str(row["sp2"])]
        data.append(participants)

        for participant, i in zip(data[1], range(10)):
            row = self.lol_watcher.league.by_summoner(
                self.guild_region[guild.id], participant["summonerId"]
            )

            if len(row) != 0:
                ranked_solo_index = 0
                for league in row:
                    if league["queueType"] == "RANKED_SOLO_5x5":
                        break
                    else:
                        ranked_solo_index += 1
                try:
                    row[ranked_solo_index]
                except IndexError:
                    participants[i]["tier"] = "unranked"
                    participants[i]["rank"] = ""
                    participants[i]["wins"] = ""
                    participants[i]["losses"] = ""
                    participants[i]["avarage"] = ""
                    continue
                participants[i]["tier"] = row[ranked_solo_index]["tier"]
                participants[i]["rank"] = row[ranked_solo_index]["rank"]
                participants[i]["wins"] = row[ranked_solo_index]["wins"]
                participants[i]["losses"] = row[ranked_solo_index]["losses"]
                participants[i]["avarage"] = round(
                    row[ranked_solo_index]["wins"]
                    / (
                        row[ranked_solo_index]["wins"]
                        + row[ranked_solo_index]["losses"]
                    )
                    * 100,
                    2,
                )
            else:
                participants[i]["tier"] = "unranked"
                participants[i]["rank"] = ""
                participants[i]["wins"] = ""
                participants[i]["losses"] = ""
                participants[i]["avarage"] = ""

        df = pd.DataFrame(participants)
        print(df)

        return self.matchWrapper(self.latest, data[0], data[1])

    def matchWrapper(self, latest, match, participants):
        # background
        lineX = 1920
        lineY = 100

        font = ImageFont.truetype("NanumGothic.ttf", 50)

        im = Image.new("RGBA", (lineX, lineY * 13), (255, 255, 255))
        d = ImageDraw.Draw(im)
        line = Image.new("RGB", (lineX, lineY), (230, 230, 230))
        for i in range(0, 13):
            if i % 2 == 0:
                im.paste(line, (0, i * lineY))
            elif i == 1:
                im.paste(
                    Image.new("RGB", (lineX, lineY), (85, 85, 255)), (0, i * lineY)
                )
            elif i == 7:
                im.paste(
                    Image.new("RGB", (lineX, lineY), (255, 70, 70)), (0, i * lineY)
                )
        # match
        d.text(
            (10, 10),
            match["map"] + " | " + match["gameMode"],
            font=font,
            fill=(0, 0, 0),
        )
        d.text((10, 110), "Blue Team", font=font, fill=(0, 0, 0))
        d.text((10, 710), "Red Team", font=font, fill=(0, 0, 0))
        for y in range(110, 711, 600):
            d.text((310, y), "Name", font=font, fill=(0, 0, 0))
            d.text((810, y), "Tier", font=font, fill=(0, 0, 0))
            d.text((1380, y), "Ratio", font=font, fill=(0, 0, 0))
            d.text((1580, y), "Wins", font=font, fill=(0, 0, 0))
            d.text((1720, y), "Losses", font=font, fill=(0, 0, 0))
        # participants
        initial_y = 210

        for data, i in zip(participants, range(1, 11)):
            im.paste(
                im=self.getImage(
                    latest["n"]["champion"], "champion", data["championId"]
                ),
                box=(10, initial_y),
            )
            im.paste(
                im=self.getImage(latest["v"], "spell", data["sp1"]),
                box=(110, initial_y),
            )
            im.paste(
                im=self.getImage(latest["v"], "spell", data["sp2"]),
                box=(210, initial_y),
            )
            d.text((310, initial_y), data["summonerName"], font=font, fill=(0, 0, 0))
            if data["tier"] != "unranked":
                tier_image = self.getImage(latest["v"], "tier", data["tier"])
                im.paste(tier_image, (810, initial_y), tier_image)
            d.text(
                (950, initial_y),
                data["tier"] + " " + data["rank"],
                font=font,
                fill=(0, 0, 0),
            )
            if type(data["avarage"]) is float:
                d.text(
                    (1380, initial_y),
                    str(data["avarage"]) + "%",
                    font=font,
                    fill=(0, 0, 0),
                )
            d.text((1580, initial_y), str(data["wins"]), font=font, fill=(0, 0, 0))
            d.text((1720, initial_y), str(data["losses"]), font=font, fill=(0, 0, 0))

            if i == 5:
                initial_y += 200
            else:
                initial_y += 100

        return im

    def getImage(self, version, type, name):
        if type == "champion":
            url = (
                "https://ddragon.leagueoflegends.com/cdn/"
                + version
                + "/img/champion/"
                + name
                + ".png"
            )
            try:
                res = request.urlopen(url).read()
            except Exception:
                img = Image.new("RGB", (80, 80))
            else:
                img = Image.open(BytesIO(res))
                img = img.resize((80, 80))
            return img
        elif type == "spell":
            url = (
                "https://ddragon.leagueoflegends.com/cdn/"
                + version
                + "/img/spell/"
                + name
                + ".png"
            )
            res = request.urlopen(url).read()
            img = Image.open(BytesIO(res))
            img = img.resize((80, 80))
            return img
        elif type == "tier":
            img = Image.open("./assets/" + name + ".png")
            img = img.resize((80, 80))
            return img
