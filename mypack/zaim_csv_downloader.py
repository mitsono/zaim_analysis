import time
import configparser
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas
import selenium_util


class ZaimCsvDownloader(object):

    DL_BALANCE_PATH = '../work/zaim/dl_balance.csv'

    def __init__(self, start_date, end_date):

        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        self.id_ = inifile.get('zaim', 'login_id')
        self.pass_ = inifile.get('zaim', 'login_pass')
        self.start_date = start_date
        self.end_date = end_date
        self.encode_str = 'utf8'
        self.driver = self.__create_driver()
        self.__login()
        time.sleep(5)

    def __create_driver(self):

        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        dl_dir = inifile.get('chrome', 'dl_dir')
        # dl_dir = 'C:\\Users\mitsono\Downloads'
        return selenium_util.create_chrome_driver(dl_dir, True)

    def __login(self):
        self.driver.get('https://auth.zaim.net')
        self.driver.find_element_by_name(
            'data[User][email]').send_keys(self.id_)
        self.driver.find_element_by_name(
            'data[User][password]').send_keys(self.pass_)
        self.driver.find_element_by_xpath(
            "//*[@id='UserLoginForm']/div[4]/input").click()

    def download_zaim_csvfile(self):

        self.__downloadcsv()
        time.sleep(30)
        self.__save_balance_csv()

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

    def __save_balance_csv(self):
        self.driver.get('https://zaim.net/home')

        page = self.driver.page_source.encode('utf-8')
        html = BeautifulSoup(page, "lxml")
        p_div = html.find('div', attrs={'id': 'list-accounts'})
        c_divs = p_div.find_all('div', recursive=False)

        bl_title_list = []
        bl_value_list = []

        for c_div in c_divs:

            c_img_t = c_div.find('img', attrs={'data-title': True})
            if c_img_t is None:
                continue
            title = c_img_t['data-title']

            c_div_name = c_div.find('div', attrs={'class': 'value plus'})
            if c_div_name is None:
                continue
            value = c_div_name.text.replace("\n", "").replace(
                ",", "").replace(chr(165), "")

            if title in bl_title_list:
                title += "2"

            bl_title_list += [title]
            bl_value_list += [value]

        bl_df = pandas.DataFrame(
            data={'口座': bl_title_list, '残高': bl_value_list}, columns={'口座', '残高'})

        bl_df.to_csv(path_or_buf=self.DL_BALANCE_PATH,
                     encoding="utf-8", index=False)


def main():
    today_date = date.today()
    current_start_date = today_date.replace(day=1)
    last_end_date = current_start_date - relativedelta(days=1)
    last_start_date = last_end_date.replace(day=1)

    zdl = ZaimCsvDownloader(last_start_date, today_date)
    zdl.download_zaim_csvfile()


if __name__ == '__main__':
    main()
