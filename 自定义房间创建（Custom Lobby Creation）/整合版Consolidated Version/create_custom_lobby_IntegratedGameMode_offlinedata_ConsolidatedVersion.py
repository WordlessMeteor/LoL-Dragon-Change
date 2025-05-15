from lcu_driver import Connector
import os, pandas, random, shutil, time, unicodedata, uuid
from wcwidth import wcswidth

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
roles_CN = {"assassin": "刺客", "fighter": "战士", "mage": "法师", "marksman": "射手", "support": "辅助", "tank": "坦克", "arbitrary": "任意"}
all_bots = list(names.keys())
print("是否查看可用电脑玩家列表？（输入任意键查看，否则不查看）\nCheck the availbale-bots list? (Any keys for Y, or null for N)")
check_botlist = input()
if check_botlist != "":
    print("*****************************************************************************")
    print("championId\t" + "{0:^14}".format("name") + "\t" + "{0:^14}".format("alias"))
    for championId in localdata.index:
        print("{0:<10}".format(str(championId)) + "\t" + "{0:<14}".format(names[championId]) + "\t" + "{0:<14}".format(aliases[championId]))
    print("*****************************************************************************\n")

def count_nonASCII(s: str): #统计一个字符串中占用命令行2个宽度单位的字符个数（Count the number of characters that take up 2 width unit in CMD）
    return sum([unicodedata.east_asian_width(character) in ("F", "W") for character in list(str(s))])

