#### Windows环境git下安装gitflow步骤
参考文档，来自github的gitflow的wiki，[链接戳我！](https://github.com/nvie/gitflow/wiki/Windows)
这里只介绍msysgit环境下的gitflow安装。
首先需要下载两个文件：
-   **getopt.exe**
-   **libintl3.dll**

##### 下载地址：
- [util-linux-ng-2.14.1-bin.zip](http://sourceforge.net/projects/gnuwin32/files/util-linux/2.14.1/util-linux-ng-2.14.1-bin.zip/download)
- [util-linux-ng-2.14.1-dep.zip](http://sourceforge.net/projects/gnuwin32/files/util-linux/2.14.1/util-linux-ng-2.14.1-dep.zip/download)

我们需要的以下两个文件
- **getopt.exe(util-linux-ng-2.14.1-bin.zip => bin)**
- **libintl3.dll(util-linux-ng-2.14.1-dep.zip => bin)**

将这两个文件拷贝到git安装目录的bin目录下，如下。
```
C:\Program Files (x86)\Git\bin
```
然后打开“Git Bash”输入下面的命令：
```
$ git clone --recursive git@github.com:nvie/gitflow.git
```
等下载完毕，切回到gitflow develop branch 打开windows下的命令行工具，
进入到刚才下载的文件目录中，例如：如果刚才是在c盘下执行的git clone命令，
则进入到gitflow/contrib>目录，然后执行下面命令（可能需要管理员权限）
```
msysgit-install.cmd [git的安装目录]

D:\+1\Development\Projects\gitflow\contrib>msysgit-install.cmd "C:\Program Files(x86)\Git"
```

执行完毕，打开“Git Bash”，输入命令 git flow。
