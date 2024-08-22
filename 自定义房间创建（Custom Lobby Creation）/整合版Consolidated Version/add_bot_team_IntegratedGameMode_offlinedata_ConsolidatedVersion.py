from lcu_driver import Connector
import pandas, random, time

#=============================================================================
# * 声明（Declaration）
#=============================================================================
# 作者（Author）：       XHXIAIEIN
# 更新（Last update）：  2021/01/08
# 主页（Home page）：    https://github.com/XHXIAIEIN/LeagueCustomLobby/
#=============================================================================

#-----------------------------------------------------------------------------
# 工具库（Tool library）
#-----------------------------------------------------------------------------
#  - lcu-driver 
#    https://github.com/sousa-andre/lcu-driver
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# 获取自定义模式电脑玩家列表（Get access to the bot list in Custom）
#-----------------------------------------------------------------------------
localdata = pandas.read_excel("../../available-bots.xlsx", sheet_name = "Sheet2", index_col = 0, usecols = list(range(1, 5)), skiprows = [1])
names = {championId: localdata.at[championId, "name"] for championId in localdata.index}
aliases = {championId: localdata.at[championId, "alias"] for championId in localdata.index}
botPositions_CN = {"TOP": "上路", "JUNGLE": "打野", "MIDDLE": "中路", "BOTTOM": "下路", "UTILITY": "辅助"}
all_bots = list(names.keys())
print("是否查看可用电脑玩家列表？（输入任意键查看，否则不查看）\nCheck the availbale-bots list? (Any keys for Y, or null for N)")
check_botlist = input()
if check_botlist != "":
    print("*****************************************************************************")
    print("championId\t" + "{0:^14}".format("name") + "\t" + "{0:^14}".format("alias"))
    for championId in localdata.index:
        print("{0:<10}".format(str(championId)) + "\t" + "{0:<14}".format(names[championId]) + "\t" + "{0:<14}".format(aliases[championId]))
    print("*****************************************************************************\n")

connector = Connector()

#-----------------------------------------------------------------------------
# 获得召唤师数据（Get access to summoner data）
#-----------------------------------------------------------------------------
async def get_summoner_data(connection):
    data = await connection.request("GET", "/lol-summoner/v1/current-summoner")
    summoner = await data.json()
    print(f"displayName:    {summoner['displayName']}")
    print(f"summonerId:     {summoner['summonerId']}")
    print(f"puuid:          {summoner['puuid']}")
    print("-")


#-----------------------------------------------------------------------------
#  lockfile
#-----------------------------------------------------------------------------
async def get_lockfile(connection):
    import os
    path = os.path.join(connection.installation_path.encode("gb18030").decode("utf-8"), "lockfile")
    if os.path.isfile(path):
        file = open(path, "r")
        text = file.readline().split(":")
        file.close()
        print(connection.address)
        print(f"riot    {connection.auth_key}")
        return connection.auth_key
    return None

#-----------------------------------------------------------------------------
# 创建自定义房间（Create a custom lobby）
#-----------------------------------------------------------------------------
async def create_custom_lobby(connection):
    data = await connection.request("GET", "/lol-summoner/v1/current-summoner")
    summoner = await data.json()
    gamemodes = ["CLASSIC", "ARAM", "PRACTICETOOL", "NEXUSBLITZ", "GAMEMODEX"]
    mapId = [11, 12, 11, 21, 21]
    print("请选择自定义房间的游戏模式：\nPlease select a game mode of the lobby:\n1\t召唤师峡谷（Summoner's Rift）\n2\t嚎哭深渊（Howling Abyss）\n3\t训练模式（Practice Tool）\n4\t极限闪击（不可用）【Nexus Blitz (Unavailable)】\n5\t极限闪击（Nexus Blitz）")
    while True:
        typeNumber = input()
        if typeNumber == "":
            continue
        elif typeNumber in map(str, range(1, 6)):
            typeNumber = int(typeNumber)
            print("请选择自定义房间的游戏类型：\nPlease select a game type of the lobby:\n1\t自选模式（Blind Pick）\n2\t征召模式（Draft Mode）\n4\t全随机模式（All Random）\n6\t竞技征召模式（Tournament Draft）")
            while True:
                mutatorId = input()
                if mutatorId == "":
                    continue
                elif mutatorId in {"1", "2", "4", "6"}:
                    mutatorId = int(mutatorId)
                    custom = {
                        "customGameLobby": {
                            "configuration": {
                                "gameMode": gamemodes[typeNumber - 1],
                                "gameMutator": "",
                                "gameServerRegion": "",
                                "mapId": mapId[typeNumber - 1],
                                "mutators": {
                                    "id": mutatorId
                                },
                            "spectatorPolicy": "AllAllowed",
                            "teamSize": 5
                            },
                            "lobbyName": summoner["gameName"] + "'s Game",
                            "lobbyPassword": ""
                        },
                        "isCustom": True
                    }
                    await connection.request("POST", "/lol-lobby/v2/lobby", data = custom)
                    break
                else:
                    print("游戏类型输入错误！请重新输入：\nError input of game type! Please try again:")
            break
        else:
            print("游戏模式输入错误！请重新输入：\nError input of game mode! Please try again:")