def format_df(df: pandas.DataFrame, width_exceed_ask: bool = True, direct_print: bool = False, print_header: bool = True, print_index: bool = False, reserve_index = False, start_index = 0, header_align: str = "^", align: str = "^", align_replicate_rule: str = "all"): #按照每列最长字符串的命令行宽度加上2，再根据每个数据的中文字符数量决定最终格式化输出的字符串宽度（Get the width of the longest string of each column, add it by 2, and substract it by the number of each cell string's Chinese characters to get the final width for each cell to print using `format` function）
    old_index = df.index
    df = df.reset_index(drop = True) #这一步至关重要，因为下面的操作前提是行号是默认的（This step is crucial, for the following operations are based on the dataframe with the default row index）
    df.index = range(start_index, len(df) + start_index)
    maxLens = {}
    maxWidth = shutil.get_terminal_size()[0]
    fields = df.columns.tolist()
    for field in fields:
        maxLens[field] = max(0 if len(df) == 0 else max(map(lambda x: wcswidth(str(x)), df[field])), wcswidth(str(field))) + 2
    index_len = max(len(str(start_index)), len(str(start_index + len(df) - 1)))
    if sum(maxLens.values()) + 2 * (len(fields) - 1) > maxWidth or print_index and index_len + sum(maxLens.values()) + 2 * len(fields) > maxWidth:
        if width_exceed_ask:
            print("单行数据字符串输出宽度超过当前终端窗口宽度！是否继续？（输入任意键继续，否则直接打印该数据框。）\nThe output width of each record string exceeds the current width of the terminal window! Continue? (Input anything to continue, or null to directly print this dataframe.)")
            if input() == "":
                #print(df)
                result = str(df)
                return (result, maxLens)
        elif direct_print:
            print("单行数据字符串输出宽度超过当前终端窗口宽度！将直接打印该数据框！\nThe output width of each record string exceeds the current width of the terminal window! The program is going to directly print this dataframe!")
            result = str(df)
            return (result, maxLens)
        else:
            print("单行数据字符串输出宽度超过当前终端窗口宽度！将继续格式化输出！\nThe output width of each record string exceeds the current width of the terminal window! The program is going on formatted printing!")
    result = ""
    #确定各列的排列方向（Determine the alignments of all columns）
    if isinstance(header_align, str) and isinstance(align, str):
        if not all(map(lambda x: x in {"<", "^", ">"}, header_align)) or not all(map(lambda x: x in {"<", "^", ">"}, align)):
            print('排列方式字符串参数错误！排列方式必须是“<”“^”或者“>”中的一个。请修改排列方式字符串参数。\nParameter ERROR of the alignment string! The alignment value must be one of {"<", "^", ">"}. Please change the alignment string parameter.')
        if len(header_align) == 0: #指定为空字符串，即默认居中输出（Specifying it as a null string means output centered by default）
            header_alignments = ["^"] * df.shape[1]
        elif len(header_align) == 1:
            header_alignments = [header_align] * df.shape[1]
        else:
            header_alignments_tmp = list(header_align)
            if len(header_align) < df.shape[1]:
                if align_replicate_rule == "last":
                    header_alignments = header_alignments_tmp + [header_alignments_tmp[-1]] * len(df.shape[1] - len(header_align))
                else:
                    if align_replicate_rule != "all":
                        print("排列方式列表补充规则不合法！将默认采用全部填充。\nAlignment list supplement rule illegal! The whole alignment string will be replicated.")
                    header_alignments = header_alignments_tmp * (df.shape[1] // len(header_align)) + header_alignments_tmp[:df.shape[1] % len(header_align)]
            else:
                header_alignments = header_alignments_tmp[:df.shape[1]]
        if len(align) == 0:
            alignments = ["^"] * df.shape[1]
        elif len(align) == 1:
            alignments = [align] * df.shape[1]
        else:
            alignments_tmp = list(align)
            if len(align) < df.shape[1]:
                if align_replicate_rule == "last":
                    alignments = alignments_tmp + [alignments_tmp[-1]] * len(df.shape[1] - len(align))
                else:
                    if align_replicate_rule != "all":
                        print("排列方式列表补充规则不合法！将默认采用全部填充。\nAlignment list supplement rule illegal! The whole alignment string will be replicated.")
                    alignments = alignments_tmp * (df.shape[1] // len(align)) + alignments_tmp[:df.shape[1] % len(align)]
            else:
                alignments = alignments_tmp[:df.shape[1]]
        if print_header:
            if print_index:
                result += " " * (index_len + 2)
            for i in range(df.shape[1]):
                field = fields[i]
                tmp = "{0:{align}{w}}".format(field, align = header_alignments[i], w = maxLens[str(field)] - count_nonASCII(str(field)))
                result += tmp
                #print(tmp, end = "")
                if i != df.shape[1] - 1:
                    result += "  "
                    #print("  ", end = "")
            result += "\n"
            #print()
        index = start_index
        for i in range(df.shape[0]):
            if print_index:
                result += "{0:>{w}}".format(old_index[index - start_index] if reserve_index else index, w = index_len) + "  "
            for j in range(df.shape[1]):
                field = fields[j]
                cell = str(list(df[field])[i])
                tmp = "{0:{align}{w}}".format(cell, align = alignments[j], w = maxLens[field] - count_nonASCII(cell))
                result += tmp
                #print(tmp, end = "")
                if j != df.shape[1] - 1:
                    result += "  "
                    #print("  ", end = "")
            if i != df.shape[0] - 1:
                result += "\n"
            #print() #注意这里的缩进和上一行不同（Note that here the indentation is different from the last line）
            index += 1
    else:
        print("排列方式参数错误！请传入字符串。\nAlignment parameter ERROR! Please pass a string instead.")
    return (result, maxLens)

connector = Connector()

#-----------------------------------------------------------------------------
# 获得召唤师数据（Get access to summoner data）
#-----------------------------------------------------------------------------
async def get_summoner_data(connection):
    data = await connection.request("GET", "/lol-summoner/v1/current-summoner")
    summoner = await data.json()
    print("displayName:    %s" %(summoner["gameName"] + "#" + summoner["tagLine"]))
    print("summonerId:     %s" %(summoner["summonerId"]))
    print("puuid:          %s" %(summoner["puuid"]))
    print("-")


#-----------------------------------------------------------------------------
#  lockfile
#-----------------------------------------------------------------------------
async def get_lockfile(connection):
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
# 检查队列可用性（Check queue availability）
#-----------------------------------------------------------------------------
async def check_available_queue(connection):
    queues = await (await connection.request("GET", "/lol-game-queues/v1/queues")).json()
    map_CN = {8: "水晶之痕", 10: "扭曲丛林", 11: "召唤师峡谷", 12: "嚎哭深渊", 14: "屠夫之桥", 16: "星界废墟", 18: "瓦洛兰城市公园", 19: "第43区", 20: "飞船坠落点", 21: "百合与莲花的神庙", 22: "聚点危机", 30: "怒火角斗场", 33: "最终都市", 35: "班德尔之森"}
    map_EN = {8: "Crystal Scar", 10: "Twisted Treeline", 11: "Summoner's Rift", 12: "Howling Abyss", 14: "Butcher's Bridge", 16: "Cosmic Ruins", 18: "Valoran City Park", 19: "Substructure 43", 20: "Crash Site", 21: "Temple of Lily and Lotus", 22: "Convergence", 30: "Rings of Wrath", 33: "Final City", 35: "The Bandlewood"}
    pickmode_CN = {"AllRandomPickStrategy": "全随机模式", "SimulPickStrategy": "自选模式", "TeamBuilderDraftPickStrategy": "征召模式", "OneTeamVotePickStrategy": "投票", "TournamentPickStrategy": "竞技征召模式", "QuickplayPickStrategy": "快速匹配", "": "待定"}
    pickmode_EN = {"AllRandomPickStrategy": "All Random", "SimulPickStrategy": "Blind Pick", "TeamBuilderDraftPickStrategy": "Draft Mode", "OneTeamVotePickStrategy": "Vote", "TournamentPickStrategy": "Tournament Draft", "QuickplayPickStrategy": "Quickplay", "": "Pending"}
    available_queues = {}
    for queue in queues:
        if queue["queueAvailability"] == "Available":
            available_queues[queue["id"]] = queue
    queue_dict = {"queueID": [], "mapID": [], "map_CN": [], "map_EN": [], "gameMode": [], "pickType_CN": [], "pickType_EN": []}
    for queue in available_queues.values():
        queue_dict["queueID"].append(queue["id"])
        queue_dict["mapID"].append(queue["mapId"])
        queue_dict["map_CN"].append(map_CN[queue["mapId"]])
        queue_dict["map_EN"].append(map_EN[queue["mapId"]])
        queue_dict["gameMode"].append(queue["name"])
        queue_dict["pickType_CN"].append(pickmode_CN[queue["gameTypeConfig"]["pickMode"]])
        queue_dict["pickType_EN"].append(pickmode_EN[queue["gameTypeConfig"]["pickMode"]])
    queue_df = pandas.DataFrame(queue_dict)
    queue_df.sort_values(by = "queueID", inplace = True, ascending = True, ignore_index = True)
    print("*****************************************************************************")
    print(format_df(queue_df)[0])
    print("*****************************************************************************")

#-----------------------------------------------------------------------------
# 创建自定义房间（Create a custom lobby）
#-----------------------------------------------------------------------------
async def create_custom_lobby(connection):
    summoner = await (await connection.request("GET", "/lol-summoner/v1/current-summoner")).json()
    gamemodes = ["CLASSIC", "ARAM", "PRACTICETOOL", "NEXUSBLITZ", "GAMEMODEX", "TUTORIAL"]
    gamemaps = {8: "水晶之痕（Crystal Scar）", 10: "扭曲丛林（Twisted Treeline）", 11: "召唤师峡谷（Summoner's Rift）", 12: "嚎哭深渊（Howling Abyss）", 14: "屠夫之桥（Butcher's Bridge）", 16: "星界废墟（Cosmic Ruins）", 18: "瓦洛兰城市公园（Valoran City Park）", 19: "第43区（Substructure 43）", 20: "飞船坠落点（Crash Site）", 21: "百合与莲花的神庙（Temple of Lily and Lotus）", 22: "聚点危机（Convergence）", 30: "怒火角斗场（Rings of Wrath）", 33: "最终都市（Final City）", 35: "班德尔之森（The Bandlewood）"}
    spectatorPolicy = ["LobbyAllowed", "FriendsAllowed", "AllAllowed", "NotAllowed"]
    defaultMapId = {"CLASSIC": 11, "ARAM": 12, "PRACTICETOOL": 11, "NEXUSBLITZ": 21, "GAMEMODEX": 21}
    print("请选择自定义房间的游戏模式：\nPlease select a game mode of the lobby:\n1\t召唤师峡谷（Summoner's Rift）\n2\t嚎哭深渊（Howling Abyss）\n3\t训练模式（Practice Tool）\n4\t极限闪击（不可用）【Nexus Blitz (Unavailable)】\n5\t极限闪击（Nexus Blitz）")
    while True:
        gameModeTypeNumber = input()
        if gameModeTypeNumber == "":
            continue
        elif gameModeTypeNumber in set(map(str, range(1, 7))):
            gameModeTypeNumber = int(gameModeTypeNumber)
            break
        else:
            print("游戏模式输入错误！请重新输入：\nError input of game mode! Please try again:")
    print("请输入地图序号：\nPlease enter a mapID:")
    mapIDs = list(gamemaps.keys())
    mapIDs.sort()
    for i in mapIDs:
        print(str(i) + "\t" + gamemaps[i])
    while True:
        mapId = input()
        if mapId == "":
            if gamemodes[gameModeTypeNumber - 1] in defaultMapId:
                mapId = defaultMapId[gamemodes[gameModeTypeNumber - 1]]
                break
        elif mapId in set(map(str, gamemaps.keys())):
            mapId = int(mapId)
            break
        else:
            print("地图序号输入错误！请重新输入：\nError input of mapID! Please try again:")
    print("请选择自定义房间的游戏类型：\nPlease select a game type of the lobby:\n1\t自选模式（Blind Pick）\n2\t征召模式（Draft Mode）\n4\t全随机模式（All Random）\n6\t竞技征召模式（Tournament Draft）\n16\t自选征召（仅测试服）【Blind Draft (Available only on PBE）】")
    while True:
        mutatorId = input()
        if mutatorId == "":
            continue
        elif mutatorId in {"1", "2", "4", "6", "16"}:
            mutatorId = int(mutatorId)
            break
        else:
            print("游戏类型输入错误！请重新输入：\nError input of game type! Please try again:")
    print("请选择自定义房间的允许观战策略：\nPlease select a spectator policy:\n1\t只允许房间内玩家（Lobby Only）\n2\t只允许好友（国服不可用）【Friends List Only (Unavailable on Chinese servers)】\n3\t所有人（国服不可用）【All (Unavailable on Chinese servers)】\n4\t无（None）")
    while True:
        customSpectatorPolicyTypeNumber = input()
        if customSpectatorPolicyTypeNumber == "":
            continue
        elif customSpectatorPolicyTypeNumber in set(map(str, range(1, 5))):
            customSpectatorPolicyTypeNumber = int(customSpectatorPolicyTypeNumber)
            break
        else:
            print("允许观战策略输入错误！请重新输入：\nError input of spectator policy! Please try again:")
    print("请依次输入对局名、队伍规模、密码（可选）：\nPlease enter the lobby's name, team size and password (optional):")
    print("对局名（Lobby Name）：", end = "")
    lobbyName = input()
    if lobbyName == "":
        region_locale = await (await connection.request("GET", "/riotclient/region-locale")).json()
        custom_game_setup_name_default_dict = {"ar_AE": "مباراة {{summonerName}}", "cs_CZ": "Hra uživatele {{summonerName}}", "el_GR": "Παιχνίδι του {{summonerName}}", "pl_PL": "Rozgrywka gracza {{summonerName}}", "ro_RO": "Jocul lui {{summonerName}}", "hu_HU": "{{summonerName}} játéka", "en_GB": "{{summonerName}}'s Game", "de_DE": "Spiel von {{summonerName}}", "es_ES": "Partida de {{summonerName}}", "it_IT": "Partita di {{summonerName}}", "fr_FR": "Partie de {{summonerName}}", "ja_JP": "{{summonerName}}の試合", "ko_KR": "{{summonerName}} 님의 게임", "es_MX": "Partida de {{summonerName}}", "es_AR": "Partida de {{summonerName}}", "pt_BR": "Partida de {{summonerName}}", "en_US": "{{summonerName}}'s Game", "en_AU": "{{summonerName}}'s Game", "ru_RU": "Игра {{summonerName}}", "tr_TR": "{{summonerName}} oyunu", "en_PH": "{{summonerName}}'s Game", "en_SG": "{{summonerName}}'s Game", "th_TH": "เกมของ {{summonerName}}", "vi_VN": "Trận của {{summonerName}}", "id_ID": "Game {{summonerName}}", "zh_MY": "{{summonerName}} 的房间", "zh_CN": "{{summonerName}}的对局", "zh_TW": "{{summonerName}} 的房間"} #来自（From）：plugins/rcp-fe-lol-parties/global/{locale}/trans.json
        lobbyName = custom_game_setup_name_default_dict.get(region_locale["locale"], "{{summonerName}}的对局").replace("{{summonerName}}", summoner["gameName"])
    print("队伍规模（Team Size）：", end = "")
    while True:
        teamsize = input()
        if teamsize == "":
            teamsize = 5
            break
        elif teamsize in set(map(str, range(1, 6))):
            teamsize = int(teamsize)
            break
        else:
            print("队伍规模输入错误！请重新输入：\nError input of team size! Please try again:")
    print("密码（Password）：", end = "")
    lobbyPassword = input()
    custom = {
        "customGameLobby": {
            "configuration": {
                "gameMode": gamemodes[gameModeTypeNumber - 1],
                "gameMutator": "",
                "gameServerRegion": "",
                "mapId": mapId,
                "mutators": {
                    "id": mutatorId
                },
            "spectatorPolicy": spectatorPolicy[customSpectatorPolicyTypeNumber - 1],
            "teamSize": teamsize
            },
            "lobbyName": lobbyName,
            "lobbyPassword": lobbyPassword
        },
        "isCustom": True
    }
    await connection.request("POST", "/lol-lobby/v2/lobby", data=custom)

#-----------------------------------------------------------------------------
# 创建队列房间（Create a queue lobby）
#-----------------------------------------------------------------------------
async def create_queue_lobby(connection):
    Client_System_States = await (await connection.request("GET", "/lol-platform-config/v1/namespaces/ClientSystemStates")).json()
    #print(Client_System_States)
    enabled_QueueId = Client_System_States["enabledQueueIdsList"]
    game_version = await (await connection.request("GET", "/lol-patch/v1/game-version")).json()
    platform_config = await (await connection.request("GET", "/lol-platform-config/v1/namespaces")).json()
    platformId = platform_config["LoginDataPacket"]["platformId"]
    for i in enabled_QueueId:
        i = int(i)
    enabled_QueueId.sort()
    print("当前可用队列房间序号：\nCurrently enabled QueueIds:")
    while True:
        await check_available_queue(connection)
        print("(" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\t" + platformId + "\t" + game_version + ")")
        print("是否刷新可用队列信息？（输入任意键不刷新，否则刷新）\nRefresh available queue information? (Submit anything to quit refreshing, or null to continue refreshing)")
        refresh = input()
        if refresh != "":
            break
##    print("*****************************************************************************")
##    print("QueueID\tmapID\t" + "{0:^14}".format("map_CN") + "\t" + "{0:^30}".format("Gamemode_CN") + "\t" + "{0:^11}".format("PickType_CN") + "\t" + "{0:^24}".format("map_EN") + "\t" + "{0:^34}".format("Gamemode_EN") + "\t" + "{0:^15}".format("PickType_EN"))
##    for i in enabled_QueueId:
##        for j in range(len(localdata)):
##            if i == localdata["QueueID"][j]:
##                print("{0:<7}".format(str(localdata["QueueID"][j])) + "\t" + "{0:<5}".format(str(localdata["mapID"][j])) + "\t" + "{0:<14}".format(localdata["map_CN"][j]) + "\t" + "{0:<30}".format(localdata["Gamemode_CN"][j]) + "\t" + "{0:<11}".format(localdata["PickType_CN"][j]) + "\t" + "{0:<24}".format(localdata["map_EN"][j]) + "\t" + "{0:<34}".format(localdata["Gamemode_EN"][j]) + "\t" + "{0:<15}".format(localdata["PickType_EN"][j]))
##                break
##    print("*****************************************************************************")
    print('请输入队列房间序号：（输入“0”以刷新可用队列信息。输入负数以退出创建。）\nPlease enter the queueID: (Enter "0" to refresh available queue information. Enter any negative number to exit creation.)')
    while True:
        try:
            lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
            if "gameConfig" in lobby_information:
                prequeueId = lobby_information["gameConfig"]["queueId"]
            else:
                prequeueId = ""
            queueId = input()
            if queueId == "":
                continue
            queueId = int(queueId)
            if queueId < 0:
                break
            elif queueId == 0:
                await check_available_queue(connection)
                print("(" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\t" + platformId + "\t" + game_version + ")")
                print('请输入队列房间序号：（输入“0”以刷新可用队列信息。输入负数以退出创建。）\nPlease enter the queueID: (Enter "0" to refresh available queue information. Enter any negative number to exit creation.)')
                continue
            lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
            if "gameConfig" in lobby_information and not lobby_information["gameConfig"]["isCustom"]:
                response = await (await connection.request("PUT", "/lol-lobby/v1/parties/queue", data = str(queueId))).json()
                if response == None:
                    print(lobby_information)
                elif "errorCode" in response:
                    if response["message"] == "UNHANDLED_SERVER_SIDE_ERROR":
                        print("服务器错误。请换一个队列序号并重试。\nUnhandled server side error. Please switch to another queueId and try again.")
                    elif response["message"] == "INVALID_REQUEST":
                        print("请求无效。\nInvalid request.")
                    else:
                        print(response)
            else:
                queue = {"queueId": queueId}
                response = await (await connection.request("DELETE", "/lol-lobby/v2/lobby")).json()
                response = await (await connection.request("POST", "/lol-lobby/v2/lobby", data = queue)).json()
                lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
                if "gameConfig" in lobby_information:
                    postqueueId = lobby_information["gameConfig"]["queueId"]
                    if prequeueId == postqueueId:
                        continue
                    else:
                        print(lobby_information)
                else:
                    print("此房间序号尚不可用。请选择其它序号。\nThis queueId isn't available yet. Please select another ID.")
        except ValueError:
            print("队列房间序号输入错误！请重新输入：\nError input of queueID! Please try again:")
        except KeyError:
            pass

#-----------------------------------------------------------------------------
# 批量添加机器人（Add a batch of bots）
#-----------------------------------------------------------------------------
async def add_bots_team(connection, teamId: str):
    lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
    maxTeamSize = lobby_information["gameConfig"]["maxTeamSize"]
    current_summonerId = (await (await connection.request("GET", "/lol-summoner/v1/current-summoner")).json())["summonerId"]
    LoLChampions = await (await connection.request("GET", f"/lol-champions/v1/inventories/{current_summonerId}/champions")).json()
    LoLChampions = {champion["id"]: champion for champion in LoLChampions}
    #英雄的推荐路线（Recommended positions for champions）
    recommended_position_for_champion = await (await connection.request("GET", "/lol-perks/v1/recommended-champion-positions")).json()
    recommended_position_for_champion_keys = list(recommended_position_for_champion.keys())
    for championId in recommended_position_for_champion_keys:
        if not int(championId) in all_bots:
            del recommended_position_for_champion[championId]
    #可用的路线（Available lanes）
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
    #botPositions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    #各路线上的英雄（Champions on each lane）
    recommended_champion_for_position = {} #用于生成某条分路的随机英雄（Used to generate random champions of specific positions respectively）
    for position in botPositions:
        recommended_champion_for_position[position] = []
    for championId in recommended_position_for_champion:
        for position in recommended_position_for_champion[championId]["recommendedPositions"]:
            recommended_champion_for_position[position].append(int(championId))
    for position in recommended_champion_for_position:
        recommended_champion_for_position[position].sort()
    #角色定位（Champion roles）
    roles = set()
    for champion in LoLChampions.values():
        roles |= set(champion["roles"])
    #将roles排序整理为["assassin", "fighter", "mage", "marksman", "support", "tank"]
    roles = list(roles)
    roles_tmp = []
    for role in ["assassin", "fighter", "mage", "marksman", "support", "tank"]:
        if role in roles:
            roles.remove(role)
            roles_tmp.append(role)
    roles = roles_tmp + roles
    #roles = ["assassin", "fighter", "mage", "marksman", "support", "tank"]
    #各角色定位的英雄（Champions of each role）
    recommended_champion_for_role = {} #用于生成某个角色定位的随机英雄（Used to generate random champions of specific roles respectively）
    for role in roles:
        recommended_champion_for_role[role] = []
    for championId in LoLChampions:
        for role in LoLChampions[championId]["roles"]:
            recommended_champion_for_role[role].append(championId)
    #可用的电脑玩家难度（Available bot difficulty）
    botDifficulty = ["EASY", "HARD", "MEDIUM", "RSINTRO", "RSBEGINNER", "RSINTERMEDIATE", "RSWARMINTRO"]
    print("队伍%s：请选择自选电脑玩家或者随机生成电脑玩家：\nTeam %s: Please select the option to generate bot players:\n0\t跳过该队伍（Skip this team）\n1\t完全随机生成（Completely Randomly）\n2\t按照分路随机生成（Randomly according to Positions）\n3\t自选（By Picking）" %(teamId[0], teamId[0]))
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
            print(f'请输入分路，以空格为分隔符。（默认使用全分路。）\nPlease enter the bot positions split by space (among {botPositions}, which is taken by default.)')
            while True:
                botPositions_add = input().split()
                if botPositions_add == []:
                    botPositions_add = botPositions[:]
                if all(map(lambda x: x in botPositions, botPositions_add)):
                    botPositions_add = botPositions_add[:maxTeamSize]
                    break
                else:
                    print(f"电脑玩家路线错误！请选择{botPositions}中的一个：\nError input of botDifficulty! Please choose among {botPositions}:")
            while True:
                back = False
                print("您想要对战什么样的阵容？\nWhat comp do you want to fight against?\n1\t清一色阵容（Full comp）\n2\t自定义阵容（Customized comp）\n3\t任意阵容（Arbitrary comp）")
                comp_specified = False
                comp_option = input()
                if comp_option != "" and comp_option[0] == "1":
                    print("请选择角色定位类型：\nPlease select a role type:\n1\t纯刺客（All assassin）\n2\t纯战士（All fighters）\n3\t纯法师（All mages）\n4\t纯射手（All marksmen）\n5\t纯辅助（All supports）\n6\t纯坦克（All tanks）")
                    while True:
                        fullcomp_role_option = input()
                        if fullcomp_role_option in list(map(str, range(1, len(roles) + 1))):
                            comp_specified = True
                            comp_role = roles[int(fullcomp_role_option) - 1]
                            print("您选择了纯%s阵容。\nYou chose all-%s comp." %(roles_CN[comp_role], comp_role))
                            break
                        elif fullcomp_role_option == "0":
                            back = True
                            break
                        else:
                            print("您的输入有误！请重新输入。\nERROR input! Please try again.")
                    if back:
                        continue
                    comp_roles = [comp_role] * len(botPositions_add)
                    role_specific_championIds = [recommended_champion_for_role[comp_role]] * len(botPositions_add)
                elif comp_option != "" and comp_option[0] == "2":
                    print("请依次为上路、打野、中路、下路和辅助位置指定英雄角色定位，以空格为分隔符。\nPlease specify the roles for TOP, JUNGLE, MIDDLE, BOTTOM and UTILITY champions, respectively, split by space.\n1\t刺客（Assassin）\n2\t战士（Fighter）\n3\t法师（Mage）\n4\t射手（Marksman）\n5\t辅助（Support）\n6\t坦克（Tank）\n示例输入（Example）：\n2 2 3 4 6\n4 6 1 3 5")
                    while True:
                        try:
                            comp_role_numbers = list(map(int, input().split()))
                        except ValueError:
                            print("您的输入有误！请输入整数。\nERROR input! Please enter integers.")
                        else:
                            if comp_role_numbers == [0]:
                                back = True
                                break
                            elif len(comp_role_numbers) != len(botPositions_add):
                                print("数量不符！请输入%d个位置的英雄角色定位。\nLength mismatch! Please enter %d champion roles." %(len(botPositions_add), len(botPositions_add)))
                            elif any(map(lambda x: x < 1 or x > 6, comp_role_numbers)):
                                print("您的输入有误！请输入1～6之间的正整数。\nERROR input! Please enter positive integers between 1 and 6.")
                            else:
                                comp_specified = True
                                comp_roles = list(map(lambda x: roles[x - 1], comp_role_numbers))
                                comp_role_str_zh = "、".join(list(map(lambda x: roles_CN[roles[x - 1]], comp_role_numbers)))
                                comp_role_str_en = ", ".join(list(map(lambda x: roles[x - 1], comp_role_numbers)))
                                print(f"您为上路、打野、中路、下路和辅助位置分别指定了{comp_role_str_zh}英雄。\nYou specified {comp_role_str_en} champions for TOP, JUNGLE, MIDDLE, BOTTOM and UTILITY champions, respectively.")
                                break
                    if back:
                        continue
                    role_specific_championIds = [recommended_champion_for_role[roles[i - 1]] for i in comp_role_numbers]
                else:
                    comp_roles = ["arbitrary"] * len(botPositions_add)
                    role_specific_championIds = [all_bots] * len(botPositions_add)
                break
            sample_notfound_hints_printed = [False] * len(botPositions_add) #有些分路可能没有特定的角色。这样的提示只需要输出一遍（Some lanes might be lack of certain roles. Such hints only need to be printed once）
            while True:
                team = []
                for i in range(len(botPositions_add)):
                    position = botPositions_add[i]
                    role = comp_roles[i]
                    candidate_champions = sorted(set(recommended_champion_for_position[position]) & set(role_specific_championIds[i]))
                    if len(candidate_champions) == 0:
                        if not sample_notfound_hints_printed[i]:
                            print("%s位置无%s英雄。将不再限定角色定位。\nNo %s champions found for %s. The program will use another arbitrary role." %(botPositions_CN[position], roles_CN[role], role, position))
                            sample_notfound_hints_printed[i] = True
                        candidate_champions = recommended_champion_for_position[position]
                        comp_roles[i] = "arbitrary"
                    team += random.sample(candidate_champions, 1)
                print("程序为您分配到以下英雄：\nYou have been distributed the following bot champions:\n*****************************************************************************")
                for i in range(len(team)):
                    print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botPositions_add[i] + "\t" + comp_roles[i])
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
                                    print("%s的推荐路线是%s。请选择一位适合%s的英雄，或者在选择%s位英雄时输入该英雄的序号。\nThe recommended positions for %s include %s. Please select a champion whose recommended positions include %s, or input this championId when selecting champions of the following lane(s): %s." %(names[championId], recommended_position_str_zh, botPositions_CN[position], recommended_position_str_zh, aliases[championId], recommended_position_str_en, position, recommended_position_str_en))
                                elif championId in LoLChampions:
                                    print("没有名为%s的电脑玩家。请对照可用电脑玩家工作簿的第一张工作表选择一个%s英雄。\nThere's not a bot named %s. Please refer to Sheet1 of the available-bots workbook and select a %s champion." %(LoLChampions[championId]["name"], botPositions_CN[position], LoLChampions[championId]["alias"], position))
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

    botUuid_team = []
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
            botPosition_team = botPositions_add[:]
            for i in range(len(team)):
                Id = team[i]
                botUuid = str(uuid.uuid4())
                botUuid_team.append(botUuid)
                bot = {"championId": Id, "botDifficulty": botDifficulty_team, "teamId": teamId, "position": botPositions_add[i], "botUuid": botUuid}
                response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
        else:
            print(f"请依次输入电脑玩家路线：\nPlease enter the botPositions: (among {botPositions})")
            botPosition_team = []
            for i in range(len(team)):
                Id = team[i]
                botUuid = str(uuid.uuid4())
                botUuid_team.append(botUuid)
                while True:
                    botPosition_tmp = input()
                    if botPosition_tmp == "":
                        continue
                    elif botPosition_tmp in botPositions:
                        botPosition_team.append(botPosition_tmp)
                        bot = {"championId": Id, "botDifficulty": botDifficulty_team, "teamId": teamId, "position": botPosition_tmp, "botUuid": botUuid}
                        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                        break
                    else:
                        print(f"电脑玩家路线错误！请选择{botPositions}中的一个：\nError input of botDifficulty! Please choose among {botPositions}:")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team)):
            print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botDifficulty_team + "\t" + botPosition_team[i] + "\t" + botUuid_team[i])
        print("*****************************************************************************\n")
    else:
        if o[0] == "2":
            print(f"请依次输入电脑玩家的难度：\nPlease enter the botDifficulty: (among {botDifficulty})")
            botDifficulty_team = []
            botPosition_team = botPositions_add[:]
            for i in range(len(team)):
                Id = team[i]
                botUuid = str(uuid.uuid4())
                botUuid_team.append(botUuid)
                botPosition_tmp = botPositions_add[i]
                while True:
                    botDifficulty_tmp = input()
                    if botDifficulty_tmp == "":
                        continue
                    elif botDifficulty_tmp in botDifficulty:
                        botDifficulty_team.append(botDifficulty_tmp)
                        bot = {"championId": Id, "botDifficulty": botDifficulty_tmp, "teamId": teamId, "position": botPosition_tmp, "botUuid": botUuid}
                        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                        break
                    else:
                        print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
        else:
            print(f"请依次输入电脑玩家的难度和路线，以空格为分隔符：\nPlease enter the botDifficulty (among {botDifficulty}) and role (among {botPositions}), split by space:")
            botDifficulty_team = []
            botPosition_team = []
            for i in range(len(team)):
                Id = team[i]
                botUuid = str(uuid.uuid4())
                botUuid_team.append(botUuid)
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
                                botDifficulty_team.append(botDifficulty_tmp)
                                botPosition_team.append(botPosition_tmp)
                                bot = {"championId": Id, "botDifficulty": botDifficulty_tmp, "teamId": teamId, "position": botPosition_tmp, "botUuid": botUuid}
                                response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
                                break
                            elif not botDifficulty_tmp in botDifficulty and botPosition_tmp in botPositions:
                                print(f"电脑玩家难度输入错误！请选择{botDifficulty}中的一个：\nError input of botDifficulty! Please choose among {botDifficulty}:")
                            elif botDifficulty_tmp in botDifficulty and not botPosition_tmp in botPositions:
                                print(f"电脑玩家路线输入错误！请选择{botPositions}中的一个：\nError input of botPositions! Please choose among {botPositions}:")
                            else:
                                print(f"电脑玩家难度和路线输入错误！\nError input of botDifficulty!\n请选择{botDifficulty}中的一个作为电脑玩家难度。\nPlease choose among {botDifficulty} as botDifficulty.\n请选择{botPositions}中的一个作为电脑玩家路线。\nPlease choose among {botDifficulty} as botPositions.")
        print("您的最终选择如下：\nYour final choices are as follows:\n*****************************************************************************")
        for i in range(len(team)):
            print("{0:<14}".format(names[team[i]]) + "\t" + "{0:<14}".format(aliases[team[i]]) + "\t" + botDifficulty_team[i] + "\t" + botPosition_team[i] + "\t" + botUuid_team[i])
        print("*****************************************************************************\n")

