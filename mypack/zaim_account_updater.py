import time
import configparser
import selenium_util
import selenium
import datetime
from bs4 import BeautifulSoup
import linepush


class ZaimAccountUpdater(object):

    IGNORE_TITLE_LIST = ("Yahoo! JAPAN カード")

    def __init__(self):

        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        self.id_ = inifile.get('zaim', 'login_id')
        self.pass_ = inifile.get('zaim', 'login_pass')
        self.encode_str = 'utf8'
        self.driver = self.__create_driver()
        self.__login()
        time.sleep(5)

    def __create_driver(self):

        return selenium_util.create_chrome_driver("", True)

    def __login(self):
        self.driver.get('https://auth.zaim.net')
        self.driver.find_element_by_name(
            'data[User][email]').send_keys(self.id_)
        self.driver.find_element_by_name(
            'data[User][password]').send_keys(self.pass_)
        self.driver.find_element_by_xpath(
            "//*[@id='UserLoginForm']/div[4]/input").click()

    def update(self):

        check_time = datetime.datetime.now() - datetime.timedelta(minutes=15)
        self.__exec_update()
        time.sleep(10 * 60)
        error_list = self.__check(check_time)

        snd_str = []
        snd_str.append("銀行・カード連携更新完了\n")

        if len(error_list) == 0:
            snd_str.append("エラーなし\n")
        else:
            snd_str.append("\n■未更新リスト\n")
            for error in error_list:
                snd_str.append("{} {}\n".format(
                    error[1].strftime("%m/%d %H:%M"), error[0]))
        return "".join(snd_str)

    def __exec_update(self):

        self.driver.get('https://zaim.net/online_accounts')
        ele_tbl = self.driver.find_element_by_id("online-accounts")
        ele_divs = ele_tbl.find_elements_by_xpath(".//div[@class='dropdown']")
        try_cnt = len(ele_divs)
        err_cnt = 0

        for i in range(try_cnt):
            try:
                time.sleep(5)
                self.driver.get('https://zaim.net/online_accounts')
                ele_tbl = self.driver.find_element_by_id("online-accounts")
                ele_divs = ele_tbl.find_elements_by_xpath(
                    ".//div[@class='dropdown']")
                ele_divs[i].find_element_by_xpath(".//a").click()
                ele_divs[i].find_element_by_xpath(
                    ".//input[@name='commit']").click()
            except selenium.common.exceptions.StaleElementReferenceException:
                err_cnt += 1

        if err_cnt > 0:
            print("try_cnt:{} err_cnt:{}".format(try_cnt, err_cnt))

    def __check(self, check_dt):
        self.driver.get('https://zaim.net/online_accounts')
        page = self.driver.page_source.encode('utf-8')
        html = BeautifulSoup(page, "lxml")

        p_tbl = html.find('table', attrs={'id': 'online-accounts'})
        trs = p_tbl.findAll('tr')

        error_list = []
        for i in range(1, len(trs)):
            td_name = trs[i].find('td', attrs={'class': 'name'})
            title = td_name.find('strong').text
            update_str = td_name.find(
                'div', attrs={'class': 'text-muted'}).text
            update_str = update_str.replace("\n", "").replace("最終更新 : ", "")
            update_str = update_str[:16]
            update_dt = datetime.datetime.strptime(
                update_str, '%Y/%m/%d %H:%M')
            if update_dt < check_dt and title not in self.IGNORE_TITLE_LIST:
                error_list += [(title, update_dt)]

        return error_list


def main():

    zau = ZaimAccountUpdater()
    # print(zau.update())
    linepush.pushMessage(zau.update())


if __name__ == '__main__':
    main()
