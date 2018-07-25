# encoding:UTF-8
# python3.6
import os
import re
import time
import threading
import queue
import json
import requests
import zipfile
from bs4 import BeautifulSoup
from PIL import Image

titleNo='1'
path = './'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/64.0.3282.186 Safari/537.36',
}
pattern = re.compile(
    r'''http://comicimg\.comico\.com\.tw/onetimecontents/pc/.*(?=')''')
coinUseToken=''

def save_cookies(session, file='cookie.txt'):
    with open(file, 'w') as f:
        json.dump(requests.utils.dict_from_cookiejar(session.cookies), f)


def load_cookies(session, file='cookie.txt'):
    with open(file, 'r') as f:
        session.cookies = requests.utils.cookiejar_from_dict(json.load(f))


def islogin(session):
    if os.path.exists('cookie.txt'):
        load_cookies(session)
    else:
        pass
    r = session.get('https://id.comico.com.tw/settings/',
                    headers=headers)
    if r.url == 'https://id.comico.com.tw/settings/':
        save_cookies(session)
        return True
    else:
        return False


def login(session, loginid, password):
    data = {
        'autoLoginChk': 'Y',
        'loginid': loginid,
        'password': password,
        'nexturl': 'http://www.comico.com.tw/index.nhn',
    }
    session.post('https://id.comico.com.tw/login/login.nhn',
                 data=data, headers=headers)


