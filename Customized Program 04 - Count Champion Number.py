from lcu_driver import Connector
import json, pandas, re, requests, time, uuid

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

def patch_compare(patch1, patch2): #比较两个版本号的先后顺序。当patch1 < patch2时，返回True，否则返回False。用于比较DataDragon数据库中未收录的版本和收录的最新版本的关系。如果未收录的版本小于收录的最新版本，那么该版本是美测服的临时版本，后来被合并更新了，如正式服将13.2和13.3合并更新了，因此DataDragon数据库中未收录13.2版本的数据；如果未收录的版本大于收录的最新版本，那么该版本是美测服的当前版本，但是仍处于开发状态，尚未完全确定，所以DataDragon数据库尚未收录，将以最新版本代替该版本；二者不可能相等，因为如果相等的话，就不会引发报错而调用此函数（Compare the time order of two patches. When patch1 < patch2, return True and vice versa. Designed to compare a patch not archived in DataDragon database with the latest patch archived in DataDragon database. If the unarchived patch is less than the latest archived patch, then this patch must be the intermediate patch and be merged into the update of its successive patch, such as Patch 13.2 merged into the update of Patch 13.3, so that DataDragon database doesn't archive the data of Patch 13.2; If the unarchived patch is greater than the latest archived patch, then this patch must be the current patch on PBE but is under development and improvement, so that DataDragon database doesn't archive this patch, either, in which case the latest patch will be used to substitute this unarchived patch; The two patches can't be the same, for suppose they're same, then the error to cause the call of this function won't be triggered）
    if not isinstance(patch1, str):
        patch1 = str(patch1)
    if not isinstance(patch2, str):
        patch2 = str(patch2)
    lst1, lst2 = patch1.split("."), patch2.split(".")
    try:
        lst1 = list(map(int, lst1))
    except ValueError:
        if lst1[0] != "pbe":
            print("第1个版本字符串不合法！请输入用半角句号连接的正整数，如13.15.1、10.10.3216176。\nThe first patch variable is illegal! Please pass the integers concatenated by dot, such as 13.15.1 and 10.10.3216176.")
        return False
    try:
        lst2 = list(map(int, lst2))
    except ValueError:
        if lst1[0] != "pbe":
            print("第2个版本字符串不合法！请输入用半角句号连接的正整数，如13.15.1、10.10.3216176。\nThe second patch variable is illegal! Please pass the integers concatenated by dot, such as 13.15.1 and 10.10.3216176.")
            return False
        else:
            return True
    for i in range(min(len(lst1), len(lst2))):
        if lst1[i] < lst2[i]:
            return True
        elif lst1[i] > lst2[i]:
            return False
        else:
            continue
    if len(lst1) < len(lst2):
        return True
    else:
        return False #这里将两个版本相同视为假，暗示了在本程序用得到的地方，两个版本不可能相同（Here the case where the two patches are the same is regarded as False, which indicates that the two patches can't be same within its use in this program）

def patch_sort(patchList: list): #利用插入排序算法，根据patch_compare函数对版本列表进行升序排列（Sorts a patch list according to the principle of `patch_compare` function through the insertion sort algorithm）
    bigPatch_re = re.compile("[0-9]*.[0-9]*")
    if all(map(lambda x: isinstance(x, str), patchList)) and all(map(lambda x: bigPatch_re.search(x), patchList)): #此处放宽了参数的格式限制：只要列表的每个元素都是包含版本字符串的字符串即可（Here the function relaxes the limit for the format of the parameter: any list whose elements are all strings that contain a patch string is OK）
        patchList = list(map(lambda x: bigPatch_re.search(x).group(), patchList))
        for i in range(1, len(patchList)):
            tmp = patchList[i] #将第i个元素临时存储（Temporarily stores the i-th element of `patchList`）
            j = i - 1
            while j >= 0 and patch_compare(tmp, patchList[j]): #如果检测到第i个元素比第(j = i - 1)个元素小，就要逐渐减小j，直到找到一个j，使得第j个元素小于第i个元素，此时第j + 1个元素仍然大于第i个铁元素。把j + 1及以后的元素右移，空出的位置再插入第i个元素（1f an i-th element is detected to be less than the j-th element, namely the (i - 1)th element, then the program decrements j until it finds a j such that the j-th element is less than the i-th element, while the (j + 1)-th element is still greater than the i-the element. Then, shift all elements between the current j-th and i-th elements and insert the i-th elements into the empty space）
                patchList[j + 1] = patchList[j]
                j -= 1
            patchList[j + 1] = tmp
    else:
        print("您的版本列表格式有误！\nYour patch list is not correctly formatted!")
    return patchList

