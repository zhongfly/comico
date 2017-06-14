# encoding:UTF-8
# 依赖库：
# requests
# BeautifulSoup4
# lxml
import requests
import urllib.request
import os
from bs4 import BeautifulSoup
# 生成文件名变量部分（中间部分）
temp = []
temp1 = ['_00'+str(x) for x in range(1, 10)]
temp2 = ['_0'+str(x) for x in range(10, 21)]
temp.extend(temp1)
temp.extend(temp2)
temp1 = ['_0'+str(x) for x in range(21, 41)]
targetlist = ['_001' + t for t in temp]
targetlist0 = ['_002' + t for t in temp1]
targetlist.extend(targetlist0)

# 漫画编号 1 = relife 2346 = 脫處大作戰 2353 = 我的意外美眉
uid = 1
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/58.0.3029.110 Safari/537.36'
}
# 指定开始与结束的章节
b = int(input('begin:'))
e = int(input('end:'))
while e < b:
    print('输入错误！')
    e = int(input('end:'))
for n in range(b, e+1):
    # 获取图片下载地址前半部分
    target = []
    divs = []
    web = (r'http://www.comico.com.tw/%d/%d/' % (uid, n))
    print('处理网页%s中' % web)
    r = requests.get(web, headers=headers)
    content = r.text
    soup = BeautifulSoup(content, 'lxml')
    test = soup.find(href="http://www.comico.com.tw/",
                     class_="m-btn-top o-replacement")
    if test == None:
        divs = soup.find_all(class_="locked-episode__kv _lockedEpisodeKv")
    else:
        print('%s该页面不存在\n' % web)
        continue

    if divs == []:
        print('%s为免费章节，跳过\n' % web)
        continue
    # 获取标题
    title_div = soup.find(class_="comico-global-header__page-title-ellipsis")
    title = title_div.string
    # 生成图片下载地址
    for div in divs:
        url = div.get('style')
        url = url[23:-83]
    target = [url + x + '.jpg' for x in targetlist]
    print('已获取图片地址')
    # 建立文件夹
    imgdir = './%s' % title
    if os.path.isdir(imgdir) == False:
        os.mkdir(imgdir)
    # 下载图片
    t = 1
    for link in target:
        try:
            urllib.request.urlopen(link)
        except urllib.error.URLError as e:
            break
        else:
            path = r'%s/%d.jpg' % (imgdir, t)
            urllib.request.urlretrieve(link, path)
            t = t+1
    print('已下载%s，共%d张图片\n' % (title, t-1))
print('已完成所有下载!')
