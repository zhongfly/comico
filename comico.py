# encoding:UTF-8
import queue
import lxml
# 以上均为用pyinstaller打包时需要加上的依赖
import requests
import os
from bs4 import BeautifulSoup
import zipfile
from PIL import Image

print('comico漫画下载\n作者：ishadows\n')
s = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/60.0.3112.90 Safari/537.36',
}

# 登录并保存正确的账号信息
flag = 1
while flag != None:
    if os.path.isfile('login.txt'):
        with open('login.txt', 'r') as f:
            loginid = f.readline().strip()
            password = f.readline().strip()
    else:
        loginid = input('电子邮箱：')
        password = input('密码：')
    print('\n开始尝试登录\n')
    data = {
        'autoLoginChk': 'Y',
        'loginid': loginid,
        'password': password,
        'nexturl': 'http://www.comico.com.tw/index.nhn',
    }
    s.post('https://id.comico.com.tw/login/login.nhn',
           data=data, headers=headers)
    r = s.get("https://id.comico.com.tw/login/login.nhn")

    soup = BeautifulSoup(r.text, 'lxml')
    # 若登录失败，login.nhn返回一个js函数，成功便返回一个网页
    flag = soup.find('body')
    if flag == None:
        if os.path.isfile('login.txt') == False:
            with open('login.txt', 'w') as f:
                f.write('%s\n%s' % (loginid, password))
        print('登录成功\n')
    else:
        if os.path.isfile('login.txt'):
            os.remove('login.txt')
        print('登录失败,请重试！\n')

r = s.get('http://www.comico.com.tw/consume/coin/publish.nhn',
          data={'paymentCode': 'C', }, headers=headers)
# {"result":{"coinUseToken":"3OcKoCqoRSd9uRVD47mk"}}
coinUseToken = r.text[27:-3]

# 漫画代码，relife的为1
titleNo = '1'
print('说明：\n以第186话为例，网址是：http://www.comico.com.tw/1/193/\n网址最后的数字 193 即为这话的网页代码\n如果只下载一话，则 开始与结束 的网页代码都填这一话的即可\n')
b = int(input('开始网页代码:'))
e = int(input('结束网页代码:'))
while e < b:
    print('输入错误！\n')
    b = int(input('开始网页:'))
    e = int(input('结束网页:'))

for n in range(b, e+1):
    articleNo = str(n)
    r = s.get("http://www.comico.com.tw/%s/%d/" % (titleNo, n))
    soup = BeautifulSoup(r.text, 'lxml')

    # 网页是否存在
    if soup.find(id='main'):
        print('www.comico.com.tw/%s/%d/ 网页不存在' % (titleNo, n))
        break

    # 获取标题
    title_div = soup.find(class_="comico-global-header__page-title-ellipsis")
    title = title_div.string
    # 去除最后的空格
    title.rstrip()
    # 避免半角问号导致文件夹无法命名
    title.replace('?', '？')
    title.replace('!', '！')

   # 检查章节是否解锁
    if soup.find(class_="locked-episode__list-btn-item") != None:
        # 是否可用专用阅读券
        if soup.find(class_="locked-episode__list-btn-item _transparent") != None:
            paymentCode = 'K'
        # 是否可用通用阅读券，以上2项均否则为必须用coin购买的章节
        elif soup.find(class_="locked-episode__list-btn-item o-hidden _transparent") != None:
            paymentCode = 'MK'
        # 是否使用coin购买
        elif input('是否使用%scoins购买《%s》？【y/n】' % (soup.find_all('input')[-2]['value'], title)) == 'y':
            paymentCode = 'C'
        else:
            print('《%s》无法下载' % title)
            continue
        pay_data = {
            'titleNo': titleNo,
            'articleNo': articleNo,
            'paymentCode': paymentCode,  # K为专用阅读券，MK为通用阅读券，C为coin
            'coinUseToken': coinUseToken,  # 使用coin时才需要
            'productNo': soup.find_all('input')[-3]['value'],
            'price': soup.find_all('input')[-2]['value'],
            'rentalPrice': '',  # 用coin租用价格，一般能租用的都可以用阅读券，没必要
        }
        s.post('http://www.comico.com.tw/consume/index.nhn',
               data=pay_data, headers=headers)
        r = s.get('http://www.comico.com.tw/%s/%d/' %
                  (titleNo, n), headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        if soup.find(class_="locked-episode__list-btn-item") != None:
            print(' 《%s》 无法下载\n' % title)
            continue
        else:
            payment={'K':'专用阅读券','MK':'通用阅读券','C':'Coin'}
            print('已使用%s解锁章节《%s》'%(payment[paymentCode],title))

    # 获取图片链接
    firstimg_div = soup.find(class_="comic-image__image")
    firstimg_url = firstimg_div.get('src')
    url = []
    url.append("%s" % firstimg_url)

    # 提取在js中的图片链接
    items = soup.find_all('script', limit=3)
    string = str(items[2].string)
    string = string.replace(']', '[')
    string = string.split("[")
    string = string[1].replace("\r\n\t\r\n\t'", "'\r\n\t")
    string = string.replace("',\r\n\t'", "'\r\n\t")
    string = string.split("'\r\n\t")
    url.extend(string[1:-1])
    print('已获取 《%s》 的下载链接' % title)

    # 建立文件夹
    imgdir = './%s' % title
    if os.path.isdir(imgdir) == False:
        os.mkdir(imgdir)

    # 创建压缩文件
    zfile = zipfile.ZipFile("%s.zip" % title, "w", zipfile.zlib.DEFLATED)

    imgpath = []

    # 下载图片并添加到压缩文件中
    for i in url:
        path = '%s/%s' % (imgdir, i[-74:-68])
        imgpath.append(path)
        r = s.get(i, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            zfile.write(path, os.path.basename(path), zipfile.ZIP_DEFLATED)
    zfile.close()
    print('已完成 《%s》 的下载' % title)

    # 拼接长图
    images = map(Image.open, imgpath)
    heights = [i.height for i in images]
    total_height = sum(heights)
    new_im = Image.new('RGB', (690, total_height))
    y_offset = 0
    for im in imgpath:
        fromImage = Image.open(im)
        new_im.paste(fromImage, (0, y_offset))
        fromImage.close()
        y_offset = y_offset+2000
    new_im.save('%s.jpg' % title)
    print('已拼接长图\n')
print('所有任务已经完成')
input('按任意键退出')
