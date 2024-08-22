import json, os, pandas, requests, shutil, time, unicodedata
from wcwidth import wcswidth
from urllib.parse import urljoin

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
            if http_err.response.status_code == 404:
                return (source, 404)
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

def count_nonASCII(s: str): #统计一个字符串中占用命令行2个宽度单位的字符个数（Count the number of characters that take up 2 width unit in CMD）
    return sum([unicodedata.east_asian_width(character) in ("F", "W") for character in list(str(s))])

def format_df(df: pandas.DataFrame, width_exceed_ask: bool = True, direct_print: bool = False): #按照每列最长字符串的命令行宽度加上2，再根据每个数据的中文字符数量决定最终格式化输出的字符串宽度（Get the width of the longest string of each column, add it by 2, and substract it by the number of each cell string's Chinese characters to get the final width for each cell to print using `format` function）
    df = df.reset_index(drop = True) #这一步至关重要，因为下面的操作前提是行号是默认的（This step is crucial, for the following operations are based on the dataframe with the default row index）
    maxLens = {}
    maxWidth = shutil.get_terminal_size()[0]
    fields = df.columns.tolist()
    for field in fields:
        maxLens[field] = max(max(map(lambda x: wcswidth(str(x)), df[field])), wcswidth(str(field))) + 2
    if sum(maxLens.values()) + 2 * (len(fields) - 1) > maxWidth: #因为输出的时候，相邻两列之间需要有两个空格分隔，所以在计算总宽度的时候必须算上这些空格的宽度（Because two spaces are used between each pair of columns, the width they take up must be taken into consideration）
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
    for i in range(df.shape[1]):
        field = fields[i]
        tmp = "{0:^{w}}".format(field, w = maxLens[str(field)] - count_nonASCII(str(field))) #算法实现原理：全ASCII字符串可以直接参考前面计算好的宽度进行格式化，因为每个字符占用1个字符宽度。如果字符串中包含一个中文字符，而格式化的宽度不变的话，那么最终格式化得到的结果是整个字符串宽度会多一个单位。所以，当字符串中包含中文字符时，传入format函数的宽度参数应当在原来计算好的宽度的基础上减去中文字符的个数（Algorithm principle: A string that consists of all ASCII characters can be formatted the width based on the width calculated before (`lens`), for each character takes up 1 width unit. If a string consists of a Chinese character and the width parameter in the `format` function stays unchanged, then the final width of the formatted string is actually one unit more than expected. Therefore, when a string contains Chinese characters, the width parameter to be passed into the `format` function should be the previously calculated width subtracted by the number of Chinese characters）
        result += tmp
        #print(tmp, end = "")
        if i != df.shape[1] - 1:
            result += "  "
            #print("  ", end = "")
    result += "\n"
    #print()
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            field = fields[j]
            cell = df[field][i]
            tmp = "{0:^{w}}".format(cell, w = maxLens[field] - count_nonASCII(str(cell)))
            result += tmp
            #print(tmp, end = "")
            if j != df.shape[1] - 1:
                result += "  "
                #print("  ", end = "")
        if i != df.shape[0] - 1:
            result += "\n"
        #print() #注意这里的缩进和上一行不同（Note that here the indentation is different from the last line）
    return (result, maxLens)

