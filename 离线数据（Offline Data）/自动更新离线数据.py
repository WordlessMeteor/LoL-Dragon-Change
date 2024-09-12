import json, os, re, requests, shutil, time, unicodedata
import pandas as pd
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from wcwidth import wcswidth

def count_nonASCII(s: str): #统计一个字符串中占用命令行2个宽度单位的字符个数（Count the number of characters that take up 2 width unit in CMD）
    return sum([unicodedata.east_asian_width(character) in ("F", "W") for character in list(str(s))])

def format_df(df: pd.DataFrame, log, width_exceed_ask: bool = True, direct_print: bool = False): #按照每列最长字符串的命令行宽度加上2，再根据每个数据的中文字符数量决定最终格式化输出的字符串宽度（Get the width of the longest string of each column, add it by 2, and substract it by the number of each cell string's Chinese characters to get the final width for each cell to print using `format` function）
    df = df.reset_index(drop = True) #这一步至关重要，因为下面的操作前提是行号是默认的（This step is crucial, for the following operations are based on the dataframe with the default row index）
    maxLens = {}
    maxWidth = shutil.get_terminal_size()[0]
    fields = df.columns.tolist()
    for field in fields:
        maxLens[field] = max(max(map(lambda x: wcswidth(str(x)), df[field])), wcswidth(str(field))) + 2
    if sum(maxLens.values()) + 2 * (len(fields) - 1) > maxWidth: #因为输出的时候，相邻两列之间需要有两个空格分隔，所以在计算总宽度的时候必须算上这些空格的宽度（Because two spaces are used between each pair of columns, the width they take up must be taken into consideration）
        if width_exceed_ask:
            print("单行数据字符串输出宽度超过当前终端窗口宽度！是否继续？（输入任意键继续，否则直接打印该数据框。）\nThe output width of each record string exceeds the current width of the terminal window! Continue? (Input anything to continue, or null to directly print this dataframe.)")
            log.write("单行数据字符串输出宽度超过当前终端窗口宽度！是否继续？（输入任意键继续，否则直接打印该数据框。）\nThe output width of each record string exceeds the current width of the terminal window! Continue? (Input anything to continue, or null to directly print this dataframe.)\n")
            cont = input()
            log.write(cont + "\n")
            if cont == "":
                #print(df)
                result = str(df)
                return (result, maxLens)
        elif direct_print:
            print("单行数据字符串输出宽度超过当前终端窗口宽度！将直接打印该数据框！\nThe output width of each record string exceeds the current width of the terminal window! The program is going to directly print this dataframe!")
            log.write("单行数据字符串输出宽度超过当前终端窗口宽度！将直接打印该数据框！\nThe output width of each record string exceeds the current width of the terminal window! The program is going to directly print this dataframe!\n")
            result = str(df)
            return (result, maxLens)
        else:
            print("单行数据字符串输出宽度超过当前终端窗口宽度！将继续格式化输出！\nThe output width of each record string exceeds the current width of the terminal window! The program is going on formatted printing!")
            log.write("单行数据字符串输出宽度超过当前终端窗口宽度！将继续格式化输出！\nThe output width of each record string exceeds the current width of the terminal window! The program is going on formatted printing!\n")
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

