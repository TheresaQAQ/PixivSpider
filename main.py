from PyQt5.QtWidgets import QApplication, QMainWindow
from GUI import Ui_MainWindow
from Pixiv import Pixiv
import time
import threading
import sys
import json

class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)
        
        try:
            js = json.load(open('config.json', encoding='utf-8'))
            self.user_name = js['Login']['user_name']
            self.user_password = js['Login']['user_password']
            self.user_cookies = js['Login']['user_cookies']
            self.ban_status = js['Setting']['ban_status']
            self.ban_word = js['Setting']['ban_word']
            self.work_thread = js['Setting']['work_thread']
            self.download_thread = js['Setting']['download_thread']
            self.screening_criteria = js['Setting']['screening_criteria']
        except:
            self.gui.listWidget.addItem('读取配置文件失败')
            self.work = False
        else:
            self.work = True

        self._search_type = {
            '全年龄': 'safe',
            '全部': 'all',
            'R18': 'r18'
        }

        self.gui.button_search_start.clicked.connect(self.search)
        self.gui.button_ranking_start.clicked.connect(self.ranking)


    def _search_thread(self):
        keyword = self.gui.search_tag.toPlainText()
        mode = self._search_type[self.gui.search_type.currentText()]
        start = self.gui.search_startpage.toPlainText()
        finish = self.gui.search_finishpage.toPlainText()
        if keyword != '' and mode != '' and start != '' and finish != '':
            try:
                if int(finish) >= int(start):
                    all_time = 0
                    pixix = Pixiv(self.user_cookies)
                    for i in range(int(start), int(finish)+1):
                        self.gui.listWidget.addItem('正在爬取第{0}页......'.format(i))
                        time1 = time.time()
                        pics = pixix.search(keyword=keyword, mode=mode, search_page=i)
                        if pics != []:
                            new_data = pixix.screen(self.screening_criteria, pics['data'], self.work_thread)
                            pixix.download(freq=self.download_thread, data=new_data, path=pics['path'])
                            time2 = time.time()
                            self.gui.listWidget.addItem('第{0}页完成，用时{1}秒'.format(i, round(time2 - time1),2))
                            all_time = all_time + time2 - time1
                        else:
                            self.gui.listWidget.addItem('第{0}页为空'.format(i))
                    self.gui.listWidget.addItem('{0}到{1}页已完成，共用时{2}秒'.format(start, finish, round(all_time,2)))
                else:
                    self.gui.listWidget.addItem('Error：开始页数不能大于结束页数')
            except ValueError:
                self.gui.listWidget.addItem('Error：请输入数字')
        else:
            self.gui.listWidget.addItem('Error：请输入')

    def search(self):
        if self.work:
            pixiv = Pixiv(self.user_cookies)
            if pixiv.login_status():
                thread = threading.Thread(target=self._search_thread)
                thread.start()
            else:
                self.gui.listWidget.addItem('Error：登录失效')
        else:
            self.gui.listWidget.addItem('读取配置文件出错，无法运行')

    def _ranking_thread(self):
        ranking_type = {
            '今日普通': 'daily',
            '本周普通': 'weekly',
            '本月普通': 'monthly',
            '新人普通': 'rookie',
            '原创普通': 'original',
            '受男性欢迎普通': 'male',
            '受女性欢迎普通': 'female',
            '今日R18': 'daily_r18',
            '本周R18': 'weekly_r18',
            '本月R18': 'monthly_r18',
            '新人R18': 'rookie_r18',
            '原创R18': 'original_r18',
            '受男性欢迎R18': 'male_r18',
            '受女性欢迎R18': 'female_r18'
        }
        mode = ranking_type[self.gui.ranking_type.currentText() + self.gui.ranking_type2.currentText()]
        date = self.gui.ranking_date.toPlainText()
        if mode not in ['weekly_r18', 'monthly_r18', 'monthly', 'weekly']:
            try:
                int(date)
            except ValueError:
                self.gui.listWidget.addItem('Error：请输入数字')
            else:
                pixiv = Pixiv(self.user_cookies)
                time1 = time.time()
                self.gui.listWidget.addItem('正在搜索...')
                pics = pixiv.ranking_list(mode=mode, date=date)
                if pics != []:
                    new_data = pixiv.screen(self.screening_criteria, pics['data'], self.work_thread)
                    time2 = time.time()
                    self.gui.listWidget.addItem('搜索完成，用时{0}秒'.format(round(time2-time1, 2)))
                    self.gui.listWidget.addItem('正在下载...')
                    time1 = time.time()
                    pixiv.download(freq=self.download_thread, data=new_data, path=pics['path'])
                    time2 = time.time()
                    self.gui.listWidget.addItem('下载完成，用时{0}秒'.format(round(time2 - time1, 2)))
                else:
                    self.gui.listWidget.addItem('内容为空！')
        else:
            pixiv = Pixiv(self.user_cookies)
            pics = pixiv.ranking_list(mode=mode, date=date)
            if pics != []:
                new_data = pixiv.screen(self.screening_criteria, pics['data'], self.work_thread)
                self.gui.listWidget.addItem('正在下载...')
                pixiv.download(freq=self.download_thread, data=new_data, path=pics['path'])
            else:
                self.gui.listWidget.addItem('内容为空！')

    def ranking(self):
        if self.work:
            pixiv = Pixiv(self.user_cookies)
            if pixiv.login_status():
                thread = threading.Thread(target=self._ranking_thread)
                thread.start()
            else:
                self.gui.listWidget.addItem('Error：登录失效')
        else:
            self.gui.listWidget.addItem('读取配置文件出错，无法运行')


def main():
    app = QApplication(sys.argv)
    windows = MainWindows()
    windows.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()