import json, os, re, requests, shutil, time, unicodedata
import pandas as pd
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from wcwidth import wcswidth

def count_nonASCII(s: str): #统计一个字符串中占用命令行2个宽度单位的字符个数（Count the number of characters that take up 2 width unit in CMD）
    return sum([unicodedata.east_asian_width(character) in ("F", "W") for character in list(str(s))])

def format_df(df: pd.DataFrame): #按照每列最长字符串的命令行宽度加上2，再根据每个数据的中文字符数量决定最终格式化输出的字符串宽度（Get the width of the longest string of each column, add it by 2, and substract it by the number of each cell string's Chinese characters to get the final width for each cell to print using `format` function）
    df = df.reset_index(drop = True) #这一步至关重要，因为下面的操作前提是行号是默认的（This step is crucial, for the following operations are based on the dataframe with the default row index）
    maxLens = {}
    maxWidth = shutil.get_terminal_size()[0]
    fields = df.columns.tolist()
    for field in fields:
        maxLens[field] = max(max(map(lambda x: wcswidth(str(x)), df[field])), wcswidth(str(field))) + 2
    if sum(maxLens.values()) + 2 * (len(fields) - 1) > maxWidth: #因为输出的时候，相邻两列之间需要有两个空格分隔，所以在计算总宽度的时候必须算上这些空格的宽度（Because two spaces are used between each pair of columns, the width they take up must be taken into consideration）
        print("单行数据字符串输出宽度超过当前终端窗口宽度！是否继续？（输入任意键继续，否则直接打印该数据框。）\nThe output width of each record string exceeds the current width of the terminal window! Continue? (Input anything to continue, or null to directly print this dataframe.)")
        if input() == "":
            #print(df)
            result = str(df)
            return (result, maxLens)
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
    while retry <= 5:
        try:
            source = requests.get(url)
            source.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            retry += 1
            if http_err.response.status_code == 404:
                print("文件不存在！正在尝试第%d次重新获取数据！\nFile not found! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
                log.write("文件不存在！正在尝试第%d次重新获取数据！\nFile not found! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        except requests.exceptions.SSLError as ssl_error:
            retry += 1
            if "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol" in str(ssl_error):
                print("违反协议导致读取中断！正在尝试第%d次重新获取数据！\nEOF occurred in violation of protocol! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
                log.write("违反协议导致读取中断！正在尝试第%d次重新获取数据！\nEOF occurred in violation of protocol! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
            elif 'certificate verify failed' in str(ssl_error):
                print("SSL证书验证失败！正在尝试第%d次重新获取数据！\nSSL certificate verify failed! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
                log.write("SSL证书验证失败！正在尝试第%d次重新获取数据！\nSSL certificate verify failed! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        except requests.exceptions.ProxyError:
            retry += 1
            print("无法连接到代理！正在尝试第%d次重新获取数据！\nCannot connect to proxy! Trying to recapture the data with url: %s. Time(s) tried: %d" %(retry, url, retry))
            log.write("无法连接到代理！正在尝试第%d次重新获取数据！\nCannot connect to proxy! Trying to recapture the data with url: %s. Time(s) tried: %d\n" %(retry, url, retry))
        else:
            return (source, True)
    if retry > 5:
        return (None, False)

currentTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
os.makedirs("离线数据（Offline Data）/Update Logs", exist_ok = True)
log = open(f"离线数据（Offline Data）/Update Logs/{currentTime}.log", "w", encoding = "utf-8")
ddragon_hint = True
while True:
    print("请选择要更新的数据资源，输入空字符串以退出程序：\nPlease select the data resource to update, or submit an empty string to exit the program:\n1\tCommunityDragon\n2\tDataDragon")
    log.write("请选择要更新的数据资源，输入空字符串以退出程序：\nPlease select the data resource to update, or submit an empty string to exit the program:\n1\tCommunityDragon\n2\tDataDragon\n")
    resource = input()
    log.write(resource + "\n")
    if resource == "":
        log.close()
        break
    elif resource[0] == "1":
        print("请选择更新模式：\nPlease select the update mode:\n1\t全局扫描（Global Scanning）\n2\t按修改时间更新（Updating According to Modification Time）")
        log.write("请选择更新模式：\nPlease select the update mode:\n1\t全局扫描（Global Scanning）\n2\t按修改时间更新（Updating According to Modification Time）\n")
        mode = input()
        log.write(mode + "\n")
        if mode == "" or mode[0] != "1":
            mode = "2"
            print("请选择一种方式指定修改时间：\nPlease select a method of specifying the modification time:\n1\t自动获取（Automatically get）\n2\t手动输入（Manually input）")
            log.write("请选择一种方式指定修改时间：\nPlease select a method of specifying the modification time:\n1\t自动获取（Automatically get）\n2\t手动输入（Manually input）\n")
            time_get_method = input()
            log.write(time_get_method + "\n")
            if time_get_method != "" and time_get_method[0] == "2":
                print('请以“年-月-日 时-分-秒”的格式输入修改时间。示例：2024-05-04 10-26-21。\nPlease input a modification time in the format "%Y-%m-%d %H-%M-%S". Example: 2024-05-04 10-26-21.')
                log.write('请以“年-月-日 时-分-秒”的格式输入修改时间。示例：2024-05-04 10-26-21。\nPlease input a modification time in the format "%Y-%m-%d %H-%M-%S". Example: 2024-05-04 10-26-21.\n')
                while True:
                    latest_mod_time = input()
                    log.write(latest_mod_time + "\n")
                    if latest_mod_time == "":
                        continue
                    try: #允许输入整型或浮点型时间戳（A timestamp of integer or float type is allowed）
                        latest_mod_time = eval(latest_mod_time)
                        if isinstance(latest_mod_time, (int, float)):
                            break
                    except:
                        try:
                            date_obj = datetime.strptime(latest_mod_time, "%Y-%m-%d %H-%M-%S")
                        except ValueError:
                            print("您的输入格式有误！请重新输入。\nFormat not matched! Please try again.")
                            log.write("您的输入格式有误！请重新输入。\nFormat not matched! Please try again.\n")
                        else:
                            latest_mod_time = date_obj.timestamp()
                            break
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("指定修改时间（Specified modification time）：%s" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(latest_mod_time))))
                log.write("指定修改时间（Specified modification time）：%s\n" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(latest_mod_time))))
            else:
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("正在遍历离线数据资源以获取最新修改时间……\nTraversing the offline data resource files to get the latest modification time ...")
                log.write("正在遍历离线数据资源以获取最新修改时间……\nTraversing the offline data resource files to get the latest modification time ...\n")
                latest_mod_time = 0
                for root, dirs, files in os.walk("离线数据（Offline Data）"):
                    for file in files:
                        if "Update Logs" in root or file == "自动更新离线数据.py": #统计修改时间，不能算上刚刚生成的日志文件和本脚本（When summarizing the modification time, the log that has just been created should be taken into account）
                            continue
                        file_path = os.path.join(root, file)
                        mod_time = os.path.getmtime(file_path)
                        latest_mod_time = mod_time if mod_time > latest_mod_time else latest_mod_time
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("最新修改时间（Latest modification time）：%s" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(latest_mod_time))))
                log.write("最新修改时间（Latest modification time）：%s\n" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(latest_mod_time))))
        else:
            mode = "1"
        cdragon_folders = ["latest/cdragon/arena/", "latest/cdragon/tft/", "latest/plugins/rcp-be-lol-game-data/global/default/v1/champions/", "latest/plugins/rcp-be-lol-game-data/global/default/v1/map-assets/", "latest/plugins/rcp-be-lol-game-data/global/default/v1/", "latest/plugins/rcp-be-lol-game-data/global/zh_cn/v1/champions/", "latest/plugins/rcp-be-lol-game-data/global/zh_cn/v1/map-assets/", "latest/plugins/rcp-be-lol-game-data/global/zh_cn/v1/", "pbe/cdragon/arena/", "pbe/cdragon/tft/", "pbe/plugins/rcp-be-lol-game-data/global/default/v1/champions/", "pbe/plugins/rcp-be-lol-game-data/global/default/v1/map-assets/", "pbe/plugins/rcp-be-lol-game-data/global/default/v1/", "pbe/plugins/rcp-be-lol-game-data/global/zh_cn/v1/champions/", "pbe/plugins/rcp-be-lol-game-data/global/zh_cn/v1/map-assets/", "pbe/plugins/rcp-be-lol-game-data/global/zh_cn/v1/"]
        web_prefix = "https://raw.communitydragon.org/"
        local_prefix = "离线数据（Offline Data）/cdragon"
        updated_files = []
        added_files = []
        error_files = []
        cnt1 = 0
        for folder in cdragon_folders:
            cnt1 += 1
            cnt2 = 0
            url = urljoin(web_prefix, folder)
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            print("[%d/%d]正在检查文件夹（Checking the folder）：%s" %(cnt1, len(cdragon_folders), url))
            log.write("[%d/%d]正在检查文件夹（Checking the folder）：%s\n" %(cnt1, len(cdragon_folders), url))
            line_re = re.compile('<tr><td class="link"><a href=".*" title=".*">.*</a></td><td class="size">.*</td><td class="date">.*</td></tr>')
            table = {"file": [], "size": [], "date": [], "timestamp": []}
            retry = 0
            source, status = getUrl(url, log)
            if not status:
                print("文件夹%s信息获取失败！请等待程序结束后手动比对。\nFolder %s information check failed! Please check manually after the program execution finishes." %(url, url))
                log.write("文件夹%s信息获取失败！请等待程序结束后手动比对。\nFolder %s information check failed! Please check manually after the program execution finishes.\n" %(url, url))
                error_files.append(url)
                continue
            source = source.content.decode()
            source_list = list(map(lambda x: x.strip(), source.split("\n")))
            print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
            log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
            if mode == "1":
                print("页面文件列表如下：\nFile list is as follows:\n网页链接（URL)： %s" %url)
                log.write("页面文件列表如下：\nFile list is as follows:\n网页链接（URL)： %s\n" %url)
            elif mode == "2":
                print("最新修改时间后的页面文件列表如下：\nFile list after the latest modification time is as follows:\n网页链接（URL)： %s" %url)
                log.write("最新修改时间后的页面文件列表如下：\nFile list after the latest modification time is as follows:\n网页链接（URL)： %s\n" %url)
            for line in source_list:
                matchedLine = line_re.search(line)
                if matchedLine:
                    soup = BeautifulSoup(line, 'lxml')
                    name = soup.find("a")["href"]
                    size = soup.find("td", class_ = "size").text
                    date = soup.find("td", class_ = "date").text
                    date_obj = datetime.strptime(date, "%Y-%b-%d %H:%M")
                    timestamp = date_obj.timestamp()
                    if ".json" in name:
                        if ("cdragon/arena" in folder or "cdragon/tft" in folder) and (name != "en_us.json" and name != "zh_cn.json") or mode == "2" and timestamp < latest_mod_time:
                            continue
                        table["file"].append(name)
                        table["size"].append(size)
                        table["date"].append(date)
                        table["timestamp"].append(timestamp)
            table = pd.DataFrame(table)
            if table.empty:
                print(table)
                log.write(str(table) + "\n")
            else:
                print(format_df(table)[0])
                log.write(format_df(table)[0] + "\n")
            dir = os.path.join(local_prefix, folder).replace("\\", "/")
            for i in range(len(table)):
                cnt2 += 1
                name = table["file"][i]
                print("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())), end = "")
                log.write("[%s]" %(time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())))
                print("[%d/%d][%d/%d]正在校对文件（Checking file）： %s" %(cnt1, len(cdragon_folders), cnt2, len(table), urljoin(url, name)))
                log.write("[%d/%d][%d/%d]正在校对文件（Checking file）： %s\n" %(cnt1, len(cdragon_folders), cnt2, len(table), urljoin(url, name)))
                update = added = False
                src, status = getUrl(urljoin(url, name), log)
                if not status:
                    print("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes." %(urljoin(url, name), urljoin(url, name)))
                    log.write("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes.\n" %(urljoin(url, name), urljoin(url, name)))
                    error_files.append(urljoin(url, name))
                    continue
                src = src.json()
                if not name in os.listdir(dir):
                    update = added = True
                else:
                    with open(os.path.join(dir, name), "r", encoding = "utf-8") as fp:
                        dst = json.load(fp)
                    if src != dst:
                        update = True
                if update:
                    with open(os.path.join(dir, name), "w", encoding = "utf-8") as fp:
                        json.dump(src, fp, indent = 4, ensure_ascii = False)
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
        if error_files:
            print("以下文件比对失败。请重新比对！\nThe following files fail to be checked. Please check manually!")
            log.write("以下文件比对失败。请重新比对！\nThe following files fail to be checked. Please check manually!\n")
            for file in error_files:
                print(file)
                log.write(file + "\n")
            print()
    elif resource[0] == "2":
        if ddragon_hint:
            hint = '请按以下步骤操作：\nPlease follow these steps:\n1. 访问网址https://developer.riotgames.com/docs/lol#data-dragon\n   Visit the website: https://developer.riotgames.com/docs/lol#data-dragon\n2. 在Latest中找到正式服最新版本数据资源压缩包下载链接。例如：https://ddragon.leagueoflegends.com/cdn/dragontail-14.8.1.tgz\n   Find the link to download the compressed tarball of the latest data resource for live servers. For example: https://ddragon.leagueoflegends.com/cdn/dragontail-14.8.1.tgz\n3. 下载。这需要花费一些时间。\n   Download the file. It may take some time.\n4. 将下载好的tgz文件直接“解压至此”。\n   "Extract here" for the tgz file.\n5. 将解压出来的压缩包再次解压到选定文件夹下与压缩包同名的文件夹。示例：将“dragontail-14.8.1.tar”解压到“D:/360AI浏览器下载/dragontail-14.8.1”文件夹下。\nExtract to "Archive-Name" folder under the selected folder for the extracted tar file. For example, extract "dragontail-14.8.1.tar" into the folder "D:/Downloads/dragontail-14.8.1".\n接下来，请给出数据资源的位置。（按照上例应为“D:/360AI浏览器下载/dragontail-14.8.1/14.8.1/data”。）\nNext, please provide the directory that stores the data resources. (By the above example, the directory should be "D:/Downloads/dragontail-14.8.1/14.8.1/data".)'
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
                if file.endswith(".json"):
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
        if not status:
            print("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes." %(version_url, version_url))
            log.write("文件%s比对失败！请等待程序结束后手动比对。\nFile %s check failed! Please check manually after the program execution finishes.\n" %(version_url, version_url))
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