#-----------------------------------------------------------------------------
# 批量添加机器人（Add a batch of bots）
#-----------------------------------------------------------------------------
async def add_bots_team1(connection):
    lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
    maxTeamSize = lobby_information["gameConfig"]["maxTeamSize"]
    current_summonerId = (await (await connection.request("GET", "/lol-summoner/v1/current-summoner")).json())["summonerId"]
    LoLChampions = await (await connection.request("GET", f"/lol-champions/v1/inventories/{current_summonerId}/champions")).json()
    LoLChampions = {champion["id"]: champion for champion in LoLChampions}
    recommended_position_for_champion = await (await connection.request("GET", "/lol-perks/v1/recommended-champion-positions")).json()
    recommended_position_for_champion_keys = list(recommended_position_for_champion.keys())
    for championId in recommended_position_for_champion_keys:
        if not int(championId) in all_bots:
            del recommended_position_for_champion[championId]
    botPositions = set()
    for champion in recommended_position_for_champion.values():
        botPositions |= set(champion["recommendedPositions"])
    #将botPositions排序整理为["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    botPositions = list(botPositions)
    botPositions_tmp = []
    for position in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]:
        if position in botPositions:
            botPositions.remove(position)
            botPositions_tmp.append(position)
    botPositions = botPositions_tmp + botPositions
    recommended_champion_for_position = {} #用于生成某条分路的随机英雄（Used to generate random champions of specific positions respectively）
    for position in botPositions:
        recommended_champion_for_position[position] = []
    for championId in recommended_position_for_champion:
        for position in recommended_position_for_champion[championId]["recommendedPositions"]:
            recommended_champion_for_position[position].append(int(championId))
    for position in recommended_champion_for_position:
        recommended_champion_for_position[position].sort()
    botDifficulty = ["EASY", "MEDIUM", "RSINTRO", "RSBEGINNER", "RSINTERMEDIATE"]
    #botPositions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    print("队伍1：请选择自选电脑玩家或者随机生成电脑玩家：\nTeam 1: Please select the option to generate bot players:\n0\t跳过该队伍（Skip this team）\n1\t完全随机生成（Completely Randomly）\n2\t按照推荐分路随机生成（Randomly according to Recommended Positions）\n3\t自选（By Picking）")
    while True:
        o = input()
        if o == "":
            continue
        elif o == "0":
            return 0
        elif o[0] == "1":
            print("请输入电脑玩家数量：\nPlease enter the number of bot players:")
            while True:
                i = input()
                if i == "":
                    continue
                elif i in map(str, range(1, maxTeamSize + 1)):
                    i = int(i)
                    while True:
                        team = random.sample(all_bots, i)
                        print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                        for j in team:
                            print("{0:<14}".format(names[j]) + "\t" + "{0:<14}".format(aliases[j]) + "\t" + str(recommended_position_for_champion[str(j)]["recommendedPositions"]))
                        print("*****************************************************************************\n是否重新随机英雄？（输入任意键以重新随机，否则进行下一步）\nDo you want to regenerate the champions? (Input anything to reroll, or null to enter the next step)")
                        if input() == "":
                            break
                    break
                else:
                    print("电脑玩家数量不合法！请重新输入：\nIllegal bot players number! Please try again:")
            break
        elif o[0] == "2":
            while True:
                team = []
                for position in botPositions:
                    team += random.sample(recommended_champion_for_position[position], 1)
                print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                for i in range(len(team)):
                    print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botPositions[i])
                print("*****************************************************************************\n是否重新随机英雄？（输入任意键以重新随机，否则进行下一步）\nDo you want to regenerate the champions? (Input anything to reroll, or null to enter the next step)")
                tmp = input()
                if tmp == "" or tmp[0] == "s":
                    break
            if tmp != "" and tmp[0] == "s": #隐藏功能：自行指定（Hidden function: manually specify the champions）
                print('''请按照“上路—打野—中路—下路—辅助”的顺序逐行输入电脑玩家的英雄序号：\nPlease input the bot championIds in the "TOP-JUNGLE-MIDDLE-BOTTOM-UTILITY" order, one bot per line:''')
                team = []
                for position in botPositions:
                    while True:
                        try:
                            championId = input()
                            if championId == "":
                                continue
                            else:
                                championId = int(championId)
                                if championId in recommended_champion_for_position[position]:
                                    team.append(championId)
                                    print("您已选择以下英雄：\nYou have selected the bot champions as follows:\n*****************************************************************************")
                                    for i in range(len(team)):
                                        print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botPositions[i])
                                    print("*****************************************************************************")
                                    break
                                elif championId in all_bots:
                                    recommended_position_str_zh = "、".join(list(map(lambda x: botPositions_CN[x], recommended_position_for_champion[str(championId)]["recommendedPositions"])))
                                    recommended_position_str_en = ", ".join(recommended_position_for_champion[str(championId)]["recommendedPositions"])
                                    print(f"{names[championId]}的推荐路线是{recommended_position_str_zh}。请选择一位适合{botPositions_CN[position]}的英雄，或者在选择{recommended_position_str_zh}位英雄时输入该英雄的序号。\nThe recommended positions for {aliases[championId]} include {recommended_position_str_en}. Please select a champion whose recommended positions include {position}, or input this championId when selecting champions of the following lane(s): {recommended_position_str_en}.")
                                elif championId in LoLChampions:
                                    print(f"没有名为{LoLChampions[championId]["name"]}的电脑玩家。请对照可用电脑玩家工作簿的第一张工作表选择一个{botPositions_CN[position]}英雄。\nThere's not a bot named {LoLChampions[championId]["alias"]}. Please refer to Sheet1 of the available-bots workbook and select a {position} champion.")
                                else:
                                    print(f"没有序号为{championId}的英雄。请重新输入！\nNo champion with championId {championId}. Please try again!")
                        except ValueError:
                            print("您的输入有误！请输入一个正整数。\nERROR input of championId! Please submit a positive integer.")
            break
        else:
            print("请输入电脑玩家的id，以空格为分隔符：\nPlease input the ids of bot players, split by space:")
            while True:
                try:
                    team = list(map(int, input().split()))
                except ValueError:
                    print("您的输入有误，请重新输入！\nInput ERROR! Please try again!")
                else:
                    break
            print("您已选择以下英雄：\nYou have selected the bot champions as follows:\n*****************************************************************************")
            for j in team:
                print("{0:<14}".format(names[j]) + "\t" + "{0:<14}".format(aliases[j]) + "\t" + str(recommended_position_for_champion[str(j)]["recommendedPositions"]))
            print("*****************************************************************************")
            break

    team1 = team[:]
    popped = 0
    print("是否设定电脑玩家难度一致？（输入任意键设定为不一致，否则一致）\nSet all botDifficulties identical? (Any keys for N, or null for Y)")
    botDifficulty_consistency = input() == ""
    if botDifficulty_consistency:
        print(f"请输入电脑玩家的难度：\nPlease enter the botDifficulty: (among {botDifficulty})")
        while True:
            botDifficulty_team = input()
            if botDifficulty_team == "":
                continue
            elif botDifficulty_team in botDifficulty:
                break
            else:
                print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
        if o[0] == "2":
            botParameter = []
            botPosition_team = botPositions[:]
            for i in range(len(team)):
                Id = team[i]
                bot = {"championId": Id, "botDifficulty": botDifficulty_team, "teamId": "100", "position": botPositions[i]}
                response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
        else:
            print(f"请依次输入电脑玩家角色定位：\nPlease enter the botPositions: (among {botPositions})")
            botPosition_team = []
            botParameter = []
            for i in range(len(team)):
                Id = team[i]
                while True:
                    botPosition_tmp = input()
                    if botPosition_tmp == "":
                        continue
                    elif botPosition_tmp in botPositions:
                        if (Id, botPosition_tmp) in botParameter:
                            team1.pop(i - popped)
                            popped += 1
                        else:
                            botPosition_team.append(botPosition_tmp)
                            botParameter.append((Id, botPosition_tmp))
                        bot = {"championId": Id, "botDifficulty": botDifficulty_team, "teamId": "100", "position": botPosition_tmp}
                        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                        break
                    else:
                        print(f"电脑玩家角色定位错误！请选择{botPositions}中的一个：\nError input of botDifficulty! Please choose among {botPositions}:")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team1)):
            print("{0:<14}".format(names[team1[i]]) + "\t" + "{0:<14}".format(aliases[team1[i]]) + "\t" + botDifficulty_team + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")
    else:
        if o[0] == "2":
            print(f"请依次输入电脑玩家的难度：\nPlease enter the botDifficulty: (among {botDifficulty})")
            botDifficulty_team = []
            botPosition_team = botPositions[:]
            botParameter = []
            for i in range(len(team)):
                Id = team[i]
                botPosition_tmp = botPositions[i]
                while True:
                    botDifficulty_tmp = input()
                    if botDifficulty_tmp == "":
                        continue
                    elif botDifficulty_tmp in botDifficulty:
                        if (Id, botDifficulty_tmp, botPosition_tmp) in botParameter:
                            team1.pop(i - popped)
                            popped += 1
                        else:
                            botDifficulty_team.append(botDifficulty_tmp)
                            botParameter.append((Id, botDifficulty_tmp, botPosition_tmp))
                        bot = {"championId": Id, "botDifficulty": botDifficulty_tmp, "teamId": "100", "position": botPosition_tmp}
                        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                        break
                    else:
                        print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
        else:
            print(f"请依次输入电脑玩家的难度和角色定位，以空格为分隔符：\nPlease enter the botDifficulty (among {botDifficulty}) and role (among {botPositions}), split by space:")
            botDifficulty_team = []
            botPosition_team = []
            botParameter = [] #房间内无法存在相同参数的两个电脑玩家（There can't be two bots with the same parameters in a lobby）
            for i in range(len(team)):
                Id = team[i]
                while True:
                    tmp = input()
                    if tmp == "":
                        continue
                    else:
                        try:
                            botDifficulty_tmp, botPosition_tmp = tmp.split()
                        except ValueError:
                            print("您的输入格式有误！请重新输入。\nERROR format of input! Please try again.")
                        else:
                            if botDifficulty_tmp in botDifficulty and botPosition_tmp in botPositions:
                                if (Id, botDifficulty_tmp, botPosition_tmp) in botParameter:
                                    team1.pop(i - popped)
                                    popped += 1
                                else:
                                    botDifficulty_team.append(botDifficulty_tmp)
                                    botPosition_team.append(botPosition_tmp)
                                    botParameter.append((Id, botDifficulty_tmp, botPosition_tmp))
                                bot = {"championId": Id, "botDifficulty": botDifficulty_tmp, "teamId": "100", "position": botPosition_tmp}
                                response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                                break
                            elif not botDifficulty_tmp in botDifficulty and botPosition_tmp in botPositions:
                                print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
                            elif botDifficulty_tmp in botDifficulty and not botPosition_tmp in botPositions:
                                print(f"电脑玩家角色定位输入错误！请选择{botPositions}中的一个：\nError input of botPositions! Please choose among {botPositions}:")
                            else:
                                print(f"电脑玩家难度和角色定位输入错误！\nError input of botDifficulty!\n请选择{botDifficulty}中的一个作为电脑玩家难度。\nPlease choose among {botDifficulty} as botDifficulty.\n请选择{botPositions}中的一个作为电脑玩家角色定位。\nPlease choose among {botDifficulty} as botPositions.")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team1)):
            print("{0:<14}".format(names[team1[i]]) + "\t" + "{0:<14}".format(aliases[team1[i]]) + "\t" + botDifficulty_team[i] + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")
    time.sleep(2)

async def add_bots_team2(connection):
    lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
    maxTeamSize = lobby_information["gameConfig"]["maxTeamSize"]
    current_summonerId = (await (await connection.request("GET", "/lol-summoner/v1/current-summoner")).json())["summonerId"]
    LoLChampions = await (await connection.request("GET", f"/lol-champions/v1/inventories/{current_summonerId}/champions")).json()
    LoLChampions = {champion["id"]: champion for champion in LoLChampions}
    recommended_position_for_champion = await (await connection.request("GET", "/lol-perks/v1/recommended-champion-positions")).json()
    recommended_position_for_champion_keys = list(recommended_position_for_champion.keys())
    for championId in recommended_position_for_champion_keys:
        if not int(championId) in all_bots:
            del recommended_position_for_champion[championId]
    botPositions = set()
    for champion in recommended_position_for_champion.values():
        botPositions |= set(champion["recommendedPositions"])
    #将botPositions排序整理为["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    botPositions = list(botPositions)
    botPositions_tmp = []
    for position in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]:
        if position in botPositions:
            botPositions.remove(position)
            botPositions_tmp.append(position)
    botPositions = botPositions_tmp + botPositions
    recommended_champion_for_position = {} #用于生成某条分路的随机英雄（Used to generate random champions of specific positions respectively）
    for position in botPositions:
        recommended_champion_for_position[position] = []
    for championId in recommended_position_for_champion:
        for position in recommended_position_for_champion[championId]["recommendedPositions"]:
            recommended_champion_for_position[position].append(int(championId))
    for position in recommended_champion_for_position:
        recommended_champion_for_position[position].sort()
    botDifficulty = ["EASY", "MEDIUM", "RSINTRO", "RSBEGINNER", "RSINTERMEDIATE"]
    #botPositions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    print("队伍2：请选择自选电脑玩家或者随机生成电脑玩家：\nTeam 2: Please select the option to generate bot players:\n0\t跳过该队伍（Skip this team）\n1\t完全随机生成（Completely Randomly）\n2\t按照推荐分路随机生成（Randomly according to Recommended Positions）\n3\t自选（By Picking）")
    while True:
        o = input()
        if o == "":
            continue
        elif o == "0":
            return 0
        elif o[0] == "1":
            print("请输入电脑玩家数量：\nPlease enter the number of bot players:")
            while True:
                i = input()
                if i == "":
                    continue
                elif i in map(str, range(1, maxTeamSize + 1)):
                    i = int(i)
                    while True:
                        team = random.sample(all_bots, i)
                        print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                        for j in team:
                            print("{0:<14}".format(names[j]) + "\t" + "{0:<14}".format(aliases[j]) + "\t" + str(recommended_position_for_champion[str(j)]["recommendedPositions"]))
                        print("*****************************************************************************\n是否重新随机英雄？（输入任意键以重新随机，否则进行下一步）\nDo you want to regenerate the champions? (Input anything to reroll, or null to enter the next step)")
                        if input() == "":
                            break
                    break
                else:
                    print("电脑玩家数量不合法！请重新输入：\nIllegal bot players number! Please try again:")
            break
        elif o[0] == "2":
            while True:
                team = []
                for position in botPositions:
                    team += random.sample(recommended_champion_for_position[position], 1)
                print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                for i in range(len(team)):
                    print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botPositions[i])
                print("*****************************************************************************\n是否重新随机英雄？（输入任意键以重新随机，否则进行下一步）\nDo you want to regenerate the champions? (Input anything to reroll, or null to enter the next step)")
                tmp = input()
                if tmp == "" or tmp[0] == "s":
                    break
            if tmp != "" and tmp[0] == "s": #隐藏功能：自行指定（Hidden function: manually specify the champions）
                print('''请按照“上路—打野—中路—下路—辅助”的顺序逐行输入电脑玩家的英雄序号：\nPlease input the bot championIds in the "TOP-JUNGLE-MIDDLE-BOTTOM-UTILITY" order, one bot per line:''')
                team = []
                for position in botPositions:
                    while True:
                        try:
                            championId = input()
                            if championId == "":
                                continue
                            else:
                                championId = int(championId)
                                if championId in recommended_champion_for_position[position]:
                                    team.append(championId)
                                    print("您已选择以下英雄：\nYou have selected the bot champions as follows:\n*****************************************************************************")
                                    for i in range(len(team)):
                                        print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botPositions[i])
                                    print("*****************************************************************************")
                                    break
                                elif championId in all_bots:
                                    recommended_position_str_zh = "、".join(list(map(lambda x: botPositions_CN[x], recommended_position_for_champion[str(championId)]["recommendedPositions"])))
                                    recommended_position_str_en = ", ".join(recommended_position_for_champion[str(championId)]["recommendedPositions"])
                                    print(f"{names[championId]}的推荐路线是{recommended_position_str_zh}。请选择一位适合{botPositions_CN[position]}的英雄，或者在选择{recommended_position_str_zh}位英雄时输入该英雄的序号。\nThe recommended positions for {aliases[championId]} include {recommended_position_str_en}. Please select a champion whose recommended positions include {position}, or input this championId when selecting champions of the following lane(s): {recommended_position_str_en}.")
                                elif championId in LoLChampions:
                                    print(f"没有名为{LoLChampions[championId]["name"]}的电脑玩家。请对照可用电脑玩家工作簿的第一张工作表选择一个{botPositions_CN[position]}英雄。\nThere's not a bot named {LoLChampions[championId]["alias"]}. Please refer to Sheet1 of the available-bots workbook and select a {position} champion.")
                                else:
                                    print(f"没有序号为{championId}的英雄。请重新输入！\nNo champion with championId {championId}. Please try again!")
                        except ValueError:
                            print("您的输入有误！请输入一个正整数。\nERROR input of championId! Please submit a positive integer.")
            break
        else:
            print("请输入电脑玩家的id，以空格为分隔符：\nPlease input the ids of bot players, split by space:")
            while True:
                try:
                    team = list(map(int, input().split()))
                except ValueError:
                    print("您的输入有误，请重新输入！\nInput ERROR! Please try again!")
                else:
                    break
            print("您已选择以下英雄：\nYou have selected the bot champions as follows:\n*****************************************************************************")
            for j in team:
                print("{0:<14}".format(names[j]) + "\t" + "{0:<14}".format(aliases[j]) + "\t" + str(recommended_position_for_champion[str(j)]["recommendedPositions"]))
            print("*****************************************************************************")
            break

    team2 = team[:]
    popped = 0
    print("是否设定电脑玩家难度一致？（输入任意键设定为不一致，否则一致）\nSet all botDifficulties identical? (Any keys for N, or null for Y)")
    botDifficulty_consistency = input() == ""
    if botDifficulty_consistency:
        print(f"请输入电脑玩家的难度：\nPlease enter the botDifficulty: (among {botDifficulty})")
        while True:
            botDifficulty_team = input()
            if botDifficulty_team == "":
                continue
            elif botDifficulty_team in botDifficulty:
                break
            else:
                print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
        if o[0] == "2":
            botParameter = []
            botPosition_team = botPositions[:]
            for i in range(len(team)):
                Id = team[i]
                bot = {"championId": Id, "botDifficulty": botDifficulty_team, "teamId": "200", "position": botPositions[i]}
                response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
        else:
            print(f"请依次输入电脑玩家角色定位：\nPlease enter the botPositions: (among {botPositions})")
            botPosition_team = []
            botParameter = []
            for i in range(len(team)):
                Id = team[i]
                while True:
                    botPosition_tmp = input()
                    if botPosition_tmp == "":
                        continue
                    elif botPosition_tmp in botPositions:
                        if (Id, botPosition_tmp) in botParameter:
                            team2.pop(i - popped)
                            popped += 1
                        else:
                            botPosition_team.append(botPosition_tmp)
                            botParameter.append((Id, botPosition_tmp))
                        bot = {"championId": Id, "botDifficulty": botDifficulty_team, "teamId": "200", "position": botPosition_tmp}
                        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                        break
                    else:
                        print(f"电脑玩家角色定位错误！请选择{botPositions}中的一个：\nError input of botDifficulty! Please choose among {botPositions}:")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team2)):
            print("{0:<14}".format(names[team2[i]]) + "\t" + "{0:<14}".format(aliases[team2[i]]) + "\t" + botDifficulty_team + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")
    else:
        if o[0] == "2":
            print(f"请依次输入电脑玩家的难度：\nPlease enter the botDifficulty: (among {botDifficulty})")
            botDifficulty_team = []
            botPosition_team = botPositions[:]
            botParameter = []
            for i in range(len(team)):
                Id = team[i]
                botPosition_tmp = botPositions[i]
                while True:
                    botDifficulty_tmp = input()
                    if botDifficulty_tmp == "":
                        continue
                    elif botDifficulty_tmp in botDifficulty:
                        if (Id, botDifficulty_tmp, botPosition_tmp) in botParameter:
                            team2.pop(i - popped)
                            popped += 1
                        else:
                            botDifficulty_team.append(botDifficulty_tmp)
                            botParameter.append((Id, botDifficulty_tmp, botPosition_tmp))
                        bot = {"championId": Id, "botDifficulty": botDifficulty_tmp, "teamId": "200", "position": botPosition_tmp}
                        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                        break
                    else:
                        print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
        else:
            print(f"请依次输入电脑玩家的难度和角色定位，以空格为分隔符：\nPlease enter the botDifficulty (among {botDifficulty}) and role (among {botPositions}), split by space:")
            botDifficulty_team = []
            botPosition_team = []
            botParameter = [] #房间内无法存在相同参数的两个电脑玩家（There can't be two bots with the same parameters in a lobby）
            for i in range(len(team)):
                Id = team[i]
                while True:
                    tmp = input()
                    if tmp == "":
                        continue
                    else:
                        try:
                            botDifficulty_tmp, botPosition_tmp = tmp.split()
                        except ValueError:
                            print("您的输入格式有误！请重新输入。\nERROR format of input! Please try again.")
                        else:
                            if botDifficulty_tmp in botDifficulty and botPosition_tmp in botPositions:
                                if (Id, botDifficulty_tmp, botPosition_tmp) in botParameter:
                                    team2.pop(i - popped)
                                    popped += 1
                                else:
                                    botDifficulty_team.append(botDifficulty_tmp)
                                    botPosition_team.append(botPosition_tmp)
                                    botParameter.append((Id, botDifficulty_tmp, botPosition_tmp))
                                bot = {"championId": Id, "botDifficulty": botDifficulty_tmp, "teamId": "200", "position": botPosition_tmp}
                                response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                                break
                            elif not botDifficulty_tmp in botDifficulty and botPosition_tmp in botPositions:
                                print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
                            elif botDifficulty_tmp in botDifficulty and not botPosition_tmp in botPositions:
                                print(f"电脑玩家角色定位输入错误！请选择{botPositions}中的一个：\nError input of botPositions! Please choose among {botPositions}:")
                            else:
                                print(f"电脑玩家难度和角色定位输入错误！\nError input of botDifficulty!\n请选择{botDifficulty}中的一个作为电脑玩家难度。\nPlease choose among {botDifficulty} as botDifficulty.\n请选择{botPositions}中的一个作为电脑玩家角色定位。\nPlease choose among {botDifficulty} as botPositions.")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team2)):
            print("{0:<14}".format(names[team2[i]]) + "\t" + "{0:<14}".format(aliases[team2[i]]) + "\t" + botDifficulty_team[i] + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")

#-----------------------------------------------------------------------------
# 获取房间信息（Get lobby information）
#-----------------------------------------------------------------------------
async def get_lobby_information(connection):
    lobby_information = await connection.request("GET", "/lol-lobby/v2/lobby")
    print(await lobby_information.json())
    time.sleep(5)

#-----------------------------------------------------------------------------
# websocket
#-----------------------------------------------------------------------------
@connector.ready
async def connect(connection):
    await get_summoner_data(connection)
    #await create_custom_lobby(connection)
    await add_bots_team1(connection)
    await add_bots_team2(connection)
    time.sleep(0.1)
    await get_lobby_information(connection)

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------
connector.start()
