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
    if os.path.isfile('login-jp.txt'):
        with open('login-jp.txt', 'r') as f:
            loginid = f.readline().strip()
            password = f.readline().strip()
#			print(loginid,password)
    else:
        loginid = input('电子邮箱：')
        password = input('密码：')
    print('\n开始尝试登录\n')
    login_data = {
        'autoLoginChk': 'Y',
        'loginid': loginid,
        'password': password,
        'nexturl': 'http://www.comico.jp/index.nhn',
    }
    r = s.post('https://id.comico.jp/login/login.nhn',data=login_data, headers=headers)
    r = s.get("https://id.comico.jp/login/login.nhn")
    soup = BeautifulSoup(r.text, 'lxml')
    # 若登录失败，login.nhn返回一个js函数，成功便返回一个网页
    flag = soup.find('body')
    if flag == None:
        with open('login-jp.txt', 'w') as f:
            f.write('%s\n%s' % (loginid, password))
            print('登录成功\n')
    else:
        if os.path.isfile('login-jp.txt'):
            os.remove('login-jp.txt')
        print('登录失败,请重试！\n')

# 漫画代码为titleNo，relife的为2
titleNo = '2'
#print('说明：\n以第186话为例，网址是：http://www.comico.com.tw/1/193/ \n网址最后的数字 193 即为这话的网页代码\n如果只下载一话，则 开始与结束 的网页代码都填这一话的即可\n')
b = int(input('开始网页代码:'))
e = int(input('结束网页代码:'))
while e < b:
    print('输入错误！\n')
    b = int(input('开始网页:'))
    e = int(input('结束网页:'))

for n in range(b, e+1):
    articleNo=str(n)
    data={
    'titleNo':titleNo,
    'articleNo':articleNo,
    }
    url='http://www.comico.jp/detail.nhn?titleNo='+titleNo+'&articleNo='+articleNo
    r=s.get(url,data=data,headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')

    if soup.find("m-comico-body__inner") != None:
        print(url+'页面不存在\n')
        continue

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
        # print(' 《%s》 无法下载\n' % title)
        # continue
        pay_data={
        'titleNo':titleNo,
        'articleNo':articleNo,
        'paymentCode':'K',
        'coinUseToken':'',
        'productNo':'5',
        'price':'10',
        }
        pay_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \AppleWebKit/537.36 (KHTML, like Gecko) \Chrome/60.0.3112.90 Safari/537.36',
        'DNT':'1',
        'Host':'www.comico.jp',
        'Origin':'http://www.comico.jp',
        'Pragma':'no-cache',
        'Referer':url,
        'Upgrade-Insecure-Requests':'1',
        }
        s.post('http://www.comico.jp/consume/index.nhn',data=pay_data,headers=pay_headers)
        r=s.get(url,data=data,headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')

    if soup.find(class_="locked-episode__list-btn-item") != None:
        print(' 《%s》 无法下载\n' % title)
#        print(r.text)
        continue

    # 获取图片链接
    img_div=soup.find_all("img","comic-image__image")
    img_list=[]
    for div in img_div:
        img_list.append(div['src'])

    # 建立文件夹
    imgdir = './%s' % title
    if os.path.isdir(imgdir) == False:
        os.mkdir(imgdir)

    # 创建压缩文件
    zfile = zipfile.ZipFile("%s.zip" % title, "w", zipfile.zlib.DEFLATED)

    imgpath = []

    # 下载图片并添加到压缩文件中
    for i in img_list:
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
print('所有下载任务已经完成')
input('按任意键退出')