#允许用户选择语言（This program allows users to select a language）
print("请选择召唤师技能和装备的输出语言【默认为中文（中国）】：\nPlease select a language to output the summoner spells and items (the default option is zh_CN):") #本来考虑把可用CDragon数据版本放在第三列，但是后来发现表头名字太长了，索性放在最后了（I had considered putting "Applicable CDragon Data Patches" at the third column, but then found the header was too long. So I put it at the last column）
language_ddragon = {1: {"CODE": "cs_CZ", "LANGUAGE (EN)": "Czech (Czech Republic)", "LANGUAGE (ZH)": "捷克语（捷克共和国）", "Applicable CDragon Data Patches": "7.1+"}, 2: {"CODE": "el_GR", "LANGUAGE (EN)": "Greek (Greece)", "LANGUAGE (ZH)": "希腊语（希腊）", "Applicable CDragon Data Patches": "9.1+"}, 3: {"CODE": "pl_PL", "LANGUAGE (EN)": "Polish (Poland)", "LANGUAGE (ZH)": "波兰语（波兰）", "Applicable CDragon Data Patches": "9.1+"}, 4: {"CODE": "ro_RO", "LANGUAGE (EN)": "Romanian (Romania)", "LANGUAGE (ZH)": "罗马尼亚语（罗马尼亚）", "Applicable CDragon Data Patches": "9.1+"}, 5: {"CODE": "hu_HU", "LANGUAGE (EN)": "Hungarian (Hungary)", "LANGUAGE (ZH)": "匈牙利语（匈牙利）", "Applicable CDragon Data Patches": "9.1+"}, 6: {"CODE": "en_GB", "LANGUAGE (EN)": "English (United Kingdom)", "LANGUAGE (ZH)": "英语（英国）", "Applicable CDragon Data Patches": "9.1+"}, 7: {"CODE": "de_DE", "LANGUAGE (EN)": "German (Germany)", "LANGUAGE (ZH)": "德语（德国）", "Applicable CDragon Data Patches": "7.1+"}, 8: {"CODE": "es_ES", "LANGUAGE (EN)": "Spanish (Spain)", "LANGUAGE (ZH)": "西班牙语（西班牙）", "Applicable CDragon Data Patches": "9.1+"}, 9: {"CODE": "it_IT", "LANGUAGE (EN)": "Italian (Italy)", "LANGUAGE (ZH)": "意大利语（意大利）", "Applicable CDragon Data Patches": "9.1+"}, 10: {"CODE": "fr_FR", "LANGUAGE (EN)": "French (France)", "LANGUAGE (ZH)": "法语（法国）", "Applicable CDragon Data Patches": "9.1+"}, 11: {"CODE": "ja_JP", "LANGUAGE (EN)": "Japanese (Japan)", "LANGUAGE (ZH)": "日语（日本）", "Applicable CDragon Data Patches": "9.1+"}, 12: {"CODE": "ko_KR", "LANGUAGE (EN)": "Korean (Korea)", "LANGUAGE (ZH)": "朝鲜语（韩国）", "Applicable CDragon Data Patches": "9.7+"}, 13: {"CODE": "es_MX", "LANGUAGE (EN)": "Spanish (Mexico)", "LANGUAGE (ZH)": "西班牙语（墨西哥）", "Applicable CDragon Data Patches": "9.1+"}, 14: {"CODE": "es_AR", "LANGUAGE (EN)": "Spanish (Argentina)", "LANGUAGE (ZH)": "西班牙语（阿根廷）", "Applicable CDragon Data Patches": "9.7+"}, 15: {"CODE": "pt_BR", "LANGUAGE (EN)": "Portuguese (Brazil)", "LANGUAGE (ZH)": "葡萄牙语（巴西）", "Applicable CDragon Data Patches": "9.1+"}, 16: {"CODE": "en_US", "LANGUAGE (EN)": "English (United States)", "LANGUAGE (ZH)": "英语（美国）", "Applicable CDragon Data Patches": "9.1+"}, 17: {"CODE": "en_AU", "LANGUAGE (EN)": "English (Australia)", "LANGUAGE (ZH)": "英语（澳大利亚）", "Applicable CDragon Data Patches": "9.1+"}, 18: {"CODE": "ru_RU", "LANGUAGE (EN)": "Russian (Russia)", "LANGUAGE (ZH)": "俄语（俄罗斯）", "Applicable CDragon Data Patches": "9.1+"}, 19: {"CODE": "tr_TR", "LANGUAGE (EN)": "Turkish (Turkey)", "LANGUAGE (ZH)": "土耳其语（土耳其）", "Applicable CDragon Data Patches": "9.1+"}, 20: {"CODE": "ms_MY", "LANGUAGE (EN)": "Malay (Malaysia)", "LANGUAGE (ZH)": "马来语（马来西亚）", "Applicable CDragon Data Patches": ""}, 21: {"CODE": "en_PH", "LANGUAGE (EN)": "English (Republic of the Philippines)", "LANGUAGE (ZH)": "英语（菲律宾共和国）", "Applicable CDragon Data Patches": "10.5+"}, 22: {"CODE": "en_SG", "LANGUAGE (EN)": "English (Singapore)", "LANGUAGE (ZH)": "英语（新加坡）", "Applicable CDragon Data Patches": "10.5+"}, 23: {"CODE": "th_TH", "LANGUAGE (EN)": "Thai (Thailand)", "LANGUAGE (ZH)": "泰语（泰国）", "Applicable CDragon Data Patches": "9.7+"}, 24: {"CODE": "vn_VN", "LANGUAGE (EN)": "Vietnamese (Viet Nam)", "LANGUAGE (ZH)": "越南语（越南）", "Applicable CDragon Data Patches": "9.7～13.9"}, 25: {"CODE": "vi_VN", "LANGUAGE (EN)": "Vietnamese (Viet Nam)", "LANGUAGE (ZH)": "越南语（越南）", "Applicable CDragon Data Patches": "12.17+"}, 26: {"CODE": "id_ID", "LANGUAGE (EN)": "Indonesian (Indonesia)", "LANGUAGE (ZH)": "印度尼西亚语（印度尼西亚）", "Applicable CDragon Data Patches": ""}, 27: {"CODE": "zh_MY", "LANGUAGE (EN)": "Chinese (Malaysia)", "LANGUAGE (ZH)": "中文（马来西亚）", "Applicable CDragon Data Patches": "10.5+"}, 28: {"CODE": "zh_CN", "LANGUAGE (EN)": "Chinese (China)", "LANGUAGE (ZH)": "中文（中国）", "Applicable CDragon Data Patches": "9.7+"}, 29: {"CODE": "zh_TW", "LANGUAGE (EN)": "Chinese (Taiwan)", "LANGUAGE (ZH)": "中文（台湾）", "Applicable CDragon Data Patches": "9.7+"}}
language_cdragon = {}
for i in language_ddragon:
    if language_ddragon[i]["CODE"] == "en_US":
        language_cdragon[language_ddragon[i]["CODE"]] = "default" #在CommunityDragon数据库上，美服正式服的数据资源代码是default，而不是小写的en_US（The code for English (US) data resources on CommunityDragon database is "default" instead of the lowercase of "en_US"）
    else:
        language_cdragon[language_ddragon[i]["CODE"]] = language_ddragon[i]["CODE"].lower()
