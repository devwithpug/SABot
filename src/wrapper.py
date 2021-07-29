import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def get_match_data(match, queues, maps):
    match_data = {}

    try:
        queue = queues[str(match["gameQueueConfigId"])]

        if queue["detailedDescription"] == "":
            match_data["gameMode"] = queue["description"]
        else:
            match_data["gameMode"] = queue["detailedDescription"]

        for _map in maps:
            if _map["id"] == match["mapId"]:
                match_data["map"] = _map["name"]
                break

    except KeyError:
        match_data["map"] = match["gameMode"]
        match_data["gameMode"] = match["gameType"]
    
    return match_data


def get_participants(match, champ_list, spell_list):

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
    for champ in champ_list["data"]:
        row = champ_list["data"][champ]
        champ_dict[row["key"]] = row["id"]
    for spell in spell_list["data"]:
        row = spell_list["data"][spell]
        spell_dict[row["key"]] = row["id"]
    for row in participants:
        try:
            row["championId"] = champ_dict[str(row["championId"])]
        except KeyError:
            row["championId"] = "NULL"
        row["sp1"] = spell_dict[str(row["sp1"])]
        row["sp2"] = spell_dict[str(row["sp2"])]

    return participants


def update_participants(i, participants, row):

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
        else:
            participants[i]["tier"] = row[ranked_solo_index]["tier"]
            participants[i]["rank"] = row[ranked_solo_index]["rank"]
            participants[i]["wins"] = row[ranked_solo_index]["wins"]
            participants[i]["losses"] = row[ranked_solo_index]["losses"]
            participants[i]["avarage"] = round(
                row[ranked_solo_index]["wins"] / (row[ranked_solo_index]["wins"] + row[ranked_solo_index]["losses"]) * 100, 2
                )
    else:
        participants[i]["tier"] = "unranked"
        participants[i]["rank"] = ""
        participants[i]["wins"] = ""
        participants[i]["losses"] = ""
        participants[i]["avarage"] = ""


def draw_image(latest, data, locale):

    match = data['match_data']
    participants = data['participants']

    # background
    lineX = 1920
    lineY = 100

    try:
        font = ImageFont.truetype("NanumGothic.ttf", 50)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", 50)  # Window default font
        except OSError:
            font = ImageFont.truetype(
                "AppleSDGothicNeo.ttc", 50
            )  # MacOS default font

    im = Image.new("RGBA", (lineX, lineY * 13), (255, 255, 255))
    d = ImageDraw.Draw(im)
    line = Image.new("RGB", (lineX, lineY), (230, 230, 230))

    for i in range(0, 13):
        if i % 2 == 0:
            im.paste(line, (0, i * lineY))
        elif i == 1:
            im.paste(Image.new("RGB", (lineX, lineY), (85, 85, 255)), (0, i * lineY))
        elif i == 7:
            im.paste(Image.new("RGB", (lineX, lineY), (255, 70, 70)), (0, i * lineY))

    # match
    d.text((10, 10), match["map"] + " | " + match["gameMode"], font=font, fill=(0, 0, 0))
    d.text((10, 110), locale['blue_team'], font=font, fill=(0, 0, 0))
    d.text((10, 710), locale['red_team'], font=font, fill=(0, 0, 0))

    for y in range(110, 711, 600):
        d.text((310, y), locale['name'], font=font, fill=(0, 0, 0))
        d.text((810, y), locale['tier'], font=font, fill=(0, 0, 0))
        d.text((1380, y), locale['ratio'], font=font, fill=(0, 0, 0))
        d.text((1580, y), locale['wins'], font=font, fill=(0, 0, 0))
        d.text((1720, y), locale['losses'], font=font, fill=(0, 0, 0))

    # participants
    initial_y = 210

    for data, i in zip(participants, range(1, 11)):
        im.paste(
            im=get_image(latest["n"]["champion"], "champion", data["championId"]),
            box=(10, initial_y),
        )
        im.paste(
            im=get_image(latest["v"], "spell", data["sp1"]),
            box=(110, initial_y),
        )
        im.paste(
            im=get_image(latest["v"], "spell", data["sp2"]),
            box=(210, initial_y),
        )
        d.text((310, initial_y), data["summonerName"], font=font, fill=(0, 0, 0))
        if data["tier"] != "unranked":
            tier_image = get_image(latest["v"], "tier", data["tier"])
            im.paste(tier_image, (810, initial_y), tier_image)
        d.text((950, initial_y), data["tier"] + " " + data["rank"], font=font, fill=(0, 0, 0))
        
        if type(data["avarage"]) is float:
            d.text((1380, initial_y), str(data["avarage"]) + "%", font=font, fill=(0, 0, 0))
        
        d.text((1580, initial_y), str(data["wins"]), font=font, fill=(0, 0, 0))
        d.text((1720, initial_y), str(data["losses"]), font=font, fill=(0, 0, 0))

        if i == 5:
            initial_y += 200
        else:
            initial_y += 100

    return im


def get_image(version, type, name):
    if type == "champion":
        url = (
            "https://ddragon.leagueoflegends.com/cdn/"
            + version
            + "/img/champion/"
            + name
            + ".png"
        )
        response = requests.get(url)
        if response.status_code != 200:
            img = Image.new("RGB", (80, 80))
        else:
            img = Image.open(BytesIO(response.content))
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
        response = requests.get(url)
        if response.status_code != 200:
            img = Image.new("RGB", (80, 80))
        else:
            img = Image.open(BytesIO(response.content))
            img = img.resize((80, 80))
        return img

    elif type == "tier":
        img = Image.open("../assets/" + name + ".png")
        img = img.resize((80, 80))
        return img
