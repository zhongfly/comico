# encoding:UTF-8
# 依赖库：
# requests
# BeautifulSoup4
# lxml
import requests
import urllib.request
import os
from bs4 import BeautifulSoup
# 文件名变量部分（中间部分）
targetlist = ['_001_001', '_001_002', '_001_003', '_001_004', '_001_005',
              '_001_006', '_001_007', '_001_008', '_001_009', '_001_010',
              '_001_011', '_001_012', '_001_013', '_001_014', '_001_015',
              '_001_016', '_001_017', '_001_018', '_001_019', '_001_020',
              '_002_021', '_002_022', '_002_023', '_002_024', '_002_025',
              '_002_026', '_002_027', '_002_028', '_002_029', '_002_030',
              '_002_031', '_002_032', '_002_033', '_002_034', '_002_035',
              '_002_036', '_002_037', '_002_038', '_002_039', '_002_040'
              ]
# 获取漫画名并建立文件夹
# 漫画编号 1 = relife 2346 = 脫處大作戰 2353 = 我的意外美眉
uid = 1
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/58.0.3029.110 Safari/537.36'
}
r = requests.get(r'http://www.comico.com.tw/%d/' % uid, headers=headers)
content = r.text
soup = BeautifulSoup(content, 'lxml')
comic_name_div = soup.find(class_="article-hero05__ttl")
comic_name = comic_name_div.string
comic_dir = './%s' % comic_name
print('将要开始下载漫画：%s' % comic_name)
if os.path.isdir(comic_dir) == False:
    os.mkdir(comic_dir)
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
    title.replace('?', '？')
    title.replace('!', '！')
    # 生成图片下载地址
    for div in divs:
        url = div.get('style')
        url = url[23:-83]
    target = [url + x + '.jpg' for x in targetlist]
    print('已获取图片地址')
    # 建立文件夹
    imgdir = './%s/%s' % (comic_name, title)
    if os.path.isdir(imgdir) == False:
        os.mkdir(imgdir)
    # 下载图片
    t = 1
    for link in target:
        try:
            urllib.request.urlopen(link)
        except urllib.error.URLError as e:
            print('%s not exit' % link)
            break
        else:
            path = r'%s/%d.jpg' % (imgdir, t)
            urllib.request.urlretrieve(link, path)
            t = t+1
    print('已下载%s，共%d张图片\n' % (title, t-1))
print('已完成所有下载!')