def getUrl(url: str, log):
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
                log.write("违反协议导致读取中断！正在尝试第%d次重新获取数据！\nEOF occurred in violation of protocol! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
            elif 'certificate verify failed' in str(ssl_error):
                print("SSL证书验证失败！正在尝试第%d次重新获取数据！\nSSL certificate verify failed! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
                log.write("SSL证书验证失败！正在尝试第%d次重新获取数据！\nSSL certificate verify failed! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
            elif 'Max retries exceeded with url' in str(ssl_error):
                print("请求数量超过限制！正在尝试第%d次重新获取数据！\nMax retries exceed with url! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
                log.write("请求数量超过限制！正在尝试第%d次重新获取数据！\nMax retries exceed with url! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        except requests.exceptions.ProxyError:
            if retry > 5:
                break
            print("无法连接到代理！正在尝试第%d次重新获取数据！\nCannot connect to proxy! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            log.write("无法连接到代理！正在尝试第%d次重新获取数据！\nCannot connect to proxy! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        except requests.exceptions.ChunkedEncodingError:
            if retry > 5:
                break
            print("接收数据块长度不正确导致连接中断！正在尝试第%d次重新获取数据！\nConnection broken: InvalidChunkLength. Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            log.write("接收数据块长度不正确导致连接中断！正在尝试第%d次重新获取数据！\nConnection broken: InvalidChunkLength. Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        except requests.exceptions.ConnectionError:
            if retry > 5:
                break
            print("由于远程服务器端无响应，连接已关闭！正在尝试第%d次重新获取数据！\nRemote end closed connection without response. Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            log.write("由于远程服务器端无响应，连接已关闭！正在尝试第%d次重新获取数据！\nRemote end closed connection without response. Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        except requests.exceptions.ReadTimeout:
            if retry > 5:
                break
            print("读取超时！正在尝试第%d次重新获取数据！\nRead time out! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            log.write("读取超时！正在尝试第%d次重新获取数据！\nRead time out! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        else:
            return (source, 0)
    if retry > 5:
        return (None, 1)

currentTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
os.makedirs("离线数据（Offline Data）/Update Logs", exist_ok = True)
log = open(f"离线数据（Offline Data）/Update Logs/{currentTime}.log", "w", encoding = "utf-8")
#控制只输出一遍的提示（Control the hint to be displayed only once）
task_continue_hint = True
ddragon_hint = True
line_re = re.compile('<tr><td class="link"><a href=".*" title=".*">.*</a></td><td class="size">.*</td><td class="date">.*</td></tr>')
while True:
    print("请选择要更新的数据资源，输入空字符串以退出程序：\nPlease select the data resource to update, or submit an empty string to exit the program:\n1\tCommunityDragon\n2\tDataDragon")
    log.write("请选择要更新的数据资源，输入空字符串以退出程序：\nPlease select the data resource to update, or submit an empty string to exit the program:\n1\tCommunityDragon\n2\tDataDragon\n")
    resource = input()
    log.write(resource + "\n")
    if resource == "":
        log.write("[The program has exited!]\n")
        log.close()
        break
    elif resource[0] == "1":
        print("请选择更新模式：\nPlease select the update mode:\n1\t全局扫描（Global Scanning）\n2\t按修改时间更新（Updating According to Modification Time）\n3\t按程序需求更新（Updating According to Program Demands）\n4\t更新指定文件夹（Updating Specified Folders）")
        log.write("请选择更新模式：\nPlease select the update mode:\n1\t全局扫描（Global Scanning）\n2\t按修改时间更新（Updating According to Modification Time）\n3\t按程序需求更新（Updating According to Program Demands）\n4\t更新指定文件夹（Updating Specified Folders）\n")
        mode = input()
        log.write(mode + "\n")
        if mode == "" or mode[0] == "2":
            mode = "2"
            print("请选择一种方式指定修改时间：\nPlease select a method of specifying the modification time:\n1\t自动获取（Automatically get）\n2\t手动输入（Manually input）")
            log.write("请选择一种方式指定修改时间：\nPlease select a method of specifying the modification time:\n1\t自动获取（Automatically get）\n2\t手动输入（Manually input）\n")
            time_get_method = input()
            log.write(time_get_method + "\n")
            if time_get_method != "" and time_get_method[0] == "2":
                time_get_method == "2"
                print('请以“年-月-日 时-分-秒”的格式输入修改时间。示例：2024-05-04 10-26-21。\nPlease input a modification time in the format "%Y-%m-%d %H-%M-%S". Example: 2024-05-04 10-26-21.')
                log.write('请以“年-月-日 时-分-秒”的格式输入修改时间。示例：2024-05-04 10-26-21。\nPlease input a modification time in the format "%Y-%m-%d %H-%M-%S". Example: 2024-05-04 10-26-21.\n')
                while True:
                    latest_mod_timestamp = input()
                    log.write(latest_mod_timestamp + "\n")
                    if latest_mod_timestamp == "":
                        continue
                    try: #允许输入整型或浮点型时间戳（A timestamp of integer or float type is allowed）
                        latest_mod_timestamp = eval(latest_mod_timestamp)
                        if isinstance(latest_mod_timestamp, (int, float)):
                            break
                    except:
                        try:
                            date_obj = datetime.strptime(latest_mod_timestamp, "%Y-%m-%d %H-%M-%S")
                        except ValueError:
                            print("您的输入格式有误！请重新输入。\nFormat not matched! Please try again.")
                            log.write("您的输入格式有误！请重新输入。\nFormat not matched! Please try again.\n")
                        else:
                            latest_mod_timestamp = date_obj.timestamp()
                            break
                latest_mod_date = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(latest_mod_timestamp))
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("指定修改时间（Specified modification time）：%s" %())
                log.write("指定修改时间（Specified modification time）：%s\n" %(latest_mod_date))
            else:
                time_get_method = "1"
        elif mode[0] == "3":
            mode = "3"
        elif mode[0] == "4":
            mode = "4"
        else:
            mode = "1"
        if mode == "3":
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            print("正在获取目前CommunityDragon数据库支持的语言……\nTrying to get the currently supported locales in CommunityDragon database ...")
            log.write("正在获取目前CommunityDragon数据库支持的语言……\nTrying to get the currently supported locales in CommunityDragon database ...\n")
            source, status = getUrl("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/", log)
            if status != 0:
                if status == 1:
                    print('正式服语言信息获取失败！请检查系统网络状况和代理设置。程序即将退出。\nLocales in the "latest" folder capture failure! Please check the system network condition and agent configuration. The program will exit now.')
                    log.write('正式服语言信息获取失败！请检查系统网络状况和代理设置。程序即将退出。\nLocales in the "latest" folder capture failure! Please check the system network condition and agent configuration. The program will exit now.\n')
                elif status == 404:
                    print('正式服语言信息获取失败！请检查以下链接的可用性。程序即将退出。\nLocales in the "latest" folder capture failure! Please check the URL availability. The program will exit now.\nhttps://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/')
                    log.write('正式服语言信息获取失败！请检查以下链接的可用性。程序即将退出。\nLocales in the "latest" folder capture failure! Please check the URL availability. The program will exit now.\nhttps://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/\n')
                log.close()
                time.sleep(3)
                exit()
            source = source.content.decode()
            source_list = list(map(lambda x: x.strip(), source.split("\n")))
            locales_latest = []
            for line in source_list:
                matchedLine = line_re.search(line)
                if matchedLine:
                    soup = BeautifulSoup(line, 'lxml')
                    name = soup.find("a")["href"]
                    locales_latest.append(name)
            source, status = getUrl("https://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/", log)
            if status != 0:
                if status == 1:
                    print('测试服语言信息获取失败！请检查系统网络状况和代理设置。程序即将退出。\nLocales in the "pbe" folder capture failure! Please check the system network condition and agent configuration. The program will exit now.')
                    log.write('测试服语言信息获取失败！请检查系统网络状况和代理设置。程序即将退出。\nLocales in the "pbe" folder capture failure! Please check the system network condition and agent configuration. The program will exit now.\n')
                elif status == 404:
                    print('测试服语言信息获取失败！请检查以下链接的可用性。程序即将退出。\nLocales in the "pbe" folder capture failure! Please check the URL availability. The program will exit now.\nhttps://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/')
                    log.write('测试服语言信息获取失败！请检查以下链接的可用性。程序即将退出。\nLocales in the "pbe" folder capture failure! Please check the URL availability. The program will exit now.\nhttps://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/\n')
                log.close()
                time.sleep(3)
                exit()
            source = source.content.decode()
            source_list = list(map(lambda x: x.strip(), source.split("\n")))
            locales_pbe = []
            for line in source_list:
                matchedLine = line_re.search(line)
                if matchedLine:
                    soup = BeautifulSoup(line, 'lxml')
                    name = soup.find("a")["href"]
                    locales_pbe.append(name)
            cdragon_folders = ["latest/cdragon/tft/"] + ["latest/plugins/rcp-be-lol-game-data/global/%sv1/" %locale for locale in locales_latest] + ["latest/plugins/rcp-be-lol-game-data/global/%sv1/champions/" %locale for locale in locales_latest] + ["pbe/cdragon/tft/"] + ["pbe/plugins/rcp-be-lol-game-data/global/%sv1/" %locale for locale in locales_pbe] + ["pbe/plugins/rcp-be-lol-game-data/global/%sv1/champions/" %locale for locale in locales_pbe] #由于urljoin函数的特性，所有文件夹类地址必须以斜杠结尾。下同（Due to the feature of `urljoin` function, all folder URLs must end with a slash. So do the following）
            cdragon_folders.sort()
        elif mode == "4":
            print("请选择输入方式：\nPlease choose an input method:\n1\t逐行输入（Line by line）\n2\t来自文件（From file）")
            log.write("请选择输入方式：\nPlease choose an input method:\n1\t逐行输入（Line by line）\n2\t来自文件（From file）\n")
            input_method = input()
            log.write(input_method + "\n")
            if input_method == "" or input_method[0] == "2":
                print('请输入一个存放CommunityDragon数据库文件夹地址的文本文档的位置：\nPlease input the path of a text file that contains URLs of folders in CommunityDragon database:')
                log.write('请输入一个存放CommunityDragon数据库文件夹地址的文本文档的位置：\nPlease input the path of a text file that contains URLs of folders in CommunityDragon database:\n')
                while True:
                    txtfile = input()
                    log.write(txtfile + "\n")
                    if txtfile == "":
                        continue
                    elif os.path.exists(txtfile):
                        break
                    else:
                        print("您输入的地址有误！请重新输入。\nERROR input of the text file path! Please try again.")
                        log.write("您输入的地址有误！请重新输入。\nERROR input of the text file path! Please try again.\n")
                with open(txtfile, "r", encoding = "utf-8") as fp:
                    cdragon_folders = list(set(map(lambda x: (x if x.endswith("/") else x[:-len(os.path.basename(x))]).strip("\n").replace("https://raw.communitydragon.org/", "").replace("离线数据（Offline Data）/cdragon/", ""), fp.readlines())))
                if "" in cdragon_folders:
                    cdragon_folders.remove("")
                cdragon_folders.sort()
            else:
                cdragon_folders = []
                print("请逐个输入要更新的CommunityDragon文件夹的地址，输入-1以退出循环：\nPlease input the URLs of CommunityDragon folders to update one by one. Enter -1 to exit the loop:")
                while True:
                    cdragon_folder = input()
                    log.write(cdragon_folder + "\n")
                    if cdragon_folder == "":
                        continue
                    elif cdragon_folder == "-1":
                        break
                    else:
                        cdragon_folder = cdragon_folder if cdragon_folder.endswith("/") else cdragon_folder[:-len(os.path.basename(cdragon_folder))]
                        cdragon_folders.append(cdragon_folder.replace("https://raw.communitydragon.org/", "").replace("离线数据（Offline Data）/cdragon/", "")) #请思考，这里如果换成`cdragon_folder.lstrip("https://raw.communitydragon.org/")`，会有什么效果？（Please figure out what will happen if the code is replaced by `cdragon_folder.lstrip("https://raw.communitydragon.org/")`）
                cdragon_folders = list(set(cdragon_folders))
                cdragon_folders.sort()
        else:
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            print("正在读取正式服在线索引……\nReading the online index file of live data resources...")
            log.write("正在读取正式服在线索引……\nReading the online index file of live data resources...\n")
            source, status = getUrl("https://raw.communitydragon.org/latest/cdragon/files.exported.txt", log)
            if status != 0:
                if status == 1:
                    print("获取索引失败！请检查系统网络状况和代理设置。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.")
                    log.write("获取索引失败！请检查系统网络状况和代理设置。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\n")
                elif status == 404:
                    print("获取索引失败！请检查以下链接的可用性。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\nhttps://raw.communitydragon.org/latest/cdragon/files.exported.txt")
                    log.write("获取索引失败！请检查以下链接的可用性。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\nhttps://raw.communitydragon.org/latest/cdragon/files.exported.txt\n")
                log.close()
                time.sleep(3)
                exit()
            files_exported_latest = source.text.strip("\n").split("\n")
            #files_exported_latest = requests.get("https://raw.communitydragon.org/latest/cdragon/files.exported.txt").text.strip("\n").split("\n")
            text_files_exported_latest = [file for file in files_exported_latest if file.endswith((".json", ".txt", ".js", ".yaml"))]
            text_folders_exported_latest = list(set(list(map(lambda x: "/".join(x.split("/")[:-1]) + "/" if "/" in x else "", text_files_exported_latest))))
            text_folders_exported_latest.sort()
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            print("正在读取美测服在线索引……\nReading the online index file of pbe data resources...")
            log.write("正在读取美测服在线索引……\nReading the online index file of pbe data resources...\n")
            source, status = getUrl("https://raw.communitydragon.org/pbe/cdragon/files.exported.txt", log)
            if status != 0:
                if status == 1:
                    print("获取索引失败！请检查系统网络状况和代理设置。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.")
                    log.write("获取索引失败！请检查系统网络状况和代理设置。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\n")
                elif status == 404:
                    print("获取索引失败！请检查以下链接的可用性。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\nhttps://raw.communitydragon.org/pbe/cdragon/files.exported.txt")
                    log.write("获取索引失败！请检查以下链接的可用性。程序即将退出。\nIndex capture failure! Please check the system network condition and agent configuration. The program will exit now.\nhttps://raw.communitydragon.org/pbe/cdragon/files.exported.txt\n")
                log.close()
                time.sleep(3)
                exit()
            files_exported_pbe = source.text.strip("\n").split("\n")
            #files_exported_pbe = requests.get("https://raw.communitydragon.org/pbe/cdragon/files.exported.txt").text.strip("\n").split("\n")
            text_files_exported_pbe = [file for file in files_exported_pbe if file.endswith((".json", ".txt", ".js", ".yaml"))]
            text_folders_exported_pbe = list(set(list(map(lambda x: "/".join(x.split("/")[:-1]) + "/" if "/" in x else "", text_files_exported_pbe))))
            text_folders_exported_pbe.sort()
            cdragon_folders =  ["latest/cdragon/arena/", "latest/cdragon/tft/"] + list(map(lambda x: "latest/" + x, text_folders_exported_latest)) + ["pbe/cdragon/arena/", "pbe/cdragon/tft/"] + list(map(lambda x: "pbe/" + x, text_folders_exported_pbe)) #索引文件中不包含cdragon文件夹内的文件，因此这里需要单独添加到文件夹列表中（The index file doesn't contain files in cdragon folder, so they should be added to the folder list specially）
            complete_scan = True
            if task_continue_hint:
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("如果您之前有文件夹未检查，那么请在这里输入本次检查的文件夹的索引下界和上界。输入空字符串以检查所有文件夹。\nIf there're some folders unchecked before, please enter the lower and upper limit of the index of the folders to be checked this time. Submit an empty string to check all folders.\n提示：如果想要包含最后一个文件夹，请将上界指定为大于当前文件夹列表长度的任意一个正整数。\nHint: If you expect the program not to neglect the last folder, please specify the upper limit as any integer greater than the length of the current folder list.\n文件夹总个数（Total number of folders）：%d" %len(cdragon_folders))
                log.write("如果您之前有文件夹未检查，那么请在这里输入本次检查的文件夹的索引下界和上界。输入空字符串以检查所有文件夹。\nIf there're some folders unchecked before, please enter the lower and upper limit of the index of the folders to be checked this time. Submit an empty string to check all folders.\n提示：如果想要包含最后一个文件夹，请将上界指定为大于当前文件夹列表长度的任意一个正整数。\nHint: If you expect the program not to neglect the last folder, please specify the upper limit as any integer greater than the length of the current folder list.\n文件夹总个数（Total number of folders）：%d\n" %len(cdragon_folders))
                task_continue_hint = False
            else:
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("如果您之前有文件夹未检查，那么请在这里输入本次检查的文件夹的索引下界和上界。输入空字符串以检查所有文件夹。\nIf there're some folders unchecked before, please enter the lower and upper limit of the index of the folders to be checked this time. Submit an empty string to check all folders.\n文件夹总个数（Total number of folders）：%d" %len(cdragon_folders))
                log.write("如果您之前有文件夹未检查，那么请在这里输入本次检查的文件夹的索引下界和上界。输入空字符串以检查所有文件夹。\nIf there're some folders unchecked before, please enter the lower and upper limit of the index of the folders to be checked this time. Submit an empty string to check all folders.\n文件夹总个数（Total number of folders）：%d\n" %len(cdragon_folders))
            while True:
                contCheck = input()
                log.write(contCheck + "\n")
                if contCheck == "":
                    break
                else:
                    try:
                        begin, end = map(int, contCheck.split())
                    except ValueError:
                        print("请以空格为分隔符输入文件夹列表的整数类型的下界和上界！\nPlease enter two integers as the begIndex and endIndex of the folder list split by space!")
                        log.write("请以空格为分隔符输入文件夹列表的整数类型的下界和上界！\nPlease enter two integers as the begIndex and endIndex of the folder list split by space!\n")
                    else:
                        cdragon_folders = cdragon_folders[begin:end]
                        complete_scan = False
                        break
        web_prefix = "https://raw.communitydragon.org/"
        local_prefix = "离线数据（Offline Data）/cdragon"
        updated_files = []
        added_files = []
        error_folders = []
        error_files = []
        folders_to_delete = [] #统计本地存在而数据库不存在的文件夹（Summarize the folders that exist locally but don't exist in the database）
        files_to_delete = [] #统计本地存在而数据库不存在的文件（Summarize the files that exist locally but don't exist in the database）
        for root, dirs, files in os.walk(local_prefix):
            if not root in folders_to_delete and files != []: #请仔细体会后半个条件的作用（Please try to udnerstand the role of the latter condition）
                folders_to_delete.append(root.replace("\\", "/") + "/")
            files_to_delete += list(map(lambda x: os.path.join(root, x).replace("\\", "/"), files))
        cnt1 = 0
        for folder in cdragon_folders:
            cnt1 += 1
            cnt2 = 0
            url = urljoin(web_prefix, folder)
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            print("[%d/%d]正在检查文件夹（Checking the folder）：%s" %(cnt1, len(cdragon_folders), url))
            log.write("[%d/%d]正在检查文件夹（Checking the folder）：%s\n" %(cnt1, len(cdragon_folders), url))
            table = {"file": [], "size": [], "web_date": [], "web_timestamp": [], "local_date": [], "local_timestamp": []}
            source, status = getUrl(url, log)
            if status != 0:
                if status == 1:
                    print("文件夹%s信息获取失败！请等待程序结束后手动比对。\nFolder %s information check failed! Please check manually after the program execution finishes." %(url, url))
                    log.write("文件夹%s信息获取失败！请等待程序结束后手动比对。\nFolder %s information check failed! Please check manually after the program execution finishes.\n" %(url, url))
                    error_folders.append(url)
                    if os.path.join(local_prefix, folder).replace("\\", "/") in folders_to_delete:
                        folders_to_delete.remove(os.path.join(local_prefix, folder).replace("\\", "/"))
                elif status == 404:
                    print("文件夹%s不存在！\nFolder %s not found!" %(url, url))
                    log.write("文件夹%s不存在！\nFolder %s not found!\n" %(url, url))
                continue
            if os.path.join(local_prefix, folder).replace("\\", "/") in folders_to_delete:
                folders_to_delete.remove(os.path.join(local_prefix, folder).replace("\\", "/"))
            source = source.content.decode()
            source_list = list(map(lambda x: x.strip(), source.split("\n")))
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            if mode == "1":
                print("页面文件列表如下：\nFile list is as follows:\n网页链接（URL)： %s" %url)
                log.write("页面文件列表如下：\nFile list is as follows:\n网页链接（URL)： %s\n" %url)
            elif mode == "2":
                if time_get_method == "1":
                    print("页面新文件列表如下：\nNew file list is as follows:\n网页链接（URL)： %s" %url)
                    log.write("页面新文件列表如下：\nNew file list is as follows:\n网页链接（URL)： %s\n" %url)
                elif time_get_method == "2":
                    print("指定修改时间（%s）后的页面文件列表如下：\nFile list after the specified modification time (%s) is as follows:\n网页链接（URL)： %s" %(latest_mod_date, latest_mod_date, url))
                    log.write("指定修改时间（%s）后的页面文件列表如下：\nFile list after the specified modification time (%s) is as follows:\n网页链接（URL)： %s\n" %(latest_mod_date, latest_mod_date, url))
            elif mode == "3":
                print("本程序集涉及的新文件列表如下：\nNew file list involved in this program set is as follows:\n网页链接（URL)： %s" %url)
                log.write("本程序集涉及的新文件列表如下：\nNew file list involved in this program set is as follows:\n网页链接（URL)： %s\n" %url)
            elif mode == "4":
                print("指定文件夹涉及的新文件列表如下：\nNew file list in specified folders is as follows:\n网页链接（URL)： %s" %url)
                log.write("指定文件夹涉及的新文件列表如下：\nNew file list involved in specified folders is as follows:\n网页链接（URL)： %s\n" %url)
            for line in source_list:
                matchedLine = line_re.search(line)
                if matchedLine:
                    soup = BeautifulSoup(line, 'lxml')
                    name = soup.find("a")["href"]
                    size = soup.find("td", class_ = "size").text
                    web_date = soup.find("td", class_ = "date").text
                    web_date_obj = datetime.strptime(web_date, "%Y-%b-%d %H:%M")
                    web_timestamp = web_date_obj.timestamp()
                    local_timestamp = os.path.getmtime(os.path.join(local_prefix, folder, name)) if os.path.exists(os.path.join(local_prefix, folder)) and name in os.listdir(os.path.join(local_prefix, folder)) else 0
                    local_date = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(local_timestamp))
                    if name.endswith((".json", ".txt", ".js", ".yaml")):
                        if mode == "2" and time_get_method == "1" and web_timestamp + time.localtime().tm_gmtoff < local_timestamp or mode == "2" and time_get_method == "2" and web_timestamp + time.localtime().tm_gmtoff < latest_mod_timestamp or mode == "3" and web_timestamp + time.localtime().tm_gmtoff < local_timestamp or mode == "3" and folder.endswith("v1/") and not name in ["champion-summary.json", "cherry-augments.json", "companions.json", "items.json", "perks.json", "perkstyles.json", "skins.json", "statstones.json", "summoner-emotes.json", "summoner-icons.json", "summoner-spells.json", "tftchampions.json", "tftdamageskins.json", "tftitems.json", "tftmapskins.json", "tfttraits.json", "ward-skins.json"] or mode == "4" and web_timestamp + time.localtime().tm_gmtoff < local_timestamp:
                        #if mode == "2" and time_get_method == "1" and web_timestamp + time.localtime().tm_gmtoff < local_timestamp or mode == "2" and time_get_method == "2" and web_timestamp + time.localtime().tm_gmtoff < latest_mod_timestamp or mode == "3" and web_timestamp + time.localtime().tm_gmtoff < local_timestamp or mode == "3" and folder.endswith("v1/") and not name in ["champion-summary.json", "cherry-augments.json", "companions.json", "items.json", "perks.json", "perkstyles.json", "skins.json", "statstones.json", "summoner-emotes.json", "summoner-icons.json", "summoner-spells.json", "tftchampions.json", "tftdamageskins.json", "tftitems.json", "tftmapskins.json", "tfttraits.json", "ward-skins.json"] or mode == "4" and web_timestamp + time.localtime().tm_gmtoff < local_timestamp or mode == "4" and folder.endswith("v1/") and not name in ["champion-summary.json", "cherry-augments.json", "companions.json", "items.json", "perks.json", "perkstyles.json", "skins.json", "statstones.json", "summoner-emotes.json", "summoner-icons.json", "summoner-spells.json", "tftchampions.json", "tftdamageskins.json", "tftitems.json", "tftmapskins.json", "tfttraits.json", "ward-skins.json"]: #仅供发行版使用（Only for release）
                            continue
                        table["file"].append(name)
                        table["size"].append(size)
                        table["web_date"].append(web_date)
                        table["web_timestamp"].append(web_timestamp)
                        table["local_date"].append(local_date)
                        table["local_timestamp"].append(local_timestamp)
            table = pd.DataFrame(table)
            if table.empty:
                print(table)
                log.write(str(table) + "\n")
            else:
                print(format_df(table, log, False, True)[0])
                log.write(format_df(table, log, False, True)[0] + "\n")
            dir = os.path.join(local_prefix, folder).replace("\\", "/")
            os.makedirs(dir, exist_ok = True)
            for i in range(len(table)):
                cnt2 += 1
                name = table["file"][i]
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("[%d/%d][%d/%d]正在校对文件（Checking file）： %s" %(cnt1, len(cdragon_folders), cnt2, len(table), urljoin(url, name)))
                log.write("[%d/%d][%d/%d]正在校对文件（Checking file）： %s\n" %(cnt1, len(cdragon_folders), cnt2, len(table), urljoin(url, name)))
                update = added = False
                src, status = getUrl(urljoin(url, name), log)
                if status != 0:
                    if status == 1:
                        print("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes." %(urljoin(url, name), urljoin(url, name)))
                        log.write("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes.\n" %(urljoin(url, name), urljoin(url, name)))
                        error_files.append(urljoin(url, name))
                    elif status == 404:
                        print("文件%s不存在！\nFile %s not found!" %(urljoin(url, name), urljoin(url, name)))
                        log.write("文件%s不存在！\nFile %s not found!\n" %(urljoin(url, name), urljoin(url, name)))
                    continue
                if os.path.join(local_prefix, folder, name).replace("\\", "/") in files_to_delete:
                    files_to_delete.remove(os.path.join(local_prefix, folder, name).replace("\\", "/"))
                try:
                    src = src.json() if name.endswith(".json") else src.text.replace("\r", "")
                except json.decoder.JSONDecodeError as e:
                    if "Unexpected UTF-8 BOM (decode using utf-8-sig)" in str(e): #解决方案来自Stack Overflow（The solution comes from https://stackoverflow.com/questions/71025396/asyncio-and-get-unexpected-utf-8-bom）
                        print("文件编码格式错误！正在尝试改用utf-8-sig编码……\nFile decode error! Trying decoding by utf-8-sig ...")
                        log.write("文件编码格式错误！正在尝试改用utf-8-sig编码……\nFile decode error! Trying decoding by utf-8-sig ...\n")
                        src = json.loads(src.text.encode().decode("utf-8-sig"))
                if not name in os.listdir(dir):
                    update = added = True
                else:
                    with open(os.path.join(dir, name), "r", encoding = "utf-8") as fp:
                        dst = json.load(fp) if name.endswith(".json") else fp.read()
                    if src != dst:
                        update = True
                if mode == "1" and update or mode != "1": #当选择全局扫描时，只更新有变化的文档；当选择根据修改时间更新时，如果网页修改时间超前，那么无论文件内容是否发生变化，都重新保存一次，便于后续按照修改时间更新（When the user selects Global Scan, the program updates the changed files. When the user selects Updating according to modification time, if the web modification time of a file succeeds to the local midification time of that, then save the web content to local, no matter whether the web file is same as the local file in terms of content）
                    with open(os.path.join(dir, name), "w", encoding = "utf-8") as fp:
                        if name.endswith(".json"):
                            json.dump(src, fp, indent = 4, ensure_ascii = False)
                        else:
                            fp.write(src)
                if update:
                    if added:
                        print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                        log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                        print("已添加文件（Added file）：%s" %(os.path.join(dir, name)))
                        log.write("已添加文件（Added file）：%s\n" %(os.path.join(dir, name)))
                        added_files.append(urljoin(url, name))
                    else:
                        print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                        log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                        print("已更新文件（Updated file）：%s" %(os.path.join(dir, name)))
                        log.write("已更新文件（Updated file）：%s\n" %(os.path.join(dir, name)))
                        updated_files.append(urljoin(url, name))
        if updated_files:
            print("已更新以下%d个文件：\nUpdated the following %d file(s):" %(len(updated_files), len(updated_files)))
            log.write("已更新以下%d个文件：\nUpdated the following %d file(s):\n" %(len(updated_files), len(updated_files)))
            for file in updated_files:
                print(file)
                log.write(file + "\n")
            print()
            log.write("\n")
        if added_files:
            print("已添加以下%d个文件：\nAdded the following %d file(s):" %(len(added_files), len(added_files)))
            log.write("已添加以下%d个文件：\nAdded the following %d file(s):\n" %(len(added_files), len(added_files)))
            for file in added_files:
                print(file)
                log.write(file + "\n")
            print()
            log.write("\n")
        if error_folders:
            print("以下%d个文件夹比对失败。请重新比对！\nThe following %d folder(s) fail to be checked. Please check manually!" %(len(error_folders), len(error_folders)))
            log.write("以下%d个文件夹比对失败。请重新比对！\nThe following %d folder(s) fail to be checked. Please check manually!\n" %(len(error_folders), len(error_folders)))
            for folder in error_folders:
                print(folder)
                log.write(folder + "\n")
            print()
            log.write("\n")
        if error_files:
            print("以下%d个文件比对失败。请重新比对！\nThe following %d file(s) fail to be checked. Please check manually!" %(len(error_files), len(error_files)))
            log.write("以下%d个文件比对失败。请重新比对！\nThe following %d file(s) fail to be checked. Please check manually!\n" %(len(error_files), len(error_files)))
            for file in error_files:
                print(file)
                log.write(file + "\n")
            print()
            log.write("\n")
        if mode == "1" and complete_scan and files_to_delete: #只有全局扫描才可以决定删除哪些文件（Only by Global Scan can the program decide which files to delete）
            print("以下%d个文件不存在于数据库中。是否永久删除这些文件？（输入任意非空字符串删除，否则不删除）\nThe following %d file(s) don't exist in the database. Do you want to delete them? (Submit any non-empty string to delete, or null to refuse deleting the files)\n" %(len(files_to_delete), len(files_to_delete)) + "\n".join(files_to_delete))
            log.write("以下%d个文件不存在于数据库中。是否永久删除这些文件？（输入任意非空字符串删除，否则不删除）\nThe following %d file(s) don't exist in the database. Do you want to delete them? (Submit any non-empty string to delete, or null to refuse deleting the files)\n" %(len(files_to_delete), len(files_to_delete)) + "\n".join(files_to_delete) + "\n")
            delete = input()
            log.write(delete + "\n")
            if delete != "":
                for file in files_to_delete:
                    try:
                        os.remove(file)
                    except FileNotFoundError:
                        pass
            print()
            log.write("\n")
        if (mode == "1" or mode == "2") and complete_scan and folders_to_delete:
            print("以下%d个文件夹不存在于数据库中。是否永久删除这些文件夹？（输入任意非空字符串删除，否则不删除）\nThe following %d folder(s) don't exist in the database. Do you want to delete them? (Submit any non-empty string to delete, or null to refuse deleting the folders)\n" %(len(folders_to_delete), len(folders_to_delete)) + "\n".join(folders_to_delete))
            log.write("以下%d个文件夹不存在于数据库中。是否永久删除这些文件夹？（输入任意非空字符串删除，否则不删除）\nThe following %d folder(s) don't exist in the database. Do you want to delete them? (Submit any non-empty string to delete, or null to refuse deleting the folders)\n" %(len(folders_to_delete), len(folders_to_delete)) + "\n".join(folders_to_delete) + "\n")
            delete = input()
            log.write(delete + "\n")
            if delete != "":
                for folder in folders_to_delete:
                    try:
                        shutil.rmtree(folder)
                    except FileNotFoundError: #部分文件夹可能在上一步中已被删除（Some folders may have been deleted in the last step）
                        pass
            print()
            log.write("\n")
    elif resource[0] == "2":
        print("请选择更新模式：\nPlease select the update mode:\n1\t全局比对（Global Compare）\n2\t按程序需求更新（Updating According to Program Demands）")
        log.write("请选择更新模式：\nPlease select the update mode:\n1\t全局比对（Global Compare）\n2\t按程序需求更新（Updating According to Program Demands）\n")
        mode = input()
        log.write(mode + "\n")
        if mode == "" or mode[0] == "1":
            mode = "1"
        else:
            mode = "2"
        if ddragon_hint:
            hint = '请按以下步骤操作：\nPlease follow these steps:\n1. 访问网址https://developer.riotgames.com/docs/lol#data-dragon\n   Visit the website: https://developer.riotgames.com/docs/lol#data-dragon\n2. 在Latest中找到正式服最新版本数据资源压缩包下载链接。例如：https://ddragon.leagueoflegends.com/cdn/dragontail-14.18.1.tgz\n   Find the link to download the compressed tarball of the latest data resource for live servers. For example: https://ddragon.leagueoflegends.com/cdn/dragontail-14.18.1.tgz\n3. 下载。这需要花费一些时间。\n   Download the file. It may take some time.\n4. 将下载好的tgz文件直接“解压至此”。\n   "Extract here" for the tgz file.\n5. 将解压出来的压缩包再次解压到选定文件夹下与压缩包同名的文件夹。示例：将“dragontail-14.18.1.tar”解压到“D:/360AI浏览器下载/dragontail-14.18.1”文件夹下。\nExtract to "Archive-Name" folder under the selected folder for the extracted tar file. For example, extract "dragontail-14.18.1.tar" into the folder "D:/Downloads/dragontail-14.18.1".\n接下来，请给出数据资源的位置。（按照上例应为“D:/360AI浏览器下载/dragontail-14.18.1/14.18.1/data”。）\nNext, please provide the directory that stores the data resources. (By the above example, the directory should be "D:/Downloads/dragontail-14.18.1/14.18.1/data".)'
            print(hint)
            log.write(hint + "\n")
            ddragon_hint = False
        else:
            print("请给出数据资源的位置。\nPlease provide the directory that stores the data resources.")
            log.write("请给出数据资源的位置。\nPlease provide the directory that stores the data resources.\n")
        dst_folder = "离线数据（Offline Data）/ddragon"
        while True:
            src_folder = input()
            log.write(src_folder + "\n")
            try:
                if not ("en_US" in os.listdir(src_folder) and "zh_CN" in os.listdir(src_folder)):
                    print("您输入的地址有误！请重新输入！\nERROR input of data resource directory! Please try again!")
                    log.write("您输入的地址有误！请重新输入！\nERROR input of data resource directory! Please try again!\n")
                else:
                    break
            except FileNotFoundError:
                print("您输入的地址有误！请重新输入！\nERROR input of data resource directory! Please try again!")
                log.write("您输入的地址有误！请重新输入！\nERROR input of data resource directory! Please try again!\n")
        added_files = []
        updated_files = []
        error_files = []
        cnt1 = 0
        for root, dirs, files in os.walk(src_folder):
            for file in files:
                update = added = False
                if mode == "1" and file.endswith(".json") or mode == "2" and file == "champion.json":
                    src_path = os.path.join(root, file).replace("\\", "/")
                    relative_path = os.path.relpath(root, src_folder).replace("\\", "/")
                    dst_path = os.path.join(dst_folder, relative_path, file).replace("\\", "/")
                    if "en_US" in relative_path or "zh_CN" in relative_path:
                        cnt1 += 1
                        os.makedirs(os.path.dirname(dst_path), exist_ok = True)
                        print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                        log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                        print("[%d]正在校对文件（Checking file）： %s" %(cnt1, src_path))
                        log.write("[%d]正在校对文件（Checking file）： %s\n" %(cnt1, src_path))
                        with open(src_path, "r", encoding = "utf-8") as fp:
                            src = json.load(fp)
                        if not file in os.listdir(os.path.join(dst_folder, relative_path)):
                            update = added = True
                        else:
                            with open(dst_path, "r", encoding = "utf-8") as fp:
                                dst = json.load(fp)
                            if src != dst:
                                update = True
                        if update:
                            with open(dst_path, "w", encoding = "utf-8") as fp:
                                json.dump(src, fp, indent = 4, ensure_ascii = False)
                            if added:
                                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                                print("[%d]已添加文件（Added file）：%s" %(cnt1, dst_path))
                                log.write("[%d]已添加文件（Added file）：%s\n" %(cnt1, dst_path))
                                added_files.append(src_path)
                            else:
                                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                                print("[%d]已更新文件（Updated file）：%s" %(cnt1, dst_path))
                                log.write("[%d]已更新文件（Updated file）：%s\n" %(cnt1, dst_path))
                                updated_files.append(src_path)
        cnt1 += 1
        version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
        log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
        print("[%d]正在校对文件（Checking file）： %s" %(cnt1, version_url))
        log.write("[%d]正在校对文件（Checking file）： %s\n" %(cnt1, version_url))
        update = added = False
        src, status = getUrl(version_url, log)
        if status != 0:
            if status == 1:
                print("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes." %(version_url, version_url))
                log.write("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes.\n" %(version_url, version_url))
            elif status == 404:
                print("文件%s不存在！请等待程序结束后手动比对。\nFile %s not found! Please check manually after the program execution finishes." %(version_url, version_url))
                log.write("文件%s不存在！请等待程序结束后手动比对。\nFile %s not found! Please check manually after the program execution finishes.\n" %(version_url, version_url))
            error_files.append(version_url)
            continue
        src = src.json()
        if not "versions.json" in os.listdir("离线数据（Offline Data）"):
            update = added = True
        else:
            with open("离线数据（Offline Data）/versions.json", "r", encoding = "utf-8") as fp:
                dst = json.load(fp)
            if src != dst:
                update = True
        if update:
            with open("离线数据（Offline Data）/versions.json", "w", encoding = "utf-8") as fp:
                json.dump(src, fp, indent = 4, ensure_ascii = False)
            if added:
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("[%d]已添加文件（Added file）：离线数据（Offline Data）/versions.json" %cnt1)
                log.write("[%d]已添加文件（Added file）：离线数据（Offline Data）/versions.json\n" %cnt1)
                added_files.append("离线数据（Offline Data）/versions.json")
            else:
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("[%d]已更新文件（Updated file）：离线数据（Offline Data）/versions.json" %cnt1)
                log.write("[%d]已更新文件（Updated file）：离线数据（Offline Data）/versions.json\n" %cnt1)
                updated_files.append("离线数据（Offline Data）/versions.json")
    else:
        print("您的输入有误！请重新输入。\nERROR input! Please try again.")
        log.write("您的输入有误！请重新输入。\nERROR input! Please try again.\n")
print("比对完成！请按回车键退出。\nCheck finished! Press Enter to exit.")
input()