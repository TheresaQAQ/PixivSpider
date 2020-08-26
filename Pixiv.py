from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from configparser import  ConfigParser
import time
import requests
import json
import os
import re

cookies = {'ki_t': '1596232916887%3B1596232916887%3B1596232916887%3B1%3B1', '_fbp': 'fb.1.1596232916064.554409096', '__utmb': '235335808.1.10.1596232912', 'login_bc': '1', '__utmv': '235335808.|3=plan=normal=1^5=gender=male=1^6=user_id=33324042=1^11=lang=zh=1', '__utmc': '235335808', 'c_type': '26', 'b_type': '1', 'a_type': '0', '__utmz': '235335808.1596232912.1.1.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/login', 'yuid_b': 'EQA4VgU', '_gat': '1', '__cfduid': 'd6ba69ce1b7e176ff71739dd4449a01661596232912', 'device_token': 'dca43352bb1501ffa87a87a5190d5db3', 'PHPSESSID': '33324042_FtyR5vktJwa42aO10NLJ3gQYZXgLJaGh', '_gid': 'GA1.2.216418219.1596232890', '__utma': '235335808.731519508.1596232890.1596232912.1596232912.1', 'privacy_policy_agreement': '0', 'first_visit_datetime_pc': '2020-08-01+07%3A01%3A52', 'p_ab_id_2': '9', 'ki_r': '', '_ga': 'GA1.2.731519508.1596232890', 'p_ab_d_id': '750150235', '__utmt': '1', 'p_ab_id': '5'}

class Login:
    def __init__(self, username, password):
        self._url = 'https://accounts.pixiv.net/login'
        self._username = username
        self._password = password

    # Selenium库控制Chrome浏览器登录，返回Cookies
    def selenium_chrome(self):
        chrome = webdriver.Chrome()
        chrome.get('https://accounts.pixiv.net/login')
        time.sleep(2)
        chrome.find_element_by_css_selector('[autocomplete=username]').send_keys(self._username)
        chrome.find_element_by_css_selector('[autocomplete=current-password]').send_keys(self._password)
        chrome.find_element_by_css_selector('[autocomplete=current-password]').send_keys('\n')
        time.sleep(2)

        list_cookies = chrome.get_cookies()
        cookies = {}
        for s in list_cookies:
            cookies[s['name']] = s['value']
        chrome.quit()
        return cookies


