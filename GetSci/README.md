# Spider for sci

## 1. What is this?
This spider is written to get sci papers information from the following websites:
1. https://xs.zidianzhan.net/ --> get paper links
2. [scihub](https://sci-hub.et-fine.com/) --> get papers

## 2. How to use it?
1. Download python3.6(higher version also can be accepted) or pycharm(more efficiently)
2. if you have python, you **need** to check whether you have the following packages:

| Packages     | Version | 
|--------------|---------|
| **pandas**   | 1.5.2   |
| **selenium** | 4.72    |
| **bs4**      | 0.01    |
| **os**       | none    |
| **requests** | 2.28.1  |
| **re**       | none    |
| **random**   | none    |

* the version `none` refers to these packages have existed when you choose pycharm

the following packages are **not necessary** if you don't need, but you should find the related sentence to delete or comment out (`shift + ?`)

| Packages | Version   |
|----------|-----------|
| time     | none      |
* How to find sentences using package `time`?
  * use `ctrl + F` to search `time` .
  * usually I use the following sentences:
    * start_time = time.time()                          
      * in `main.py` line 8, `GetPapers.py` line 19
    * end_time = time.time()                            
      * in `main.py` line 14, `GetPapers.py` line 66
    * print("总用时 %.3f s" % (end_time-start_time))     
      * in `main.py` line 15
    * print('爬取用时 %.3f s' % (end_time-start_time))    
      * in `GetPapers.py` line 67
3. How to install these packages?
    * for python, you need to use the following sentence in the console(for windows: cmd, for linux: terminal), make sure you've added `pip` into the system environment.
      * ```
        pip install package_name
        ```
    * for pycharm, you only need to find file -- set -- python interpret -- click the `+` and search the package to install
4. **you need install `Chrome` and `selenium driver`, the download links are following:**
    * [chrome](https://www.google.cn/intl/zh-CN/chrome/) version 108.0.5395
    * [selenium dirver](https://registry.npmmirror.com/binary.html?path=chromedriver/) find the driver suitable for chrome, and download it. Move it (`.exe` file) to you python install dir.
5. if all steps you have done, you can click run(`main.py`) to find sci papers.
6. if all success, you'll get paper pdfs and a csv sheet to tell you the papers' information.

## 3. some bugs
1. some pdf can't save, usually the file size is 0 bytes, you can download it manually.