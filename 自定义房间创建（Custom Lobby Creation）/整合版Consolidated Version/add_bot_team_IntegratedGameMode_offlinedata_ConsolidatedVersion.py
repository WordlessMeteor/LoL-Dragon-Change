from lcu_driver import Connector

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
import pandas,random,time
localdata = pandas.read_excel("../../available-bots.xlsx", sheet_name = "Sheet2")
champions_CN = { int(localdata["championId"][bot]): localdata["name"][bot] for bot in range(len(localdata)) }
champions_EN = { int(localdata["championId"][bot]): localdata["alias"][bot] for bot in range(len(localdata)) }
all_champions = list(champions_CN.keys())
print("是否查看可用电脑玩家列表？（输入任意键查看，否则不查看）\nCheck the availbale-bots list? (Any keys for Y, or null for N)")
check_botlist = input()
if check_botlist != "":
    print("*****************************************************************************")
    print("championId\t" + "{0:^14}".format("name") + "\t" + "{0:^14}".format("alias"))
    for h in range(len(localdata)):
        print("{0:<10}".format(str(localdata["championId"][h])) + "\t" + "{0:<14}".format(localdata["name"][h]) + "\t" + "{0:<14}".format(localdata["alias"][h]))
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
    gameMode = ["CLASSIC","ARAM","PRACTICETOOL","NEXUSBLITZ"]
    mapId = [11,12,11,21]
    print("请选择自定义房间的游戏模式：\nPlease select a game mode of the lobby:\n1\t召唤师峡谷（Summoner's Rift）\n2\t嚎哭深渊（Howling Abyss）\n3\t训练模式（Practice Tool）\n4\t极限闪击（国服不可用）【Nexus Blitz (Unavailable on Chinese servers)】")
    while True:
        TypeNumber = input()
        if TypeNumber == "":
            continue
        elif TypeNumber in {"1","2","3","4"}:
            TypeNumber = int(TypeNumber)
            print("请选择自定义房间的游戏类型：\nPlease select a game type of the lobby:\n1\t自选模式（Blind Pick）\n2\t征召模式（Draft Mode）\n4\t全随机模式（All Random）\n6\t竞技征召模式（国服正式服不可用）【Tournament Draft (Unavailable on Chinese Live servers)】")
            while True:
                mutatorid = input()
                if mutatorid == "":
                    continue
                elif mutatorid in {"1","2","4","6"}:
                    mutatorid = int(mutatorid)
                    custom = {
                        "customGameLobby": {
                            "configuration": {
                                "gameMode": gameMode[TypeNumber - 1],
                                "gameMutator": "",
                                "gameServerRegion": "",
                                "mapId": mapId[TypeNumber - 1],
                                "mutators": {
                                    "id": mutatorid
                                },
                            "spectatorPolicy": "AllAllowed",
                            "teamSize": 5
                            },
                            "lobbyName": summoner["gameName"] + "'s Game",
                            "lobbyPassword": ""
                        },
                        "isCustom": True
                    }
                    await connection.request("POST", "/lol-lobby/v2/lobby", data=custom)
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
    riot_client_info = await (await connection.request("GET", "/riotclient/command-line-args")).json()
    client_info = {}
    for i in range(len(riot_client_info)):
        try:
            client_info[riot_client_info[i].split("=")[0]] = riot_client_info[i].split("=")[1]
        except IndexError:
            pass
    region = client_info["--region"]
    botDifficulty1 = ["NONE", "TUTORIAL", "INTRO", "EASY", "MEDIUM", "HARD", "UBER"]
    botDifficulty2 = ["RSINTRO", "RSBEGINNER", "RSINTERMEDIATE"]
    botDifficulty = botDifficulty1 + botDifficulty2 if region == "TENCENT" else botDifficulty2
    botPosition = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    print("队伍1：请选择自选电脑玩家或者随机生成电脑玩家：\nTeam 1: Please select the option to generate bot players:\n0\t跳过该队伍（Skip this team）\n1\t随机生成（Randomly）\n2\t自选（By picking）")
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
                        team = random.sample(all_champions, i)
                        print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                        for j in team:
                            print("{0:<14}".format(champions_CN[j]) + "\t" + "{0:<14}".format(champions_EN[j]))
                        print("*****************************************************************************\n是否重新随机英雄？（输入任意键以重新随机，否则进行下一步）\nDo you want to regenerate the champions? (Input anything to reroll, or null to enter the next step)")
                        if input() == "":
                            break
                    break
                else:
                    print("电脑玩家数量不合法！请重新输入：\nIllegal bot players number! Please try again:")
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
                print("{0:<14}".format(champions_CN[j]) + "\t" + "{0:<14}".format(champions_EN[j]))
            print("*****************************************************************************")
            break

    team1 = team[:] #存储去重之后的电脑玩家序号（Stores the botIds after removing redundancy）
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
        print(f"请依次输入电脑玩家角色定位：\nPlease enter the botPosition: (among {botPosition})")
        botPosition_team = []
        botParameter = []
        for i in range(len(team)):
            Id = team[i]
            while True:
                botPosition_tmp = input()
                if botPosition_tmp == "":
                    continue
                elif botPosition_tmp in botPosition:
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
                    print(f"电脑玩家角色定位错误！请选择{botPosition}中的一个：\nError input of botDifficulty! Please choose among {botPosition}:")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team1)):
            print("{0:<14}".format(champions_CN[team1[i]]) + "\t" + "{0:<14}".format(champions_EN[team1[i]]) + "\t" + botDifficulty_team + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")
    else:
        print(f"请依次输入电脑玩家的难度和角色定位，以空格为分隔符：\nPlease enter the botDifficulty (among {botDifficulty}) and role (among {botPosition}), split by space:")
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
                        if botDifficulty_tmp in botDifficulty and botPosition_tmp in botPosition:
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
                        elif not botDifficulty_tmp in botDifficulty and botPosition_tmp in botPosition:
                            print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
                        elif botDifficulty_tmp in botDifficulty and not botPosition_tmp in botPosition:
                            print(f"电脑玩家角色定位输入错误！请选择{botPosition}中的一个：\nError input of botPosition! Please choose among {botPosition}:")
                        else:
                            print(f"电脑玩家难度和角色定位输入错误！\nError input of botDifficulty!\n请选择{botDifficulty}中的一个作为电脑玩家难度。\nPlease choose among {botDifficulty} as botDifficulty.\n请选择{botPosition}中的一个作为电脑玩家角色定位。\nPlease choose among {botDifficulty} as botPosition.")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team1)):
            print("{0:<14}".format(champions_CN[team1[i]]) + "\t" + "{0:<14}".format(champions_EN[team1[i]]) + "\t" + botDifficulty_team[i] + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")
    time.sleep(2)

async def add_bots_team2(connection):
    lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
    maxTeamSize = lobby_information["gameConfig"]["maxTeamSize"]
    riot_client_info = await (await connection.request("GET", "/riotclient/command-line-args")).json()
    client_info = {}
    for i in range(len(riot_client_info)):
        try:
            client_info[riot_client_info[i].split("=")[0]] = riot_client_info[i].split("=")[1]
        except IndexError:
            pass
    region = client_info["--region"]
    botDifficulty1 = ["NONE", "TUTORIAL", "INTRO", "EASY", "MEDIUM", "HARD", "UBER"]
    botDifficulty2 = ["RSINTRO", "RSBEGINNER", "RSINTERMEDIATE"]
    botDifficulty = botDifficulty1 + botDifficulty2 if region == "TENCENT" else botDifficulty2
    botPosition = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    print("队伍2：请选择自选电脑玩家或者随机生成电脑玩家：\nTeam 2: Please select the option to generate bot players:\n0\t跳过该队伍（Skip this team）\n1\t随机生成（Randomly）\n2\t自选（By picking）")
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
                        team = random.sample(all_champions, i)
                        print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                        for j in team:
                            print("{0:<14}".format(champions_CN[j]) + "\t" + "{0:<14}".format(champions_EN[j]))
                        print("*****************************************************************************\n是否重新随机英雄？（输入任意键以重新随机，否则进行下一步）\nDo you want to regenerate the champions? (Input anything to reroll, or null to enter the next step)")
                        if input() == "":
                            break
                    break
                else:
                    print("电脑玩家数量不合法！请重新输入：\nIllegal bot players number! Please try again:")
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
                print("{0:<14}".format(champions_CN[j]) + "\t" + "{0:<14}".format(champions_EN[j]))
            print("*****************************************************************************")
            break

    team2 = team[:] #存储去重之后的电脑玩家序号（Stores the botIds after removing redundancy）
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
        print(f"请依次输入电脑玩家角色定位：\nPlease enter the botPosition: (among {botPosition})")
        botPosition_team = []
        botParameter = []
        for i in range(len(team)):
            Id = team[i]
            while True:
                botPosition_tmp = input()
                if botPosition_tmp == "":
                    continue
                elif botPosition_tmp in botPosition:
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
                    print(f"电脑玩家角色定位错误！请选择{botPosition}中的一个：\nError input of botDifficulty! Please choose among {botPosition}:")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team2)):
            print("{0:<14}".format(champions_CN[team2[i]]) + "\t" + "{0:<14}".format(champions_EN[team2[i]]) + "\t" + botDifficulty_team + "\t" + botPosition_team[i])
        print("*****************************************************************************\n")
    else:
        print(f"请依次输入电脑玩家的难度和角色定位，以空格为分隔符：\nPlease enter the botDifficulty (among {botDifficulty}) and role (among {botPosition}), split by space:")
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
                        if botDifficulty_tmp in botDifficulty and botPosition_tmp in botPosition:
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
                        elif not botDifficulty_tmp in botDifficulty and botPosition_tmp in botPosition:
                            print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
                        elif botDifficulty_tmp in botDifficulty and not botPosition_tmp in botPosition:
                            print(f"电脑玩家角色定位输入错误！请选择{botPosition}中的一个：\nError input of botPosition! Please choose among {botPosition}:")
                        else:
                            print(f"电脑玩家难度和角色定位输入错误！\nError input of botDifficulty!\n请选择{botDifficulty}中的一个作为电脑玩家难度。\nPlease choose among {botDifficulty} as botDifficulty.\n请选择{botPosition}中的一个作为电脑玩家角色定位。\nPlease choose among {botDifficulty} as botPosition.")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team2)):
            print("{0:<14}".format(champions_CN[team2[i]]) + "\t" + "{0:<14}".format(champions_EN[team2[i]]) + "\t" + botDifficulty_team[i] + "\t" + botPosition_team[i])
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
    await get_lockfile(connection)
    #await create_custom_lobby(connection)
    await add_bots_team1(connection)
    await add_bots_team2(connection)
    time.sleep(0.1)
    await get_lobby_information(connection)

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------
connector.start()