language_dict = {"No.": [], "CODE": [], "LANGUAGE": [], "语言": [], "Applicable CDragon Data Patches": []}
for i in language_ddragon:
    language_dict["No."].append(i)
    language_dict["CODE"].append(language_ddragon[i]["CODE"])
    language_dict["LANGUAGE"].append(language_ddragon[i]["LANGUAGE (EN)"])
    language_dict["语言"].append(language_ddragon[i]["LANGUAGE (ZH)"])
    language_dict["Applicable CDragon Data Patches"].append(language_ddragon[i]["Applicable CDragon Data Patches"])
language_df = pandas.DataFrame(language_dict)
print(format_df(language_df)[0])
while True:
    language_option = input()
    if language_option == "" or language_option in [str(i) for i in range(1, 30)]:
        if language_option == "":
            language_option = "28"
        language_code = language_ddragon[int(language_option)]["CODE"]
        break
    elif language_option[0] == "0":
        exit()
    else:
        print("语言选项输入错误！请重新输入：\nERROR input of language option! Please try again:")
#获取翻译相关文件的地址（Get the URLs of translation files）
print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
print("正在读取美测服在线索引……\nReading the online index file of pbe data resources...")
source, status = getUrl("https://raw.communitydragon.org/pbe/cdragon/files.exported.txt")
if status != 0:
    if status == 1:
        print("获取索引失败！请检查系统网络状况和代理设置。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.")
    elif status == 404:
        print("获取索引失败！请检查以下链接的可用性。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\nhttps://raw.communitydragon.org/pbe/cdragon/files.exported.txt")
    time.sleep(3)
    exit()
