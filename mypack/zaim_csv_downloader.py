import time
from selenium import webdriver
import configparser
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from datetime import date
from dateutil.relativedelta import relativedelta


class ZaimCsvDownloader(object):

    def __init__(self, start_date, end_date):

        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        self.id_ = inifile.get('zaim', 'login_id')
        self.pass_ = inifile.get('zaim', 'login_pass')
        self.start_date = start_date
        self.end_date = end_date
        self.encode_str = 'utf8'
        self.driver = self.__create_driver()

    def download_zaim_csvfile(self):

        self.__login()
        time.sleep(5)
        self.__downloadcsv()
        time.sleep(30)

    def __create_driver(self):
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')
        options.add_argument('--start-maximized')
        options.add_argument('--headless')
        driver = webdriver.Chrome(chrome_options=options)
        driver.implicitly_wait(10)

        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        dl_dir = inifile.get('chrome', 'dl_dir')
        # dl_dir = 'C:\\Users\mitsono\Downloads'
        driver.command_executor._commands["send_command"] = (
            "POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {
            'behavior': 'allow', 'downloadPath': dl_dir}}
        driver.execute("send_command", params)

        return driver

    def __login(self):
        self.driver.get('https://auth.zaim.net')
        self.driver.find_element_by_name(
            'data[User][email]').send_keys(self.id_)
        self.driver.find_element_by_name(
            'data[User][password]').send_keys(self.pass_)
        self.driver.find_element_by_xpath(
            "//*[@id='UserLoginForm']/div[4]/input").click()

    def __downloadcsv(self):
        self.driver.get('https://content.zaim.net/home/money')
        self.driver.find_element_by_class_name('title').click()
        Select(self.driver.find_element_by_name(
            'data[Money][start_date][year]')).select_by_value(self.start_date.strftime("%Y"))
        Select(self.driver.find_element_by_name(
            'data[Money][start_date][month]')).select_by_value(self.start_date.strftime("%m"))
        Select(self.driver.find_element_by_name(
            'data[Money][start_date][day]')).select_by_value(self.start_date.strftime("%d"))
        Select(self.driver.find_element_by_name(
            'data[Money][end_date][year]')).select_by_value(self.end_date.strftime("%Y"))
        Select(self.driver.find_element_by_name(
            'data[Money][end_date][month]')).select_by_value(self.end_date.strftime("%m"))
        Select(self.driver.find_element_by_name(
            'data[Money][end_date][day]')).select_by_value(self.end_date.strftime("%d"))
        Select(self.driver.find_element_by_name(
            'data[Money][charset]')).select_by_value(self.encode_str)
        self.driver.find_element_by_xpath(
            "//form[@id='MoneyHomeIndexForm']/div[@class='submit']/input").click()


def main():
    today_date = date.today()
    current_start_date = today_date.replace(day=1)
    last_end_date = current_start_date - relativedelta(days=1)
    last_start_date = last_end_date.replace(day=1)

    zdl = ZaimCsvDownloader(last_start_date, today_date)
    zdl.download_zaim_csvfile()


if __name__ == '__main__':
    main()