class Pixiv:
    def __init__(self,cookies):

        self.ban_tags = ['SM''異物挿入','性器破壊','リョナ','陵辱','敗北','調教','拷問','R18-G',"重口","拡張",
         "全頭マスク", "Prolapse",'触手',"腐乱", "尸体", "腐敗", "蛆","猎奇", "脱糞", "スカトロ",
         "人體改造", "丧尸", "变异", "死体","屍姦","食人", "怪物くん", "异物"]
        self.cookies = cookies
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362'
        }

    def login_status(self):
        url = 'https://www.pixiv.net/'
        html = requests.get(url, cookies=self.cookies)
        soup = BeautifulSoup(html.text, 'html.parser')
        soup = soup.select('#wrapper > div.signup-form > div:nth-child(2) > a.signup-form__submit.js-click-trackable')

        return soup == []

    def threadpool(self,task,frequency,parameter):
        '''
        ########## 参数 ##########
        task: 任务名
        frequency:   线程数
        parameter: 参数 [()]
        '''
        with ThreadPoolExecutor(frequency) as executor:
            for args in parameter:
                executor.submit(lambda p: task(*p),args)

    # 通过时间，ID，页数拼接Url
    def _get_url(self,date,id,page='0'):
        '''
        ########## 参数 ##########
        data: 图片创建时间
        id:   图片ID
        page: 页数
        '''
        date = date.replace("-", "/")
        date = date.replace("T", "/")
        date = date.replace(":", "/")
        date = date[:date.find('+')]

        return 'https://i.pximg.net/img-original/img/{date}/{id}_p{page}.png'.format(date=date,id=id,page=str(page))

    def _get_detail_thread(self,id):
        pic = {}
        url = 'https://www.pixiv.net/ajax/illust/{id}?lang=zh'.format(id=id)
        dict = json.loads(requests.get(url=url, cookies=self.cookies, headers=self.headers).text)
        pic['bookmark'] = dict['body']['bookmarkCount']  # 收藏数
        pic['like'] = dict['body']['likeCount']  # 点赞数
        pic['view'] = dict['body']['viewCount']  # 观看数
        pic['name'] = dict['body']['alt']  # 整体名称
        pic['title'] = dict['body']['extraData']['meta']['title']  # 标题
        pic['date'] = dict['body']['createDate']  # 创建时间
        pic['id'] = dict['body']['id']  # ID
        pic['tags'] = dict['body']['tags']['tags']  # 标签
        pic['page'] = dict['body']['pageCount']  # 页数
        pic['userID'] = dict['body']['userId']  # 作者ID
        pic['userName'] = dict['body']['userName']  # 作者名

        origin_url = dict['body']['urls']['original']
        urls = []
        for i in range(pic['page']):
            list = origin_url.split('_')
            ed = list[-1]
            new_ed = ed.replace('0', str(i))
            new_url = list[0] + '_' + new_ed
            urls.append(new_url)

        pic['urls'] = urls  # 原图地址，列表

        self._data.append(pic)

    def _download_thread(self,name,urls,id,path=''):
        '''
        ########## 参数 ##########
        name: 作品名称
        urls: 作品地址，列表
        id:   作品Id
        path: 保存路径
        '''
        header = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': 'https://www.pixiv.net/artworks/' + str(id), # 必须项，否则403
            'Accept': 'image/png, image/svg+xml, image/*; q=0.8, */*; q=0.5',
            'Host': 'original.img.cheerfun.dev',
            'Cache-Control': 'max-age=0',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'Keep-Alive',
            'Accept-Language': 'zh-CN'
        }
        # 创建此路径文件夹(path)
        if not os.path.exists(path):
            os.mkdir(path)

        name = name.replace('#', '')
        for num in range(len(urls)):
            pic_name = name + '-第' + str(num+1) + '页' + urls[num][-4:]  # 作品保存文件名 [作品名]-第[int]页-[后缀]
            pic_path = path + pic_name # 路径


            if not os.path.exists(pic_path):
                # 如果文件不存在
                html = requests.get(url=urls[num], cookies=self.cookies, headers=header)
                if html.status_code == 200:
                    # 访问成功
                    with open(pic_path,'wb') as f:
                        f.write(html.content)
                elif html.status_code == 404:
                    # 错误404 后缀错误，更改后缀为.jpg重试
                    url = urls[num][:-4] + '.jpg'
                    html = requests.get(url=url, cookies=self.cookies, headers=header)
                    if html.status_code == 404:
                        # 错误404 后缀错误，更改后缀为.gif重试
                        url = urls[num][:-4] + '.gif'
                        html = requests.get(url=url, cookies=self.cookies, headers=header)
                        if html.status_code == 200:
                            pic_path = pic_path[:-4] + '.gif'
                            with open(pic_path, 'wb') as f:
                                f.write(html.content)
                    elif html.status_code == 200:
                        pic_path = pic_path[:-4] + '.jpg'
                        with open(pic_path,'wb') as f:
                            f.write(html.content)

    def _screen_thread(self,condition,data):
        id = data['id']
        url = 'https://www.pixiv.net/ajax/illust/{id}?lang=zh'.format(id=id)
        dict = json.loads(requests.get(url=url,cookies=self.cookies,headers=self.headers).text)
        bookmark = dict['body']['bookmarkCount']  # 收藏数
        like = dict['body']['likeCount']  # 点赞数
        view = dict['body']['viewCount']  # 观看数
        bookmark_probability = bookmark / view  # 收藏概率

        if bookmark_probability >= condition:
            self._screen_result.append(data)

    def search(self,keyword,mode='all',search_page='1',ban=True):
        '''
        ########## 参数 ##########
        word: 搜索内容
        mode: 搜索类型
              可选参数：all(全部) safe(全年龄) r18(18禁)
        p:    页数
        '''
        url = 'https://www.pixiv.net/ajax/search/artworks/{keyword}?word={keyword}&order=date_d&mode={mode}&p={page}&s_mode=s_tag&type=all&lang=zh'.format(keyword=keyword,mode=mode,page=search_page)
        dic = json.loads(requests.get(url=url,cookies=self.cookies,headers=self.headers).text)
        dic = dic['body']['illustManga']['data']
        data = []
        for i in dic:
            try:
                pic = {}
                pic['name'] = i['alt']  # 整体名称
                pic['title'] = i['title']  # 标题
                pic['date'] = i['createDate']  # 创建时间
                pic['id'] = i['id']  # ID
                pic['tags'] = i['tags']  # 标签
                pic['page'] = i['pageCount']  # 页数
                pic['userID'] = i['userId']  # 作者ID
                pic['userName'] = i['userName']  # 作者名

                # Url 列表
                urls = []
                for page in range(int(i['pageCount'])):
                    urls.append(self._get_url(date=i['createDate'],id=i['id'],page=page))
                pic['urls'] = urls  # 原图地址，列表
            except :
                # 如果前面出错，说明是广告位，不添加进data列表
                continue

            if ban == True:
                # 如果打开筛选违禁词
                tags = ''
                for i in pic['tags']:
                    i = str(i)
                    tags = tags + i
                if not [True for i in self.ban_tags if re.search(i, tags) != None]:
                    data.append(pic)
            elif ban == False:
                # 如果未打开筛选违禁词
                data.append(pic)

        search_type = {
            'safe':'全年龄',
            'all':'全部',
            'r18':'R18'
        }
        pics = {}
        pics['type'] = '搜索'
        pics['keyword'] = keyword
        pics['mode'] = search_type[mode]
        pics['data'] = data
        pics['search_page'] = '第{0}页'.format(search_page)
        pics['path'] = pics['type'] + '-' + pics['keyword'] + '-' + pics['mode'] + pics['search_page'] +  '\\'

        return pics

    def ranking_list(self,mode,freq=64,date='yestaday'):
        '''
        ########## 参数 ##########
        freq: 线程数
        mode: 排行榜类型
              可选参数：  1）今日 普通： daily
                        2）本周 普通：weekly
                        3）本月 普通：monthly
                        4）新人 普通：rookie
                        5）原创 普通：original
                        6）受男性欢迎 普通：male
                        7）受女性欢迎 普通：female
                        8）今日 R18：daily_r18
                        9）本周 R18：weekly_r18
                        10）本月 R18：monthly_r18
                        11）新人 R18：rookie_r18
                        12）原创 R18：original_r18
                        13）受男性欢迎 R18：male_r18
                        14）受女性欢迎 R18：female_r18
        date:    时间
        '''
        if date == 'yestaday':
            date = str(int(time.strftime("%Y-%m-%d", time.localtime()).replace('-',''))-1)
        url = 'https://www.pixiv.net/ranking.php?mode={mode}&date={data}'.format(mode=mode,data=date)
        html = requests.get(url,cookies=self.cookies,headers=self.headers)
        soup = BeautifulSoup(html.text,'html.parser')
        content = soup.find_all('div',attrs={'class':'ranking-image-item'})
        ids = []
        for i in content:
            id = i.find('a').get('href').split('/')[-1]
            ids.append(id)

        ranking_type = {
            'daily': '今日普通',
            'weekly': '本周普通',
            'monthly': '本月普通',
            'rookie': '新人普通',
            'original': '原创普通',
            'male': '受男性欢迎普通',
            'female': '受女性欢迎普通',
            'daily_r18': '今日R18',
            'weekly_r18': '本周R18',
            'monthly_r18': '本月R18',
            'rookie_r18': '新人R18',
            'original_r18': '原创R18',
            'male_r18': '受男性欢迎R18',
            'female_r18': '受女性欢迎R18'
        }

        data = self.get_detail(ids=ids,freq=freq)
        pics = {}
        pics['type'] = '排行榜'
        pics['date'] = date
        pics['mode'] = ranking_type[mode]
        pics['data'] = data
        pics['path'] = pics['type'] + '-' + pics['date'] + '-' + pics['mode'] + '\\'

        return pics


    def get_detail(self,ids,freq):
        self._data = []
        data = []
        for i in ids:
            data.append((i,))
        self.threadpool(task=self._get_detail_thread,parameter=data,frequency=freq)

        return self._data

    def screen(self,condition,data,freq):
        self._screen_result = []
        par = []
        for i in data:
            tup = (condition,i)
            par.append(tup)

        self.threadpool(self._screen_thread,freq,par)

        return self._screen_result

    def download(self,freq,data,path=''):
        par = []
        for i in data:
            tup = (i['name'],i['urls'],i['id'],path)
            par.append(tup)
        self.threadpool(self._download_thread,freq,par)