files_exported_pbe = source.text.strip("\n").split("\n")
trans_files = [file for file in files_exported_pbe if file.endswith("trans.json") and language_cdragon[language_code] in file]
trans_files.sort()
#获取最新翻译数据（Get the latest translation data）
web_prefix = "https://raw.communitydragon.org/pbe/"
local_prefix = "离线数据（Offline Data）/cdragon/pbe/"
mode = "online"
try:
    with open("trans.json", "r", encoding = "utf-8") as fp:
        trans_data = json.load(fp)
except:
    trans_data = {}
trans_data[language_code] = {}
cnt = 0
for file in trans_files:
    url = urljoin(web_prefix, file)
    cnt += 1
    print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
    print("[%d/%d]正在获取文件（Fetching file）： %s" %(cnt, len(trans_files), url))
    src, status = getUrl(url)
    if status != 0:
        if status == 1:
            print("翻译数据获取失败！将转为离线模式。\nTranslation data capture failed. The program is going to retry in the offline mode.")
        elif status == 404:
            print("文件%s不存在！\nFile %s not found!" %(url, url))
        mode = "offline"
        break
    try:
        trans_data[language_code][os.path.dirname(file)] = src.json()
    except json.decoder.JSONDecodeError as e:
        if "Unexpected UTF-8 BOM (decode using utf-8-sig)" in str(e): #解决方案来自Stack Overflow（The solution comes from https://stackoverflow.com/questions/71025396/asyncio-and-get-unexpected-utf-8-bom）
            print("文件编码格式错误！正在尝试改用utf-8-sig编码……\nFile decode error! Trying decoding by utf-8-sig ...")
            trans_data[language_code][os.path.dirname(file)] = json.loads(src.text.encode().decode("utf-8-sig"))
if mode == "offline":
    print("请输入一个包含以下文件的文件夹，注意文件夹结构对应：\nPlease input a folder containing the following files. Note that the folder structure should comply with the following files:")
    for file in trans_files:
        print(file)
    while True:
        trans_data[language_code] = {}
        folder = input()
        if folder == "":
            folder = local_prefix
        try:
            cnt = 0
            for file in trans_files:
                path = os.path.join(folder, file)
                cnt += 1
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                print("[%d/%d]正在获取文件（Fetching file）： %s" %(cnt, len(trans_files), path))
                with open(path, "r", encoding = "utf-8") as fp:
                    src = json.load(fp)
                trans_data[language_code][os.path.dirname(file)] = src
        except FileNotFoundError:
            print('未找到文件“%s”！请输入正确的翻译数据文件夹路径！\nFile "%s" NOT found! Please input a correct translation data folder!' %(path, path))
            continue
        except OSError:
            print("数据文件名不合法！请输入合法的翻译数据文件夹路径！\nIllegal data filename! Please input a valid translation data folder.")
            continue
        except json.decoder.JSONDecodeError:
            print("数据格式错误！请选择一个符合CommunityDragon数据库中记录的翻译数据格式（%s）的数据文件！\nData format mismatched! Please select a data file that corresponds to the format of the translation data archived in CommunityDragon database (%s)!" %(urljoin(web_prefix, file), urljoin(web_prefix, file)))
            continue
        else:
            break
#调整字典键序（Adjust the order of keys）
trans_data_organized = {}
for i in language_ddragon:
    language_code_tmp = language_ddragon[i]["CODE"]
    if language_code_tmp in trans_data:
        trans_data_organized[language_code_tmp] = trans_data[language_code_tmp]
#保存获取到的翻译数据（Export the captured translation data）
with open("trans.json", "w", encoding = "utf-8") as fp:
    json.dump(trans_data_organized, fp, indent = 4, ensure_ascii = False)
print("翻译数据保存成功！请查看同文件夹下的trans.json。程序即将退出！\nAll translation data are saved successfully! Please check trans.json under the same folder. The program will now exit!")
time.sleep(3)