def getUrl(url: str):
    retry = 0
    while True:
        try:
            retry += 1
            source = requests.get(url)
            source.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            if retry > 5:
                break
            if http_err.response.status_code in {403, 404}:
                return (source, http_err.response.status_code)
        except requests.exceptions.SSLError as ssl_error:
            if retry > 5:
                break
            if "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol" in str(ssl_error):
                print("违反协议导致读取中断！正在尝试第%d次重新获取数据！\nEOF occurred in violation of protocol! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            elif 'certificate verify failed' in str(ssl_error):
                print("SSL证书验证失败！正在尝试第%d次重新获取数据！\nSSL certificate verify failed! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            elif 'Max retries exceeded with url' in str(ssl_error):
                print("请求数量超过限制！正在尝试第%d次重新获取数据！\nMax retries exceed with url! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
        except requests.exceptions.ProxyError:
            if retry > 5:
                break
            print("无法连接到代理！正在尝试第%d次重新获取数据！\nCannot connect to proxy! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
        except requests.exceptions.ChunkedEncodingError:
            if retry > 5:
                break
            print("接收数据块长度不正确导致连接中断！正在尝试第%d次重新获取数据！\nConnection broken: InvalidChunkLength. Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
        except requests.exceptions.ConnectionError:
            if retry > 5:
                break
            print("由于远程服务器端无响应，连接已关闭！正在尝试第%d次重新获取数据！\nRemote end closed connection without response. Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
        except requests.exceptions.ReadTimeout:
            if retry > 5:
                break
            print("读取超时！正在尝试第%d次重新获取数据！\nRead time out! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
        else:
            return (source, 0)
    if retry > 5:
        return (None, 1)

language_ddragon = {1: {"CODE": "ar_AE", "LANGUAGE (EN)": "Arabic (United Arab Emirates)", "LANGUAGE (ZH)": "阿拉伯语（阿拉伯联合酋长国）", "Applicable CDragon Data Patches": "9.20～10.1, 13.20+"}, 2: {"CODE": "cs_CZ", "LANGUAGE (EN)": "Czech (Czech Republic)", "LANGUAGE (ZH)": "捷克语（捷克共和国）", "Applicable CDragon Data Patches": "7.1+"}, 3: {"CODE": "el_GR", "LANGUAGE (EN)": "Greek (Greece)", "LANGUAGE (ZH)": "希腊语（希腊）", "Applicable CDragon Data Patches": "9.1+"}, 4: {"CODE": "pl_PL", "LANGUAGE (EN)": "Polish (Poland)", "LANGUAGE (ZH)": "波兰语（波兰）", "Applicable CDragon Data Patches": "9.1+"}, 5: {"CODE": "ro_RO", "LANGUAGE (EN)": "Romanian (Romania)", "LANGUAGE (ZH)": "罗马尼亚语（罗马尼亚）", "Applicable CDragon Data Patches": "9.1+"}, 6: {"CODE": "hu_HU", "LANGUAGE (EN)": "Hungarian (Hungary)", "LANGUAGE (ZH)": "匈牙利语（匈牙利）", "Applicable CDragon Data Patches": "9.1+"}, 7: {"CODE": "en_GB", "LANGUAGE (EN)": "English (United Kingdom)", "LANGUAGE (ZH)": "英语（英国）", "Applicable CDragon Data Patches": "9.1+"}, 8: {"CODE": "de_DE", "LANGUAGE (EN)": "German (Germany)", "LANGUAGE (ZH)": "德语（德国）", "Applicable CDragon Data Patches": "7.1+"}, 9: {"CODE": "es_ES", "LANGUAGE (EN)": "Spanish (Spain)", "LANGUAGE (ZH)": "西班牙语（西班牙）", "Applicable CDragon Data Patches": "9.1+"}, 10: {"CODE": "it_IT", "LANGUAGE (EN)": "Italian (Italy)", "LANGUAGE (ZH)": "意大利语（意大利）", "Applicable CDragon Data Patches": "9.1+"}, 11: {"CODE": "fr_FR", "LANGUAGE (EN)": "French (France)", "LANGUAGE (ZH)": "法语（法国）", "Applicable CDragon Data Patches": "9.1+"}, 12: {"CODE": "ja_JP", "LANGUAGE (EN)": "Japanese (Japan)", "LANGUAGE (ZH)": "日语（日本）", "Applicable CDragon Data Patches": "9.1+"}, 13: {"CODE": "ko_KR", "LANGUAGE (EN)": "Korean (Korea)", "LANGUAGE (ZH)": "朝鲜语（韩国）", "Applicable CDragon Data Patches": "9.7+"}, 14: {"CODE": "es_MX", "LANGUAGE (EN)": "Spanish (Mexico)", "LANGUAGE (ZH)": "西班牙语（墨西哥）", "Applicable CDragon Data Patches": "9.1+"}, 15: {"CODE": "es_AR", "LANGUAGE (EN)": "Spanish (Argentina)", "LANGUAGE (ZH)": "西班牙语（阿根廷）", "Applicable CDragon Data Patches": "9.7+"}, 16: {"CODE": "pt_BR", "LANGUAGE (EN)": "Portuguese (Brazil)", "LANGUAGE (ZH)": "葡萄牙语（巴西）", "Applicable CDragon Data Patches": "9.1+"}, 17: {"CODE": "en_US", "LANGUAGE (EN)": "English (United States)", "LANGUAGE (ZH)": "英语（美国）", "Applicable CDragon Data Patches": "9.1+"}, 18: {"CODE": "en_AU", "LANGUAGE (EN)": "English (Australia)", "LANGUAGE (ZH)": "英语（澳大利亚）", "Applicable CDragon Data Patches": "9.1+"}, 19: {"CODE": "ru_RU", "LANGUAGE (EN)": "Russian (Russia)", "LANGUAGE (ZH)": "俄语（俄罗斯）", "Applicable CDragon Data Patches": "9.1+"}, 20: {"CODE": "tr_TR", "LANGUAGE (EN)": "Turkish (Turkey)", "LANGUAGE (ZH)": "土耳其语（土耳其）", "Applicable CDragon Data Patches": "9.1+"}, 21: {"CODE": "ms_MY", "LANGUAGE (EN)": "Malay (Malaysia)", "LANGUAGE (ZH)": "马来语（马来西亚）", "Applicable CDragon Data Patches": ""}, 22: {"CODE": "en_PH", "LANGUAGE (EN)": "English (Republic of the Philippines)", "LANGUAGE (ZH)": "英语（菲律宾共和国）", "Applicable CDragon Data Patches": "10.5+"}, 23: {"CODE": "en_SG", "LANGUAGE (EN)": "English (Singapore)", "LANGUAGE (ZH)": "英语（新加坡）", "Applicable CDragon Data Patches": "10.5+"}, 24: {"CODE": "th_TH", "LANGUAGE (EN)": "Thai (Thailand)", "LANGUAGE (ZH)": "泰语（泰国）", "Applicable CDragon Data Patches": "9.7+"}, 25: {"CODE": "vn_VN", "LANGUAGE (EN)": "Vietnamese (Viet Nam)", "LANGUAGE (ZH)": "越南语（越南）", "Applicable CDragon Data Patches": "9.7～13.9"}, 26: {"CODE": "vi_VN", "LANGUAGE (EN)": "Vietnamese (Viet Nam)", "LANGUAGE (ZH)": "越南语（越南）", "Applicable CDragon Data Patches": "12.17+"}, 27: {"CODE": "id_ID", "LANGUAGE (EN)": "Indonesian (Indonesia)", "LANGUAGE (ZH)": "印度尼西亚语（印度尼西亚）", "Applicable CDragon Data Patches": ""}, 28: {"CODE": "zh_MY", "LANGUAGE (EN)": "Chinese (Malaysia)", "LANGUAGE (ZH)": "中文（马来西亚）", "Applicable CDragon Data Patches": "10.5+"}, 29: {"CODE": "zh_CN", "LANGUAGE (EN)": "Chinese (China)", "LANGUAGE (ZH)": "中文（中国）", "Applicable CDragon Data Patches": "9.7+"}, 30: {"CODE": "zh_TW", "LANGUAGE (EN)": "Chinese (Taiwan)", "LANGUAGE (ZH)": "中文（台湾）", "Applicable CDragon Data Patches": "9.7+"}}
language_cdragon = {}
for i in language_ddragon:
    if language_ddragon[i]["CODE"] == "en_US":
        language_cdragon[language_ddragon[i]["CODE"]] = "default" #在CommunityDragon数据库上，美服正式服的数据资源代码是default，而不是小写的en_US（The code for English (US) data resources on CommunityDragon database is "default" instead of the lowercase of "en_US"）
    else:
        language_cdragon[language_ddragon[i]["CODE"]] = language_ddragon[i]["CODE"].lower()
print('请选择英雄数据来源（输入“0”以退出程序）：\nPlease select the champion data source (submit "0" to exit):\n1\tLCU API\n2\tDataDragon\n3\tCommunityDragon')
source = input()
if source != "" and (source[0] == "0" or source[0] == "2" or source[0] == "3"):
    if source[0] == "0":
        exit()
    print("请选择输出语言【默认为中文（中国）】：\nPlease select a language for output (the default option is zh_CN):\nNo.\tCODE\tLANGUAGE\t语言\tApplicable CDragon Data Patches")
    for i in range(1, 31):
        print(str(i) + "\t" + language_ddragon[i]["CODE"] + "\t" + language_ddragon[i]["LANGUAGE (EN)"] + "\t" + language_ddragon[i]["LANGUAGE (ZH)"] + "\t" + language_ddragon[i]["Applicable CDragon Data Patches"])
    while True:
        language_option = input()
        if language_option == "" or language_option in [str(i) for i in range(1, 31)]:
            if language_option == "":
                language_option = "29"
            language_code = language_ddragon[int(language_option)]["CODE"]
            #下面声明一些数据资源的地址（The following code declare some data resources' URLs）
            patches_url = "https://ddragon.leagueoflegends.com/api/versions.json"
            #下面声明离线数据资源的默认地址（The following code declare the default paths of offline data resources）
            patches_local_default = "离线数据（Offline Data）\\versions.json"
            cdragon_champion_local_default = "离线数据（Offline Data）\\cdragon\\pbe\\plugins\\rcp-be-lol-game-data\\global\\%s\\v1\\champions\\" %language_cdragon[language_code]
            ddragon_champion_local_default = "离线数据（Offline Data）\\ddragon\\%s\\champion.json" %language_code
            break
        else:
            print("语言选项输入错误！请重新输入：\nERROR input of language option! Please try again:")
    if source[0] == "2":
        src, status = getUrl(patches_url)
        if status != 0:
            if status == 1:
                print('版本信息获取超时！正在尝试离线加载数据……\nPatch information capture timeout! Trying loading offline data ...\n请输入版本Json数据文件路径。输入空字符以使用默认相对引用路径“%s”。输入“0”以退出程序。\nPlease enter the patch Json data file path. Enter an empty string to use the default relative path: "%s". Submit "0" to exit.' %(patches_local_default, patches_local_default))
                while True:
                    patches_local = input()
                    if patches_local == "":
                        patches_local = patches_local_default
                    elif patches_local[0] == "0":
                        print("版本信息获取失败！请检查系统网络状况和代理设置。\nPatch information capture failure! Please check the system network condition and agent configuration.")
                        time.sleep(3)
                        exit()
                    try:
                        with open(patches_local, "r", encoding = "utf-8") as fp:
                            patches = json.load(fp)
                        if isinstance(patches, list) and patches[-1] == "lolpatch_3.7":
                            break
                        else:
                            print("数据格式错误！请选择一个符合DataDragon数据库中记录的版本数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the patch data archived in DataDragon database (%s)!" %(patches_url, patches_url))
                            continue
                    except FileNotFoundError:
                        print("未找到文件%s！请输入正确的版本Json数据文件路径！\nFile %s NOT found! Please input a correct patch Json data file path!" %(patches_local, patches_local))
                        continue
                    except OSError:
                        print("数据文件名不合法！请输入含有版本信息的本地文件的路径！\nIllegal data filename! Please input the path of a local file with patch information.")
                        continue
                    except json.decoder.JSONDecodeError:
                        print("数据格式错误！请选择一个符合DataDragon数据库中记录的版本数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the patch data archived in DataDragon database (%s)!" %(patches_url, patches_url))
                        continue
            elif status == 404:
                print("版本信息文件不存在！请联系作者修复程序。\nPatch information resource file not found! Please contact the author and ask for a repair.")
        else:
            patches = src.json()
            latest_patch = patches[0]
        champion_local_default = ddragon_champion_local_default
        print("请输入您想要获取的版本。输入空字符串以获取最新版本英雄信息。\nPlease input the patch you want to search from. Submit an empty string to get the latest champion data. Examples: \n" + ", ".join(patches[:-98]))
        while True:
            patch_in_url = input()
            if patch_in_url == "":
                patch_in_url = patches[0]
            if patch_in_url in patches[:-98]:
                champion_url = "http://ddragon.leagueoflegends.com/cdn/%s/data/%s/champion.json" %(patch_in_url, language_code)
                break
            else:
                print("版本输入有误！请重新输入。\nERROR input of patch! Please try again!")
        src, status = getUrl(champion_url)
        if status != 0:
            if status == 1:
                print('英雄数据获取超时！正在尝试离线加载数据……\nChampion data capture timeout! Trying loading offline data ...\n请输入英雄Json数据文件路径。输入空字符以使用默认相对引用路径“%s”。输入“0”以退出程序。\nPlease enter the champion Json data file path. Enter an empty string to use the default relative path: "%s". Submit "0" to exit.' %(champion_local_default, champion_local_default))
                while True:
                    champion_local = input()
                    if champion_local == "":
                        champion_local = champion_local_default
                    elif champion_local[0] == "0":
                        print("英雄数据获取失败！请检查系统网络状况和代理设置。\nChampion data capture failure! Please check the system network condition and agent configuration.")
                        time.sleep(3)
                        exit()
                    try:
                        with open(champion_local, "r", encoding = "utf-8") as fp:
                            LoLChampion = json.load(fp)
                        if isinstance(LoLChampion, dict) and all(i in LoLChampion for i in ["type", "format", "version", "data"]) and LoLChampion["type"] == "champion" and all(j in LoLChampion["data"][i] for i in LoLChampion["data"] for j in ["version", "id", "key", "name", "title", "blurb", "info", "image", "tags", "partype", "stats"]):
                            break
                        else:
                            print("数据格式错误！请选择一个符合DataDragon数据库中记录的英雄数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the champion data archived in DataDragon database (%s)!" %(champion_url, champion_url))
                            continue
                    except FileNotFoundError:
                        print("未找到文件%s！请输入正确的英雄Json数据文件路径！\nFile %s NOT found! Please input a correct champion Json data file path!" %(champion_local, champion_local))
                        continue
                    except OSError:
                        print("数据文件名不合法！请输入含有英雄信息的本地文件的路径！\nIllegal data filename! Please input the path of a local file with champion information.")
                        continue
                    except json.decoder.JSONDecodeError:
                        print("数据格式错误！请选择一个符合DataDragon数据库中记录的英雄数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the champion data archived in DataDragon database (%s)!" %(champion_url, champion_url))
                        continue
        else:
            LoLChampion = src.json()
        #下面按照程序需求对数据资源进行一定的整理（The following code sort out the data resource according to the program's need）
        LoLChampions = {}
        for champion in LoLChampion["data"].values():
            LoLChampions[int(champion["key"])] = champion
        LoLChampions_header = {"version": "版本", "id": "英雄代码", "key": "英雄序号", "name": "称号", "title": "名称", "blurb": "背景介绍", "partype": "施法资源属性", "info: attack": "伤害属性得分", "info: defense": "强韧属性得分", "info: magic": "法术属性得分", "info: difficulty": "使用难度系数", "tag: Assassin": "角色定位：刺客", "tag: Fighter": "角色定位：战士", "tag: Mage": "角色定位：法师", "tag: Marksman": "角色定位：射手", "tag: Support": "角色定位：辅助", "tag: Tank": "角色定位：坦克", "hp": "基础生命值", "hpperlevel": "生命值成长", "mp": "基础法力/能量值", "mpperlevel": "法力/能量值成长", "movespeed": "移动速度", "armor": "护甲", "armorperlevel": "护甲成长", "spellblock": "魔法抗性", "spellblockperlevel": "魔法抗性成长", "attackrange": "攻击距离", "hpregen": "生命回复", "hpregenperlevel": "生命回复成长", "mpregen": "施法资源回复", "mpregenperlevel": "法力/能量回复成长", "crit": "暴击率", "critperlevel": "暴击率成长", "attackdamage": "攻击力", "attackdamageperlevel": "攻击力成长", "attackspeedperlevel": "攻击速度成长", "attackspeed": "攻击速度", "lvl18hp": "18级生命值", "lvl30hp": "30级生命值", "lvl18mp": "18级法力/能量值", "lvl30mp": "30级法力/能量值", "lvl18attackdamage": "18级攻击力", "lvl30attackdamage": "30级攻击力", "lvl18armor": "18级护甲", "lvl30armor": "30级护甲", "lvl18spellblock": "18级魔法抗性", "lvl30spellblock": "30级魔法抗性", "lvl18attackspeed": "18级攻击速度", "lvl30attackspeed": "30级攻击速度", "lvl18hpregen": "18级生命回复", "lvl30hpregen": "30级生命回复", "lvl18mpregen": "18级施法资源回复", "lvl30mpregen": "30级施法资源回复"}
        LoLChampions_header_keys = list(LoLChampions_header.keys())
        LoLChampions_data = {}
        for i in range(len(LoLChampions_header_keys)):
            key = LoLChampions_header_keys[i]
            LoLChampions_data[key] = []
        print("championId\tname\ttitle\talias")
        count = 0
        for i in sorted(LoLChampions.keys()):
            champion = LoLChampions[i]
            print("%s\t%s\t%s\t%s" %(champion["key"], champion["name"], champion["title"], champion["id"]))
            if champion["id"] != -1: #API中存在一个id为-1的英雄。该英雄不计入英雄个数（There's a champion with the id -1 in API. It won't be counted)
                count += 1
            for j in range(len(LoLChampions_header_keys)):
                key = LoLChampions_header_keys[j]
                if j <= 6:
                    if j == 2: #DataDragon数据库中存储的英雄序号为字符串（ChampionIds stored in DataDragon database are of string type）
                        LoLChampions_data[key].append(int(champion[key]))
                    else:
                        LoLChampions_data[key].append(champion[key])
                elif j <= 10:
                    LoLChampions_data[key].append(champion["info"][key[6:]])
                elif j <= 16:
                    if key[5:] in champion["tags"]:
                        LoLChampions_data[key].append("√")
                    else:
                        LoLChampions_data[key].append("")
                elif j <= 36:
                    LoLChampions_data[key].append(champion["stats"][key])
                else:
                    level, subkey = int(key[3:5]), key[5:]
                    result = champion["stats"][subkey] + (level - 1) * champion["stats"][subkey + "perlevel"] * (0.01 if subkey == "attackspeed" else 1) #攻击速度成长是百分比（`attackspeedperlevel` is a percentage）
        LoLChampions_statistics_output_order = [2, 3, 4, 1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 33, 34, 22, 23, 24, 25, 36, 35, 31, 32, 21, 27, 28, 29, 30, 26]
        #LoLChampions_statistics_output_order = [2, 3, 4, 1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 37, 38, 19, 20, 39, 40, 33, 34, 41, 42, 22, 23, 43, 44, 24, 25, 45, 46, 36, 35, 47, 48, 31, 32, 21, 27, 28, 49, 50, 29, 30, 51, 52, 26] #带成长数值（With leveling up stats）
        LoLChampions_data_organized = {}
        for i in LoLChampions_statistics_output_order:
            key = LoLChampions_header_keys[i]
            LoLChampions_data_organized[key] = LoLChampions_data[key]
        LoLChampions_df = pandas.DataFrame(data = LoLChampions_data_organized)
        LoLChampions_df = pandas.concat([pandas.DataFrame([LoLChampions_header])[LoLChampions_df.columns], LoLChampions_df], ignore_index = True)
        while True:
            try:
                with pandas.ExcelWriter(path = "available-bots.xlsx", mode = "a", if_sheet_exists = "replace") as writer:
                    LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet3")
            except PermissionError:
                print("无写入权限！请确保文件未被打开且非只读状态！输入任意键以重试。\nPermission denied! Please ensure the file isn't opened right now or read-only! Press any key to try again.")
                input()
            except FileNotFoundError:
                with open(path = "available-bots.xlsx") as writer:
                    LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet3")
                break
            else:
                print("\n统计完毕，共%d名英雄。请输入任意键退出。\nCount finished! There're %d champions in total. Please press any key to exit." %(count, count))
                break
        input()
        exit() #执行到此，程序结束（Here the program terminates）
    else:
        print("请输入您想要获取的版本。输入空字符串以获取最新版本英雄信息。\nPlease input the patch you want to search from. Submit an empty string to get the latest champion data. Examples: ")
        src, status = getUrl("https://raw.communitydragon.org/") #对应于DataDragon数据库的版本，下面从CommunityDragons数据库主页的源代码获取可用版本（Corresponding to getting patches DataDragon database, the following code crawl the available patches in CommunityDragon database through its homepage）
        if status != 0:
            if status == 1:
                print("CommunityDragon数据库主页访问失败！\nCommunityDragon database homepage access failed!")
                time.sleep(3)
                exit()
            elif status == 404:
                print("CommunityDragon数据库主页不存在！可能它已经变更了。请联系作者修复程序。\nCommunityDragon database homepage not found! Maybe it's changed. Please contact the author and ask for a repair.")
                time.sleep(3)
                exit()
        else:
            cdragon_homepage = src
            sourceCode = cdragon_homepage.content.decode()
            source_list = list(map(lambda x: x.strip(), sourceCode.split("\n")))
            line_re = re.compile(r'<tr><td class="link"><a href="[0-9]*\.[0-9]*/" title="[0-9]*\.[0-9]*">[0-9]*\.[0-9]*/</a></td><td class="size">-</td><td class="date">[0-9]*-[a-zA-Z]*-[0-9]* [0-9]*:[0-9]*</td></tr>')
            patch_re = re.compile(r'[0-9]*\.[0-9]*')
            patches_cdragon = []
            for line in source_list:
                matchedLine = line_re.search(line) #先通过一个比较长的正则表达式筛选包含版本信息的CSS代码行（First filter the CSS code lines that contain patch information through a long regular expression）
                if matchedLine:
                    matchedPatch = patch_re.search(line).group() #在包含版本信息的CSS代码中再获取版本字符串（Then obtains patch string from the CSS code that contain it）
                    patches_cdragon.append(matchedPatch)
            patches_cdragon = patch_sort(patches_cdragon)
            patches_cdragon.insert(0, "pbe")
            patches_cdragon.insert(0, "latest")
            print(", ".join(patches_cdragon))
            while True:
                patch_in_url = input()
                if patch_in_url == "":
                    patch_in_url = patches_cdragon[0]
                if patch_in_url in patches_cdragon:
                    champion_folder_url = "https://raw.communitydragon.org/%s/plugins/rcp-be-lol-game-data/global/%s/v1/champions/" %(patch_in_url, language_code.lower())
                    break
                else:
                    print("版本输入有误！请重新输入。\nERROR input of patch! Please try again!")
        #下面获取每个英雄的数据资源链接（The following code obtain the data resource url of each champion）
        src, status = getUrl(champion_folder_url)
        if status != 0:
            if status == 1:
                print("英雄文件夹访问失败！\nChampion folder access failed!")
                time.sleep(3)
                exit()
            elif status == 404:
                print("英雄文件夹不存在！请联系作者修复程序。\nChampion folder not found! Please contact the author and ask for a repair.")
                time.sleep(3)
                exit()
        else:
            champion_folder = src
            sourceCode = champion_folder.content.decode()
            source_list = list(map(lambda x: x.strip(), sourceCode.split("\n")))
            line_re = re.compile(r'<tr><td class="link"><a href="-?[0-9]*\.json" title="-?[0-9]*\.json">-?[0-9]*\.json</a></td><td class="size">.*</td><td class="date">[0-9]*-[a-zA-Z]*-[0-9]* [0-9]*:[0-9]*</td></tr>')
            json_re = re.compile(r'-?[0-9]*\.json')
            champion_urls = []
            champion_files = {}
            for line in source_list:
                matchedLine = line_re.search(line)
                if matchedLine:
                    matchedJson = json_re.search(line).group()
                    champion_files[int(matchedJson[:-5])] = matchedJson
            for championId in sorted(champion_files.keys()):
                champion_urls.append(champion_folder_url + champion_files[championId])
        champion_local_default = cdragon_champion_local_default
        champion_files_ready = False
        LoLChampion = []
        for i in range(len(champion_urls)):
            champion_url = champion_urls[i]
            src, status = getUrl(champion_url)
            if status != 0:
                break
            champion = src.json()
            LoLChampion.append(champion)
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            print("获取进度（Capturing process）：%d/%d" %(i + 1, len(champion_urls)))
        else:
            champion_files_ready = True #任何一个文件获取失败都会导致程序进入离线加载模式（Any file that failed to be loaded will cause to program to load all data again offline）
        if not champion_files_ready:
            print('英雄信息获取超时！正在尝试离线加载数据……\nChampion information capture timeout! Trying loading offline data ...\n请输入英雄Json数据文件夹路径。输入空字符以使用默认相对引用路径“%s”。输入“0”以退出程序。\nPlease enter the champion Json data folder path. Enter an empty string to use the default relative path: "%s". Submit "0" to exit.' %(champion_local_default, champion_local_default))
            while True:
                LoLChampion = []
                champion_local = input()
                if champion_local == "":
                    champion_local = champion_local_default
                elif champion_local[0] == "0":
                    print("英雄数据获取失败！请检查系统网络状况和代理设置。\nChampion data capture failure! Please check the system network condition and agent configuration.")
                    time.sleep(3)
                    exit()
                try:
                    for championId in sorted(champion_files.keys()):
                        with open(champion_local + champion_files[championId], "r", encoding = "utf-8") as fp:
                            champion = json.load(fp)
                        if isinstance(champion, dict) and all([i in champion for i in ["id", "name", "alias", "title", "shortBio", "tacticalInfo", "playstyleInfo", "squarePortraitPath", "stingerSfxPath", "chooseVoPath", "banVoPath", "roles", "recommendedItemDefaults", "skins", "passive", "spells"]]) and all(isinstance(i, dict) for i in [champion["tacticalInfo"], champion["playstyleInfo"], champion["passive"]]) and all(i in champion["tacticalInfo"] for i in ["style", "difficulty", "damageType"]) and all(i in champion["playstyleInfo"] for i in ["damage", "durability", "crowdControl", "mobility", "utility"]) and all(i in champion["passive"] for i in ["name", "abilityIconPath", "abilityVideoPath", "abilityVideoImagePath", "description"]) and all(isinstance(i, int) for i in [champion["id"], champion["tacticalInfo"]["style"], champion["tacticalInfo"]["difficulty"], champion["playstyleInfo"]["damage"], champion["playstyleInfo"]["durability"], champion["playstyleInfo"]["crowdControl"], champion["playstyleInfo"]["mobility"], champion["playstyleInfo"]["utility"]]) and all(isinstance(i, str) for i in [champion["name"], champion["alias"], champion["title"], champion["shortBio"], champion["squarePortraitPath"], champion["stingerSfxPath"], champion["chooseVoPath"], champion["banVoPath"], champion["tacticalInfo"]["damageType"], champion["passive"]["name"], champion["passive"]["abilityIconPath"], champion["passive"]["abilityVideoPath"], champion["passive"]["abilityVideoImagePath"], champion["passive"]["description"]]) and all(isinstance(i, list) for i in [champion["roles"], champion["recommendedItemDefaults"], champion["skins"], champion["spells"]]):
                            LoLChampion.append(champion)
                        else:
                            print("数据格式错误！请选择一个符合CommunityDragon数据库中记录的英雄数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the champion data archived in CommunityDragon database (%s)!" %(champion_url, champion_url))
                            break
                except FileNotFoundError:
                    print("未找到文件%s！请输入正确的英雄Json数据文件夹路径！\nFile %s NOT found! Please input a correct champion Json data folder path!" %(champion_local, champion_local))
                    continue
                except OSError:
                    print("数据文件名不合法！请输入含有英雄信息的本地文件的路径！\nIllegal data filename! Please input the path of a local file with champion information.")
                    continue
                except json.decoder.JSONDecodeError:
                    print("数据格式错误！请选择一个符合CommunityDragon数据库中记录的英雄数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the champion data archived in CommunityDragon database (%s)!" %(champion_url, champion_url))
                    continue
                else:
                    break
        #下面按照程序需求对数据资源进行一定的整理（The following code sort out the data resource according to the program's need）
        LoLChampions = {}
        for champion in LoLChampion:
            LoLChampions[champion["id"]] = champion
        LoLChampions_header = {"id": "英雄序号", "name": "称号", "alias": "英雄代号", "title": "名称", "shortBio": "背景简介", "squarePortraitPath": "方格头像路径", "stingerSfxPath": "锁定音效路径", "chooseVoPath": "锁定台词路径", "banVoPath": "禁用台词路径", "tacticalInfo: style": "战略信息：风格【表明英雄的伤害输出方式的倾向（普攻vs技能）】", "tacticalInfo: difficulty": "战略信息：难度（英雄的使用难度）", "tacticalInfo: damageType": "战略信息：伤害【表明英雄的伤害类型的倾向（物理伤害、魔法伤害或者混合伤害）】", "playStyleInfo: damage": "玩法雷达图：伤害（用来对敌方英雄造成伤害的英雄技能）得分", "playStyleInfo: durability": "玩法雷达图：强韧（用来吸收来自敌方英雄伤害的英雄技能）得分", "playStyleInfo: crowdControl": "玩法雷达图：控制（用来对敌方英雄施加诸如减速和晕眩的有害效果的英雄技能）得分", "playStyleInfo: mobility": "玩法雷达图：机动（通过使用闪现或位移来快速在地图四处移动的英雄技能）得分", "playStyleInfo: utility": "玩法雷达图：功能（用来对友军提供护盾、治疗或移动速度等有益效果的英雄技能）得分", "role: assassin": "角色定位：刺客", "role: fighter": "角色定位：战士", "role: mage": "角色定位：法师", "role: marksman": "角色定位：射手", "role: support": "角色定位：辅助", "role: tank": "角色定位：坦克"}
        LoLChampions_header_keys = list(LoLChampions_header.keys())
        LoLChampions_data = {}
        damageTypes = {"kPhysical": "物理伤害", "kMagic": "魔法伤害", "kMixed": "混合伤害"}
        #damageTypes = {"kPhysical": "Physical", "kMagic": "Magic", "kMixed": "Mixed"}
        for i in range(len(LoLChampions_header_keys)):
            key = LoLChampions_header_keys[i]
            LoLChampions_data[key] = []
        print("championId\tname\ttitle\talias")
        count = 0
        for i in sorted(LoLChampions.keys()):
            champion = LoLChampions[i]
            print("%s\t%s\t%s\t%s" %(champion["id"], champion["name"], champion["title"], champion["alias"]))
            if champion["id"] != -1: #API中存在一个id为-1的英雄。该英雄不计入英雄个数（There's a champion with the id -1 in API. It won't be counted)
                count += 1
            for j in range(len(LoLChampions_header_keys)):
                key = LoLChampions_header_keys[j]
                if j <= 8:
                    LoLChampions_data[key].append(champion[key])
                elif j <= 11:
                    if j == 11:
                        LoLChampions_data[key].append(damageTypes[champion["tacticalInfo"][key[14:]]])
                    else:
                        LoLChampions_data[key].append(champion["tacticalInfo"][key[14:]])
                elif j <= 16:
                    LoLChampions_data[key].append(champion["playstyleInfo"][key[15:]])
                else:
                    if key[6:] in champion["roles"]:
                        LoLChampions_data[key].append("√")
                    else:
                        LoLChampions_data[key].append("")
        LoLChampions_statistics_output_order = [0, 1, 3, 2, 17, 18, 19, 20, 21, 22, 11, 9, 10, 12, 13, 14, 15, 16, 4, 5, 6, 7, 8]
        LoLChampions_data_organized = {}
        for i in LoLChampions_statistics_output_order:
            key = LoLChampions_header_keys[i]
            LoLChampions_data_organized[key] = LoLChampions_data[key]
        LoLChampions_df = pandas.DataFrame(data = LoLChampions_data_organized)
        LoLChampions_df = pandas.concat([pandas.DataFrame([LoLChampions_header])[LoLChampions_df.columns], LoLChampions_df], ignore_index = True)
        while True:
            try:
                with pandas.ExcelWriter(path = "available-bots.xlsx", mode = "a", if_sheet_exists = "replace") as writer:
                    LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet3")
            except PermissionError:
                print("无写入权限！请确保文件未被打开且非只读状态！输入任意键以重试。\nPermission denied! Please ensure the file isn't opened right now or read-only! Press any key to try again.")
                input()
            except FileNotFoundError:
                with open(path = "available-bots.xlsx") as writer:
                    LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet3")
                break
            else:
                print("\n统计完毕，共%d名英雄。请输入任意键退出。\nCount finished! There're %d champions in total. Please press any key to exit." %(count, count))
                break
        input()
        exit() #执行到此，程序结束（Here the program terminates）
connector = Connector()

async def get_summoner_data(connection):
    data = await connection.request('GET', '/lol-summoner/v1/current-summoner')
    global summoner
    summoner = await data.json()
    print("displayName:    %s" %(summoner["gameName"] + "#" + summoner["tagLine"]))
    print("summonerId:     %s" %(summoner["summonerId"]))
    print("puuid:          %s" %(summoner["puuid"]))
    print("-")


#-----------------------------------------------------------------------------
#  lockfile
#-----------------------------------------------------------------------------
async def update_lockfile(connection):
    import os
    path = os.path.join(connection.installation_path.encode('gb18030').decode('utf-8'), 'lockfile')
    if os.path.isfile(path):
        file = open(path, 'w+')
        text = "LeagueClient:%d:%d:%s:%s" %(connection.pid, connection.port, connection.auth_key, connection.protocols[0])
        file.write(text)
        file.close()
    return None

async def get_lockfile(connection):
    import os
    path = os.path.join(connection.installation_path.encode('gb18030').decode('utf-8'), 'lockfile')
    if os.path.isfile(path):
        file = open(path, 'r')
        text = file.readline().split(':')
        file.close()
        print(connection.address)
        print(f'riot    {connection.auth_key}')
        return connection.auth_key
    return None

#-----------------------------------------------------------------------------
# 向服务器发送指令（Send commands to the server）
#-----------------------------------------------------------------------------
async def send_commands(connection):
    method = ""
    command = "0"
    print("请依次输入方法和统一资源标识符，以空格为分隔符：\nPlease enter the method and URI, split by space:\n示例：\nExamples:\nGET /lol-lobby/v2/lobby\nPOST /lol-lobby/v2/lobby/matchmaking/search\nPUT /lol-lobby/v2/lobby/partyType\nDELETE /lol-lobby-team-builder/v1/lobby\nPATCH /lol-lobby-team-builder/champ-select/v1/session/my-selection\n")
    while command[0] != "3":
        method, command = input().split()
        if command == "":
            command = "0"
        else:
            data = await connection.request(method, command)
            print(await data.json())

#-----------------------------------------------------------------------------
# 创建训练模式 5V5 自定义房间（Create a Practice Tool lobby）
#-----------------------------------------------------------------------------
async def create_custom_lobby(connection):
    custom = {
        "customGameLobby": {
            "configuration": {
                "gameMode": "PRACTICETOOL",
                "gameMutator": "",
                "gameServerRegion": "",
                "mapId": 11,
                "mutators": {
                    "id": 1
                },
            "spectatorPolicy": "AllAllowed",
            "teamSize": 5
            },
            "lobbyName": "可用电脑英雄测试（程序结束前请勿退出）",
            "lobbyPassword": ""
        },
        "isCustom": True
    }
    await connection.request("POST", "/lol-lobby/v2/lobby", data=custom)

#-----------------------------------------------------------------------------
# 统计英雄数量（Count all champions）
#-----------------------------------------------------------------------------
async def count_all_champions(connection):
    LoLChampion = await (await connection.request("GET", "/lol-champions/v1/inventories/%s/champions" %summoner["summonerId"])).json()
    LoLChampions = {}
    for champion in LoLChampion:
        LoLChampions[champion["id"]] = champion
    LoLChampions_header = {"active": "可用性", "alias": "英雄代号", "banVoPath": "禁用台词路径", "baseLoadScreenPath": "加载界面图像路径", "baseSplashPath": "英雄封面路径", "botEnabled": "电脑模型激活情况", "chooseVoPath": "锁定台词路径", "disabledQueues": "禁用队列", "freeToPlay": "允许免费使用", "id": "英雄序号", "name": "称号", "purchased": "购买日期", "rankedPlayEnabled": "排位许可", "squarePortraitPath": "方格头像路径", "stingerSfxPath": "锁定音效路径", "title": "名称", "ownership: loyaltyReward": "获取方式：排位赛段奖励", "ownership: owned": "已拥有", "ownership: xboxGPReward": "获取方式：Xbox Game Pass奖励", "ownership: rental: endDate": "租借截止日期", "ownership: rental: purchaseDate": "租借日期", "ownership: rental: rented": "已租借", "ownership: rental: winCountRemaining": "租借可用胜场数", "role: assassin": "角色定位：刺客", "role: fighter": "角色定位：战士", "role: mage": "角色定位：法师", "role: marksman": "角色定位：射手", "role: support": "角色定位：辅助", "role: tank": "角色定位：坦克", "tacticalInfo: damageType": "战略信息：伤害【表明英雄的伤害类型的倾向（物理伤害、魔法伤害或者混合伤害）】", "tacticalInfo: difficulty": "战略信息：难度（英雄的使用难度）", "tacticalInfo: style": "战略信息：风格【表明英雄的伤害输出方式的倾向（普攻vs技能）】", "recommendedPosition: TOP": "推荐路线：上路", "recommendedPosition: JUNGLE": "推荐路线：打野", "recommendedPosition: MIDDLE": "推荐路线：中路", "recommendedPosition: BOTTOM": "推荐路线：下路", "recommendedPosition: UTILITY": "推荐路线：辅助"}
    LoLChampions_header_keys = list(LoLChampions_header.keys())
    LoLChampions_data = {}
    recommended_position_for_champion = await (await connection.request("GET", "/lol-perks/v1/recommended-champion-positions")).json()
    damageTypes = {"kPhysical": "物理伤害", "kMagic": "魔法伤害", "kMixed": "混合伤害"}
    #damageTypes = {"kPhysical": "Physical", "kMagic": "Magic", "kMixed": "Mixed"}
    for i in range(len(LoLChampions_header_keys)):
        key = LoLChampions_header_keys[i]
        LoLChampions_data[key] = []
    print("championId\tname\ttitle\talias")
    count = 0
    for i in sorted(LoLChampions.keys()):
        champion = LoLChampions[i]
        print("%d\t%s\t%s\t%s" %(champion["id"], champion["name"], champion["title"], champion["alias"]))
        if champion["id"] != -1: #API中存在一个id为-1的英雄。该英雄不计入英雄个数（There's a champion with the id -1 in API. It won't be counted)
            count += 1
        for j in range(len(LoLChampions_header_keys)):
            key = LoLChampions_header_keys[j]
            if j <= 15:
                if j == 11:
                    if champion[key] == 0:
                        LoLChampions_data[key].append("")
                    else:
                        try:
                            LoLChampions_data[key].append(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(champion[key] // 1000)))
                        except OSError: #出现了购买时间戳为18446744073709550616的英雄（There's a champion with the purchased timestamp 18446744073709550616）
                            LoLChampions_data[key].append("")
                else:
                    LoLChampions_data[key].append(champion[key])
            elif j <= 22:
                if j <= 18:
                    LoLChampions_data[key].append(champion["ownership"][key[11:]])
                else:
                    if j == 19 or j == 20:
                        if champion["ownership"]["rental"][key[19:]] == 0:
                            LoLChampions_data[key].append("")
                        else:
                            try:
                                LoLChampions_data[key].append(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(champion["ownership"]["rental"][key[19:]] // 1000)))
                            except OSError: #出现了租借时间戳为18446744073709550616的英雄（There's a champion with the rented timestamp 18446744073709550616）
                                LoLChampions_data[key].append("")
                    else:
                        LoLChampions_data[key].append(champion["ownership"]["rental"][key[19:]])
            elif j <= 28:
                if key[6:] in champion["roles"]:
                    LoLChampions_data[key].append(True)
                else:
                    LoLChampions_data[key].append(False)
            elif j <= 31:
                if j == 29:
                    LoLChampions_data[key].append(damageTypes[champion["tacticalInfo"][key[14:]]])
                else:
                    LoLChampions_data[key].append(champion["tacticalInfo"][key[14:]])
            else:
                if i == -1:
                    LoLChampions_data[key].append(False)
                elif key[21:] in recommended_position_for_champion[str(i)]["recommendedPositions"]:
                    LoLChampions_data[key].append(True)
                else:
                    LoLChampions_data[key].append(False)
    LoLChampions_statistics_output_order = [9, 10, 15, 1, 5, 23, 24, 25, 26, 27, 28, 32, 33, 34, 35, 36, 29, 31, 30, 17, 11, 16, 18, 8, 20, 21, 19, 22, 12, 7, 13, 3, 4, 14, 6, 2]
    LoLChampions_data_organized = {}
    for i in LoLChampions_statistics_output_order:
        key = LoLChampions_header_keys[i]
        LoLChampions_data_organized[key] = LoLChampions_data[key]
    LoLChampions_df = pandas.DataFrame(data = LoLChampions_data_organized)
    print("正在优化逻辑值显示……\nOptimizing the display of boolean values ...")
    for column in LoLChampions_df:
        if LoLChampions_df[column].dtype == "bool":
            LoLChampions_df[column] = LoLChampions_df[column].astype(str)
            for i in range(len(LoLChampions_df)):
                LoLChampions_df.loc[i, column] = "√" if LoLChampions_df[column][i] == "True" else ""
    print("逻辑值显示优化完成！\nBoolean value display optimization finished!")
    LoLChampions_df = pandas.concat([pandas.DataFrame([LoLChampions_header])[LoLChampions_df.columns], LoLChampions_df], ignore_index = True)
    while True:
        try:
            with pandas.ExcelWriter(path = "available-bots.xlsx", mode = "a", if_sheet_exists = "replace") as writer:
                LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet3")
        except PermissionError:
            print("无写入权限！请确保文件未被打开且非只读状态！输入任意键以重试。\nPermission denied! Please ensure the file isn't opened right now or read-only! Press any key to try again.")
            input()
        except FileNotFoundError:
            with open(path = "available-bots.xlsx") as writer:
                LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet3")
            break
        else:
            print("\n统计完毕，共%d名英雄。请输入任意键退出。\nCount finished! There're %d champions in total. Please press any key to exit." %(count, count))
            break
    input()

#-----------------------------------------------------------------------------
# 统计电脑英雄数量（Count all bot champions）
#-----------------------------------------------------------------------------
async def count_all_bots(connection):
    LoLChampion = await (await connection.request("GET", "/lol-champions/v1/inventories/%s/champions" %summoner["summonerId"])).json()
    LoLChampions = {}
    print("正在统计具有电脑模型的英雄……请勿退出房间！\nCounting botEnabled champions ... Please don't exit the lobby!\n")
    await create_custom_lobby(connection)
    print("championId\tname\ttitle\talias")
    count = 0
    for champion in LoLChampion:
        botUuid = str(uuid.uuid4())
        bot = {"championId": champion["id"], "botDifficulty": "RSINTERMEDIATE", "teamId": "200", "position": "TOP", "botUuid": botUuid}
        response = await (await connection.request("POST", "/lol-lobby/v1/lobby/custom/bots", data = bot)).json()
        time.sleep(0.2) #由于服务器响应速度原因，从添加电脑到房间信息更新，需要0.2秒的缓冲时间（0.2s buffer time is needed between adding a bot and updating the lobby information due to the server response speed）
        lobby = await(await connection.request("GET", "/lol-lobby/v2/lobby")).json()
        if len(lobby["gameConfig"]["customTeam200"]) == 1 and lobby["gameConfig"]["customTeam200"][0]["botChampionId"] == champion["id"]:
            LoLChampions[champion["id"]] = champion
            print("%d\t%s\t%s\t%s" %(champion["id"], champion["name"], champion["title"], champion["alias"]))
            if champion["id"] != -1: #API中存在一个id为-1的英雄。该英雄不计入英雄个数（There's a champion with the id -1 in API. It won't be counted)
                count += 1
            response = await (await connection.request("DELETE", "/lol-lobby/v1/lobby/custom/bots/%s/%s/200" %(lobby["gameConfig"]["customTeam200"][0]["botId"], botUuid))).json()
    print("\n统计完毕，共%d名英雄。\nCount finished! There're %d champions in total." %(count, count))
    #下面按照程序需求对数据资源进行一定的整理（The following code sort out the data resource according to the program's need）
    print("正在整理数据……\nSorting out the data ...")
    LoLChampions_header = {"active": "可用性", "alias": "英雄代号", "banVoPath": "禁用台词路径", "baseLoadScreenPath": "加载界面图像路径", "baseSplashPath": "英雄封面路径", "botEnabled": "电脑模型激活情况", "chooseVoPath": "锁定台词路径", "disabledQueues": "禁用队列", "freeToPlay": "允许免费使用", "id": "英雄序号", "name": "称号", "purchased": "购买日期", "rankedPlayEnabled": "排位许可", "squarePortraitPath": "方格头像路径", "stingerSfxPath": "锁定音效路径", "title": "名称", "ownership: loyaltyReward": "获取方式：排位赛段奖励", "ownership: owned": "已拥有", "ownership: xboxGPReward": "获取方式：Xbox Game Pass奖励", "ownership: rental: endDate": "租借截止日期", "ownership: rental: purchaseDate": "租借日期", "ownership: rental: rented": "已租借", "ownership: rental: winCountRemaining": "租借可用胜场数", "role: assassin": "角色定位：刺客", "role: fighter": "角色定位：战士", "role: mage": "角色定位：法师", "role: marksman": "角色定位：射手", "role: support": "角色定位：辅助", "role: tank": "角色定位：坦克", "tacticalInfo: damageType": "战略信息：伤害【表明英雄的伤害类型的倾向（物理伤害、魔法伤害或者混合伤害）】", "tacticalInfo: difficulty": "战略信息：难度（英雄的使用难度）", "tacticalInfo: style": "战略信息：风格【表明英雄的伤害输出方式的倾向（普攻vs技能）】", "recommendedPosition: TOP": "推荐路线：上路", "recommendedPosition: JUNGLE": "推荐路线：打野", "recommendedPosition: MIDDLE": "推荐路线：中路", "recommendedPosition: BOTTOM": "推荐路线：下路", "recommendedPosition: UTILITY": "推荐路线：辅助"}
    LoLChampions_header_keys = list(LoLChampions_header.keys())
    LoLChampions_data = {}
    recommended_position_for_champion = await (await connection.request("GET", "/lol-perks/v1/recommended-champion-positions")).json()
    damageTypes = {"kPhysical": "物理伤害", "kMagic": "魔法伤害", "kMixed": "混合伤害"}
    #damageTypes = {"kPhysical": "Physical", "kMagic": "Magic", "kMixed": "Mixed"}
    for i in range(len(LoLChampions_header_keys)):
        key = LoLChampions_header_keys[i]
        LoLChampions_data[key] = []
    for i in sorted(LoLChampions.keys()):
        champion = LoLChampions[i]
        for j in range(len(LoLChampions_header_keys)):
            key = LoLChampions_header_keys[j]
            if j <= 15:
                if j == 11:
                    if champion[key] == 0:
                        LoLChampions_data[key].append("")
                    else:
                        try:
                            LoLChampions_data[key].append(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(champion[key] // 1000)))
                        except OSError: #出现了购买时间戳为18446744073709550616的英雄（There's a champion with the purchased timestamp 18446744073709550616）
                            LoLChampions_data[key].append("")
                else:
                    LoLChampions_data[key].append(champion[key])
            elif j <= 22:
                if j <= 18:
                    LoLChampions_data[key].append(champion["ownership"][key[11:]])
                else:
                    if j == 19 or j == 20:
                        if champion["ownership"]["rental"][key[19:]] == 0:
                            LoLChampions_data[key].append("")
                        else:
                            try:
                                LoLChampions_data[key].append(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(champion["ownership"]["rental"][key[19:]] // 1000)))
                            except OSError: #出现了租借时间戳为18446744073709550616的英雄（There's a champion with the rented timestamp 18446744073709550616）
                                LoLChampions_data[key].append("")
                    else:
                        LoLChampions_data[key].append(champion["ownership"]["rental"][key[19:]])
            elif j <= 28:
                if key[6:] in champion["roles"]:
                    LoLChampions_data[key].append(True)
                else:
                    LoLChampions_data[key].append(False)
            elif j <= 31:
                if j == 29:
                    LoLChampions_data[key].append(damageTypes[champion["tacticalInfo"][key[14:]]])
                else:
                    LoLChampions_data[key].append(champion["tacticalInfo"][key[14:]])
            else:
                if i == -1:
                    LoLChampions_data[key].append(False)
                elif key[21:] in recommended_position_for_champion[str(i)]["recommendedPositions"]:
                    LoLChampions_data[key].append(True)
                else:
                    LoLChampions_data[key].append(False)
    LoLChampions_statistics_output_order = [9, 10, 15, 1, 5, 23, 24, 25, 26, 27, 28, 32, 33, 34, 35, 36, 29, 31, 30, 17, 11, 16, 18, 8, 20, 21, 19, 22, 12, 7, 13, 3, 4, 14, 6, 2]
    LoLChampions_data_organized = {}
    for i in LoLChampions_statistics_output_order:
        key = LoLChampions_header_keys[i]
        LoLChampions_data_organized[key] = LoLChampions_data[key]
    LoLChampions_df = pandas.DataFrame(data = LoLChampions_data_organized)
    print("正在优化逻辑值显示……\nOptimizing the display of boolean values ...")
    for column in LoLChampions_df:
        if LoLChampions_df[column].dtype == "bool":
            LoLChampions_df[column] = LoLChampions_df[column].astype(str)
            for i in range(len(LoLChampions_df)):
                LoLChampions_df.loc[i, column] = "√" if LoLChampions_df[column][i] == "True" else ""
    print("逻辑值显示优化完成！\nBoolean value display optimization finished!")
    LoLChampions_df = pandas.concat([pandas.DataFrame([LoLChampions_header])[LoLChampions_df.columns], LoLChampions_df], ignore_index = True)
    while True:
        try:
            with pandas.ExcelWriter(path = "available-bots.xlsx", mode = "a", if_sheet_exists = "replace") as writer:
                LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet2")
        except PermissionError:
            print("无写入权限！请确保文件未被打开且非只读状态！输入任意键以重试。\nPermission denied! Please ensure the file isn't opened right now or read-only! Press any key to try again.")
            input()
        except FileNotFoundError:
            with open(path = "available-bots.xlsx") as writer:
                LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet2")
            break
        else:
            print("英雄数据导出完成！请输入任意键退出。\nChampion data exported! Please press any key to exit.")
            break
    input()

#-----------------------------------------------------------------------------
# 统计当前房间可用电脑英雄数量（Count available bots in the current lobby）
#-----------------------------------------------------------------------------
async def count_available_bots(connection):
    lobby = await(await connection.request("GET", "/lol-lobby/v2/lobby")).json()
    if "errorCode" in lobby and lobby["message"] == "LOBBY_NOT_FOUND":
        print("请确保您正在房间内！程序即将退出！\nPlease make sure you're in a lobby! The program will exit soon!")
        time.sleep(3)
        exit()
    bots_enabled = await (await connection.request("GET", "/lol-lobby/v2/lobby/custom/bots-enabled")).json()
    if bots_enabled == False:
        print("该房间无可用电脑玩家。请输入任意键退出。\nThere're no available bot champions in this lobby. Please press any key to exit.")
        input()
        return 0
    available_bots = await (await connection.request("GET", "/lol-lobby/v2/lobby/custom/available-bots")).json()
    available_botIds = list(map(lambda x: x["id"], available_bots))
    LoLChampion = await (await connection.request("GET", "/lol-champions/v1/inventories/%s/champions" %summoner["summonerId"])).json()
    LoLChampions = {}
    for champion in LoLChampion:
        if champion["id"] in available_botIds:
            LoLChampions[champion["id"]] = champion
    #下面按照程序需求对数据资源进行一定的整理（The following code sort out the data resource according to the program's need）
    LoLChampions_header = {"active": "可用性", "alias": "英雄代号", "banVoPath": "禁用台词路径", "baseLoadScreenPath": "加载界面图像路径", "baseSplashPath": "英雄封面路径", "botEnabled": "电脑模型激活情况", "chooseVoPath": "锁定台词路径", "disabledQueues": "禁用队列", "freeToPlay": "允许免费使用", "id": "英雄序号", "name": "称号", "purchased": "购买日期", "rankedPlayEnabled": "排位许可", "squarePortraitPath": "方格头像路径", "stingerSfxPath": "锁定音效路径", "title": "名称", "ownership: loyaltyReward": "获取方式：排位赛段奖励", "ownership: owned": "已拥有", "ownership: xboxGPReward": "获取方式：Xbox Game Pass奖励", "ownership: rental: endDate": "租借截止日期", "ownership: rental: purchaseDate": "租借日期", "ownership: rental: rented": "已租借", "ownership: rental: winCountRemaining": "租借可用胜场数", "role: assassin": "角色定位：刺客", "role: fighter": "角色定位：战士", "role: mage": "角色定位：法师", "role: marksman": "角色定位：射手", "role: support": "角色定位：辅助", "role: tank": "角色定位：坦克", "tacticalInfo: damageType": "战略信息：伤害【表明英雄的伤害类型的倾向（物理伤害、魔法伤害或者混合伤害）】", "tacticalInfo: difficulty": "战略信息：难度（英雄的使用难度）", "tacticalInfo: style": "战略信息：风格【表明英雄的伤害输出方式的倾向（普攻vs技能）】", "recommendedPosition: TOP": "推荐路线：上路", "recommendedPosition: JUNGLE": "推荐路线：打野", "recommendedPosition: MIDDLE": "推荐路线：中路", "recommendedPosition: BOTTOM": "推荐路线：下路", "recommendedPosition: UTILITY": "推荐路线：辅助"}
    LoLChampions_header_keys = list(LoLChampions_header.keys())
    LoLChampions_data = {}
    recommended_position_for_champion = await (await connection.request("GET", "/lol-perks/v1/recommended-champion-positions")).json()
    damageTypes = {"kPhysical": "物理伤害", "kMagic": "魔法伤害", "kMixed": "混合伤害"}
    #damageTypes = {"kPhysical": "Physical", "kMagic": "Magic", "kMixed": "Mixed"}
    for i in range(len(LoLChampions_header_keys)):
        key = LoLChampions_header_keys[i]
        LoLChampions_data[key] = []
    print("championId\tname\ttitle\talias")
    count = 0
    for i in sorted(LoLChampions.keys()):
        champion = LoLChampions[i]
        print("%d\t%s\t%s\t%s" %(champion["id"], champion["name"], champion["title"], champion["alias"]))
        if champion["id"] != -1: #API中存在一个id为-1的英雄。该英雄不计入英雄个数（There's a champion with the id -1 in API. It won't be counted)
            count += 1
        for j in range(len(LoLChampions_header_keys)):
            key = LoLChampions_header_keys[j]
            if j <= 15:
                if j == 11:
                    if champion[key] == 0:
                        LoLChampions_data[key].append("")
                    else:
                        try:
                            LoLChampions_data[key].append(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(champion[key] // 1000)))
                        except OSError: #出现了购买时间戳为18446744073709550616的英雄（There's a champion with the purchased timestamp 18446744073709550616）
                            LoLChampions_data[key].append("")
                else:
                    LoLChampions_data[key].append(champion[key])
            elif j <= 22:
                if j <= 18:
                    LoLChampions_data[key].append(champion["ownership"][key[11:]])
                else:
                    if j == 19 or j == 20:
                        if champion["ownership"]["rental"][key[19:]] == 0:
                            LoLChampions_data[key].append("")
                        else:
                            try:
                                LoLChampions_data[key].append(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(champion["ownership"]["rental"][key[19:]] // 1000)))
                            except OSError: #出现了租借时间戳为18446744073709550616的英雄（There's a champion with the rented timestamp 18446744073709550616）
                                LoLChampions_data[key].append("")
                    else:
                        LoLChampions_data[key].append(champion["ownership"]["rental"][key[19:]])
            elif j <= 28:
                if key[6:] in champion["roles"]:
                    LoLChampions_data[key].append(True)
                else:
                    LoLChampions_data[key].append(False)
            elif j <= 31:
                if j == 29:
                    LoLChampions_data[key].append(damageTypes[champion["tacticalInfo"][key[14:]]])
                else:
                    LoLChampions_data[key].append(champion["tacticalInfo"][key[14:]])
            else:
                if i == -1:
                    LoLChampions_data[key].append(False)
                elif key[21:] in recommended_position_for_champion[str(i)]["recommendedPositions"]:
                    LoLChampions_data[key].append(True)
                else:
                    LoLChampions_data[key].append(False)
    LoLChampions_statistics_output_order = [9, 10, 15, 1, 5, 23, 24, 25, 26, 27, 28, 32, 33, 34, 35, 36, 29, 31, 30, 17, 11, 16, 18, 8, 20, 21, 19, 22, 12, 7, 13, 3, 4, 14, 6, 2]
    LoLChampions_data_organized = {}
    for i in LoLChampions_statistics_output_order:
        key = LoLChampions_header_keys[i]
        LoLChampions_data_organized[key] = LoLChampions_data[key]
    LoLChampions_df = pandas.DataFrame(data = LoLChampions_data_organized)
    print("正在优化逻辑值显示……\nOptimizing the display of boolean values ...")
    for column in LoLChampions_df:
        if LoLChampions_df[column].dtype == "bool":
            LoLChampions_df[column] = LoLChampions_df[column].astype(str)
            for i in range(len(LoLChampions_df)):
                LoLChampions_df.loc[i, column] = "√" if LoLChampions_df[column][i] == "True" else ""
    print("逻辑值显示优化完成！\nBoolean value display optimization finished!")
    LoLChampions_df = pandas.concat([pandas.DataFrame([LoLChampions_header])[LoLChampions_df.columns], LoLChampions_df], ignore_index = True)
    while True:
        try:
            with pandas.ExcelWriter(path = "available-bots.xlsx", mode = "a", if_sheet_exists = "replace") as writer:
                LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet1")
        except PermissionError:
            print("无写入权限！请确保文件未被打开且非只读状态！输入任意键以重试。\nPermission denied! Please ensure the file isn't opened right now or read-only! Press any key to try again.")
            input()
        except FileNotFoundError:
            with open(path = "available-bots.xlsx") as writer:
                LoLChampions_df.to_excel(excel_writer = writer, sheet_name = "Sheet1")
            break
        else:
            print("\n统计完毕，共%d名英雄。请输入任意键退出。\nCount finished! There're %d champions in total. Please press any key to exit." %(count, count))
            break
    input()

#-----------------------------------------------------------------------------
# websocket
#-----------------------------------------------------------------------------
@connector.ready
async def connect(connection):
    await get_summoner_data(connection)
    #await send_commands(connection)
    print("请选择统计类型：\nPlease select which type of champions to count:\n1\t所有英雄（All champions）\n2\t所有电脑英雄（All bot champions）\n3\t当前房间可用电脑英雄（Available bot champions in this lobby）")
    while True:
        mode = input()
        if mode == "":
            continue
        elif mode[0] == "1":
            await count_all_champions(connection)
            break
        elif mode[0] == "2":
            await count_all_bots(connection)
            break
        elif mode[0] == "3":
            await count_available_bots(connection)
            break
        else:
            print("您的输入有误，请重新输入！\nERROR input! Please try again!")

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------
connector.start()