def get_comic(session, titleNo, articleNo):
    if not isinstance(titleNo, str):
        titleNo = str(titleNo)
    if not isinstance(articleNo, str):
        articleNo = str(articleNo)

    r = session.get(f'http://www.comico.com.tw/{titleNo}/{articleNo}/', headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')

    # 网页是否存在
    if soup.find(id='main'):
        print(f'http://www.comico.com.tw/{titleNo}/{articleNo}/ 网页不存在')
        return False

    # 获取标题
    title_div = soup.find(class_="comico-global-header__page-title-ellipsis")
    title = title_div.string
    # 去除最后的空格，避免半角问号导致文件夹无法命名
    title = title.rstrip().replace('?', '？').replace('!', '！')

    # 处理被锁章节，并解锁
    if soup.find(class_="locked-episode__list-btn") != None:
        lock_div=soup.find(class_="locked-episode__list-btn")
        # 是否可用专用阅读券
        if lock_div.find(attrs={"data-payment-code": "K"}) != None:
            paymentCode = 'K'
        # 是否可用POINT，以上2项均否则为必须用coin购买的章节
        elif lock_div.find(attrs={"data-payment-code": "P"}) != None:
            paymentCode = 'P'
        # 是否使用coin购买
        elif input('是否使用%scoins购买《%s》？【y/n】' % (soup.find_all('input')[-3]['value'], title)) == 'y':
            paymentCode = 'C'
        else:
            print('《%s》无法下载' % title)
            return False
        global coinUseToken
        if paymentCode == 'C' and coinUseToken == '':
            r = session.get('http://www.comico.com.tw/consume/coin/publish.nhn',
                            data={'paymentCode': 'C', }, headers=headers)
            # {"result":{"coinUseToken":"3OcKoCqoRSd9uRVD47mk"}}
            coinUseToken = r.text[27:-3]
        else:
            pass
        pay_data = {
            'titleNo': titleNo,
            'articleNo': articleNo,
            'paymentCode': paymentCode,  # K为专用阅读券，P为Point，C为coin
            'coinUseToken': coinUseToken,  # 使用coin时才需要
            'productNo': soup.find_all('input')[-4]['value'],
            'price': soup.find_all('input')[-3]['value'],
            'rentalPrice': '',  # 用coin租用价格，一般能租用的都可以用阅读券，没必要
            'pointRentalPrice':soup.find_all('input')[-1]['value'],
        }
        session.post('http://www.comico.com.tw/consume/index.nhn',
                     data=pay_data, headers=headers)
        r = session.get(f'http://www.comico.com.tw/{titleNo}/{articleNo}/', headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        if soup.find(class_="locked-episode__list-btn") != None:
            print(' 《%s》 无法下载\n' % title)
            return False
        else:
            payment = {'K': '专用阅读券', 'P': 'Point', 'C': 'Coin'}
            print('已使用%s解锁章节《%s》' % (payment[paymentCode], title))

    # 获取图片链接
    firstimg_div = soup.find(class_="comic-image__image")
    firstimg_url = firstimg_div.get('src')
    url = []
    url.append(firstimg_url)
    string = soup.find_all('script', limit=3)[2].text
    url.extend(pattern.findall(string))
    print('已获取 《%s》 的下载链接' % title)
    comic = {}
    comic['title'] = title
    comic['url'] = url
    return comic


def download(session, url, dir):
    img = os.path.join(dir, url[-74:-68])
    r = session.get(url, headers=headers, stream=True)
    if r.status_code == 200:
        with open(img, 'wb') as f:
            for chunk in r:
                f.write(chunk)


def DownloadThread(q,session, dir):
    while True:
        try:
            # 不阻塞的读取队列数据
            url = q.get_nowait()
        except queue.Empty as e:
            break
        except Exception as e:
            raise
        download(session,url,dir)
        q.task_done()


def imgzip(filename, dir):
    zfile = zipfile.ZipFile(f"{filename}.zip", "w", zipfile.zlib.DEFLATED)
    imgpath = [entry.path for entry in os.scandir(
        dir) if entry.name.endswith(".jpg")]
    for img in imgpath:
        zfile.write(img, os.path.basename(img))
    zfile.close()
    print(f'已创建压缩文件{filename}.zip\n')


def get_longpic(filename, dir):
    imgpath = [entry.path for entry in os.scandir(dir) if entry.name.endswith(".jpg")]
    # 拼接长图
    with Image.open(imgpath[-1]) as i:
        total_height = (len(imgpath)-1)*2000+i.height
    new_img = Image.new('RGB', (690, total_height))
    y_offset = 0
    for img in imgpath:
        with Image.open(img) as f:
            new_img.paste(f, (0, y_offset))
        y_offset = y_offset+2000
    try:
        new_img.save(os.path.join(path, f'{filename}.jpg'))
    except Exception as e:
        new_img.save(os.path.join(path, f'{filename}.png'))
    
    print(f'已拼接长图:{filename}\n')


def get_one(session, titleNo, articleNo):
    comic=get_comic(session, titleNo, articleNo)
    if comic==False:
        return False
    title=comic['title']
    imgdir = os.path.join(path,title)
    if os.path.isdir(imgdir) == False:
        os.mkdir(imgdir)
    else:
        pass
    q = queue.Queue()
    for url in comic['url']:
        q.put(url)  
    start = time.time()
    threads=[]
    for i in range(5):
        thread=threading.Thread(target=DownloadThread, args=(q, session, imgdir))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    end=time.time()
    print('{}已下载，耗时{}'.format(title,end-start))
    imgzip(title, imgdir)
    get_longpic(title, imgdir)
    return True


def main():
    s = requests.Session()
    while(islogin(s)==False):
        loginid = input('电子邮箱：')
        password = input('密码：')
        login(s, loginid, password)
    print('已成功登录')
    print('说明：\n以第186话为例，网址是：http://www.comico.com.tw/1/193/\n网址最后的数字 193 即为这话的网页代码\n如果只下载一话，则 开始与结束 的网页代码都填这一话的即可\n')
    e,b=range(2)

    while e < b:
        b = int(input('开始网页代码:'))
        e = input('结束网页代码:')
        if e=='':
            e=b
        else:
            e=int(b)

    for articleNo in range(b, e+1):
        if get_one(s, titleNo, articleNo) == False:
            break
        print('所有任务已经完成')
        input('按任意键退出')

if __name__ == '__main__':
    main()