#-----------------------------------------------------------------------------
# 获取房间信息（Get lobby information）
#-----------------------------------------------------------------------------
async def get_lobby_information(connection):
    lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
    print(lobby_information)
    print("创建完成！输入任意键开始游戏，否则继续获取房间信息。\nLobby created successfully! Please press any key to start the game, or null to continue getting lobby information:")
    while input() == "":
        lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
        print(lobby_information)

#-----------------------------------------------------------------------------
# 开始游戏（Start Game）
#-----------------------------------------------------------------------------
async def start_game(connection):
    while True:
        lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
        if lobby_information["gameConfig"]["isCustom"]:
            start_game = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/start-champ-select")).json()
            #print("start_game = ", end = "")
            #print(start_game)
            if "success" in start_game and start_game["success"] == True:
                gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json() #gameflow_phase参数（parameters）：None、Lobby、Matchmaking、ReadyCheck、ChampSelect、InProgress、Reconnect、WaitingForStats、EndOfGame
                while gameflow_phase != "ChampSelect":
                    gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
                    #print("gameflow-phase = ", end = "")
                    #print(gameflow_phase)
                gamemode_info = await (await connection.request("GET", "/lol-gameflow/v1/session")).json()
                print(gamemode_info)
                while gameflow_phase == "ChampSelect":
                    gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
                #print("gameflow-phase = ", end = "")
                #print(gameflow_phase)
                if gameflow_phase == "Lobby":
                    print("请确认各召唤师就绪后，按回车开始匹配。\nPlease start queue by pressing Enter after confirming all ready.")
                    input()
                elif gameflow_phase == "None":
                    print("您已退出房间，请重启程序！\nYou have exited the lobby! Please restart the program!")
                    time.sleep(5)
                    break
                elif gameflow_phase == "InProgress":
                    break
            else:
                print(start_game)
                print("请检查房间有效性。输入任意键开始游戏。\nPlease check the lobby validation. Press any key to start the game.")
                input()
        else:
            members_prepared = False
            count = 0 # count用来控制输出，如果是第一次载入队列房间，需要确定各召唤师首选参数为空还是未选择。因为刚加入房间所有召唤师一定是未选择的，所以只需要请求各召唤师选择位置，不需要输出所有召唤师未首选的信息（count is used to control the output. If it first loads the queue lobby, whether firstPositionPreference is null or "UNSELECTED" should be ensured. Since all summoners join the lobby with unselected preferences, it's unnecessary to print the information about all the summoners with firstPositionPreference = "UNSELECTED"）
            while not members_prepared:
                count += 1
                first_unselected = []
                second_unselected = []
                for i in lobby_information["members"]:
                    if i["firstPositionPreference"] == "UNSELECTED":
                        first_unselected.append((i["summonerName"], i["summonerId"]))
                    elif i["firstPositionPreference"]!= "FILL" and i["secondPositionPreference"] == "UNSELECTED":
                        second_unselected.append((i["summonerName"], i["summonerId"]))
                if first_unselected == [] and second_unselected == []:
                    members_prepared = True
                else:
                    if count > 1:
                        print("以下召唤师未准备就绪：\nThe following summoners aren't ready yet:\n召唤师名称（SummonerName）\t召唤师序号（SummonerId）\t未选优先级（Unselected Preference）")
                        for i in first_unselected:
                            print(i[0] + "\t" + str(i[1]) + "\t" + "首选（First）")
                        for i in second_unselected:
                            print(i[0] + "\t" + str(i[1]) + "\t" + "次选（Second）")
                    print("请确认各召唤师就绪后，按回车开始匹配。\nPlease start queue by pressing Enter after confirming all ready.")
                    input()
                    lobby_information = await (await connection.request("GET", "/lol-lobby/v2/lobby")).json()
            start_game = await (await connection.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")).json() # 对于一些点击“寻找对局”没有反应的房间，会给出以下信息：{'errorCode': 'RPC_ERROR', 'httpStatus': 400, 'implementationDetails': {}, 'message': 'NOT_A_MATCHMADE_QUEUE'}
            search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
            print("start_game = ", end = "")
            print(start_game)
            count1 = 0
            while start_game != None:
                #print(type(start_game))
                count1 += 1 # count1为尝试次数，如果search_state没有及时得到更新，意味着房间内的“寻找对局”按钮不可用（count1 means times of trying. If search_state doesn't get updated in time, it means the "Find Queue" button isn't available）
                search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json() #已知问题：队列房间序号为700时，程序在该处陷入死循环，因为“寻找对局”按钮不可用，无法更新search_state（Known problem: When queueId is 700, program is stuck in an infinite loop here, because the "Find Queue" button isn't available, which prevents search_state from updating）
                #print(search_state, end = "\n")
                if count1 > 500 and search_state["errors"] == []:
                    print("该队列房间不可用！程序即将退出！\nThis queue lobby isn't available! The program will exit soon!")
                    time.sleep(5)
                    os._exit(0)
                while search_state["errors"] != [] and search_state["errors"][0]["errorType"] == "QUEUE_DODGER":
                    print("search-state = ", end = "")
                    print(search_state, end = "\n")
                    penalty_time_remaining = int(search_state["errors"][0]["penaltyTimeRemaining"])
                    penalty_time_remaining_text_zh = ""
                    penalty_time_remaining_text_en = ""
                    penalty_hour = penalty_time_remaining // 3600
                    penalty_minute = penalty_time_remaining % 3600 // 60
                    penalty_second = penalty_time_remaining % 60
                    if penalty_hour != 0:
                        penalty_time_remaining_text_zh += str(penalty_hour) + "时"
                        penalty_time_remaining_text_en += str(penalty_hour) + " h "
                    if penalty_minute != 0:
                        penalty_time_remaining_text_zh += str(penalty_minute) + "分"
                        penalty_time_remaining_text_en += str(penalty_minute) + " m "
                    penalty_time_remaining_text_zh += str(penalty_second) + "秒"
                    penalty_time_remaining_text_en += str(penalty_second) + " s"
                    print("队列秒退计时器：由于你在英雄选择过程中退出了游戏，或者拒绝了过多场游戏，导致你无法加入队列。剩余时间：" + penalty_time_remaining_text_zh + "。\nQUEUE DODGE TIMER: Because you abandoned a recent game during champ selection or declined too many games, you're currently unable to join the queue. Penalty Time Remaining: " + penalty_time_remaining_text_en + ".")
                    input()
                    start_game = await (await connection.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")).json()
                    search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
            print("队列中……\nIn Queue ...")
            gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
            search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
            while search_state["lowPriorityData"]["reason"] == "LEAVER_BUSTED":
                print("search-state = ", end = "")
                print(search_state, end = "\n")
                penalty_time_remaining = int(search_state["lowPriorityData"]["penaltyTimeRemaining"])
                penalty_time_remaining_text_zh = ""
                penalty_time_remaining_text_en = ""
                penalty_hour = penalty_time_remaining // 3600
                penalty_minute = penalty_time_remaining % 3600 // 60
                penalty_second = penalty_time_remaining % 60
                if penalty_hour != 0:
                    penalty_time_remaining_text_zh += str(penalty_hour) + "时"
                    penalty_time_remaining_text_en += str(penalty_hour) + " h "
                if penalty_minute != 0:
                    penalty_time_remaining_text_zh += str(penalty_minute) + "分"
                    penalty_time_remaining_text_en += str(penalty_minute) + " m "
                penalty_time_remaining_text_zh += str(penalty_second) + "秒"
                penalty_time_remaining_text_en += str(penalty_second) + " s"
                print("低优先级队列：放弃比赛或是挂机，会导致你的队友进行一场不公平的对局，并且会被系统视为应受惩罚的恶劣行为。你的队伍已被放置在一条低优先级队列中。离开该队列、拒绝或未能接受对局将重置这个倒计时。剩余时间：" + penalty_time_remaining_text_zh + ".\nLow Priority Queue: Abandoning a match or being AFK results in a negarive experience for your teammates, and is a punishable offense in League of Legends. You've been placed in a lower priority queue. Leaving the queue, declining or failing to accept a match will reset the timer. Time Remaining: " + penalty_time_remaining_text_en + ".")
                input()
                search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
            while gameflow_phase == "Lobby":
                gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
            print("gameflow-phase = ", end = "")
            print(gameflow_phase)
            while search_state["searchState"] != "Found":
                search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
                gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
                #print("gameflow-phase = " & gameflow_phase)
                if gameflow_phase == "Lobby": #这里可以考虑使用gameflow_phase进行替换。下同（It's alternative to substitute gameflow_phase for search_state here. So are the following code）
                    break
            print("search-state = ", end = "")
            print(search_state)
            print("gameflow-phase = ", end = "")
            print(gameflow_phase)   
            if gameflow_phase == "Lobby":
                print("请确认各召唤师就绪后，按回车开始匹配。\nPlease start queue by pressing Enter after confirming all ready.")
                input()
                continue
            print("对局已找到！是否接受对局？（输入任意键拒绝，否则接受）\nMatch found! Accept the match? (Press any key to decline, or null for acceptance)")
            ready_check = input()
            if ready_check == "":
                await connection.request("POST", "/lol-matchmaking/v1/ready-check/accept")
            else:
                await connection.request("POST", "/lol-matchmaking/v1/ready-check/decline")
                while search_state["searchState"] == "Found":
                    search_state = await (await connection.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")).json()
            gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
            count = 0 #这里count确保选英雄时游戏模式的信息只输出一次（Here the variable "count" makes sure that the game mode information will be output only once）
            while gameflow_phase == "ReadyCheck" or gameflow_phase == "ChampSelect":
                gameflow_phase = await (await connection.request("GET", "/lol-gameflow/v1/gameflow-phase")).json()
                if gameflow_phase == "ChampSelect" and count == 0:
                    gamemode_info = await (await connection.request("GET", "/lol-gameflow/v1/session")).json()
                    print(gamemode_info)
                    count += 1
                #print("gameflow-phase = ", end = "")
                #print(gameflow_phase)
            if gameflow_phase == "Lobby":
                print("请确认各召唤师就绪后，按回车开始匹配。\nPlease start queue by pressing Enter after confirming all ready.")
                input()
            elif gameflow_phase == "Matchmaking":
                pass
            elif gameflow_phase == "InProgress":
                break

#-----------------------------------------------------------------------------
# websocket
#-----------------------------------------------------------------------------
@connector.ready
async def connect(connection):
    await get_summoner_data(connection)
##    print("是否查看可用队列房间序号？（输入任意键查看，否则不查看）\nCheck the available QueueID list? (Any keys for Y, or null for N)")
##    check_queueid = input()
##    if check_queueid != "":
##        await check_available_queue(connection)
    print("请选择创建队列房间还是自定义房间：（输入任意键创建队列房间，否则创建自定义房间）\nCreate a queue lobby or a custom lobby? (Any keys for a queue lobby, or null for a custom lobby)")
    lobby_selection = input()
    if lobby_selection == "":
        await create_custom_lobby(connection)
        lobby = await connection.request("GET", "/lol-lobby/v2/lobby")
        lobby_information = await lobby.json()
        if "errorCode" in lobby_information and lobby_information["message"] == "LOBBY_NOT_FOUND":
            print("房间创建失败！请检查房间参数。\nError creating the lobby! Please check the lobby parameters.")
            print(lobby_information)
        else:
            await add_bots_team(connection, teamId = "100")
            await add_bots_team(connection, teamId = "200")
        time.sleep(0.1)
        await get_lobby_information(connection)
    else:
        await create_queue_lobby(connection)
    await start_game(connection)

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------
connector.start()
