该存储库存储了CommunityDragon和DataDragon数据库中的所有**文本类型**的数据资源，用以呈现各版本的详细变化。CommunityDragon数据库的数据资源将跟随<ins>美测服的每一次调整</ins>而更新，更新周期以**天**计；DataDragon数据库的数据资源将跟随<ins>正式服的每一次停机更新</ins>而更新，更新周期以**半个月**计。\
数据资源更新是通过主目录下的离线数据更新脚本来进行的。
- 在更新CommunityDragon数据库的数据资源时，程序提供了五个选项和两种模式：
    - 选项（范围）
        1. 【所有文件】——更新“latest”和“pbe”文件夹下的所有文本类型数据资源
            - 该选项为默认选项。输入空字符串即选择默认选项。
        2. 【所有正式服文件】——更新“latest”文件夹下的所有文本类型数据资源
        3. 【所有测试服文件】——更新“pbe”文件夹下的所有文本类型数据资源
        4. 【程序所需文件】——更新所有自定义脚本涉及的数据资源
            - 在[程序集](https://github.com/WordlessMeteor/LoL-DIY-Programs)中，该选项为默认选项。
        5. 【自行指定】——通过输入网址来指定要更新的数据资源
    - 模式
        - 【全局扫描】可将本地存储库中的数据资源与在线CommunityDragon数据库和下载到本地的最新DataDragon存档压缩包中的数据资源进行全面对比，实现数据资源的同步。
        - 【按修改时间更新】用于反映本地数据资源和在线数据资源的变化。
            - 如果本地数据资源文件的修改时间晚于在线数据资源文件，而本地数据资源文件的内容实际上早于在线数据资源文件，那么这些数据资源文件不会更新。
            - 该模式为默认模式。输入空字符串即采用默认模式。
        - 对于联网更新的资源，使用适当的代理可能加速数据资源的获取。
- 在更新DataDragon数据库的资源时，用户需要按照程序提示，先下载DataDragon数据库的最新压缩包，然后解压，并提供解压的目录。
- 在更新DataDragon数据库的数据资源时，程序提供了两个选项：
    - 【全局比对】——更新简体中文和美式英语的数据资源
    - 【按程序需求更新】——更新所有自定义脚本涉及的数据资源

由于每次更新可能涉及的数据资源较多，GitHub无法加载变化内容。以下推荐两种查看变化内容的方式：
1. 访问或克隆[英雄联盟版本更新存储库](https://github.com/WordlessMeteor/LoL-Patch-Change)以*在线*查看**主要**更新内容。
2. 将[本仓库](https://github.com/WordlessMeteor/LoL-Dragon-Change)克隆到本地，并查看标题为“<ins>离线数据资源更新</ins>”的提交，以*离线*查看**完整**更新内容。
    - 克隆该存储库需要占用大约<ins>42.5 GB</ins>的本地空间。请保证您的磁盘有足够的空间。
        - 该选项为默认选项。输入空字符串即选择默认选项。
    - 对于包含较多数据资源的更新的提交，本地加载仍然需要几分钟时间，请耐心等待。
        - 在[程序集](https://github.com/WordlessMeteor/LoL-DIY-Programs)中，该选项为默认选项。

程序集已迁移至[新的存储库](https://github.com/WordlessMeteor/LoL-DIY-Programs)。

----
(The following content is the English version of README.)

This repository stores all data resources **of text type** in CommunityDragon and DataDragon databases for patch change. The update of data resources in CommunityDragon database will follow <ins>each adjustment of PBE</ins> **daily**, and the update of data resources in DataDragon database will follow <ins>each patch mainteinance of live servers</ins> **about every fortnight**.\
Data resource update is performed by Offline Data Updating Program under the home directory.
- While updating CommunityDragon data resources, the program provides five options and two modes:
    - Options (Ranges)
        1. [All files]: Update all data resources of text type under "latest" and "pbe" folders
            - This option is set as the default option. Submit an empty string to select the default option.
        2. [All latest files]: Update all data resources of text type under "latest" folders
        3. [All PBE files]: Update all data resources of text type under "pbe" folders
        4. [Program requirement]: Update all data resources involved in all customized programs
            - In [the program set](https://github.com/WordlessMeteor/LoL-DIY-Programs), this option is set as the default option.
        5. [Specify manually]: Specify the data resources update by entering urls
    - Modes
        - [Global Scanning] performs an entire comparison on the data resources between the local repository and the online CommunityDragon database or the latest DataDragon archive compressed file that has already been downloaded to local, to synchronize data resources.
        - [Updating According to Modification Time] is meant to reflect the changes between online and local data resources.
            - In a case where the **modification times** of some local data resources are **later** than those of the corresponding online data resources, whereas the **actual content** of these local data resources is **earlier** than that of their corresponding online data resources, running this mode won't update these local data resources.
            - This mode is set as the default mode. Submit an empty string to adopt the default mode.
        - For resources updated online, an appropriate proxy may accelerate the data capture process.
- While updating DataDragon data resources, users need to **follow the hint of the program**: first download the latest compressed tarball of DataDragon database, then decompress it, and finally provide the decompression directory.
- While updating DataDragon data resources, the program provides two options:
    - [Global compare]: Update data resources in zh_CN and en_US
        - This option is set as the default option. Submit an empty string to select the default option.
    - [Update according to program demands]: Update only data resources involved in all customized programs
        - In [the program set](https://github.com/WordlessMeteor/LoL-DIY-Programs), this option is set as the default option.

Because a number of data resources might be involved in a commit, GitHub can't load the diff. Here two methods of checking the diff are recommended:
1. Visit or clone [LoL-Patch-Change repository](https://github.com/WordlessMeteor/LoL-Patch-Change) to look over the **main** update content *online*.
2. Clone [this repository](https://github.com/WordlessMeteor/LoL-DIY-Programs) to local and check the commit with header "<ins>Offline Data Resource Update</ins>" to look through the **complete** update content *offline*.
    - Cloning this repository takes up approximately <ins>42.5 GiB</ins> local space. Please ensure your disk has sufficient space for it.
    - For those commits that involve a number of data resources, it still takes several minutes to load the diff locally. Please wait in patience.

The program set has migrated to [a new repository](https://github.com/WordlessMeteor/LoL-DIY-Programs).