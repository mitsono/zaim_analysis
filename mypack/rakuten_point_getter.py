import time
import configparser
import selenium_util
from bs4 import BeautifulSoup


class RakutenPoint_Getter(object):

    def __init__(self):
        self.driver = None

    def __create_driver(self):

        return selenium_util.create_chrome_driver("", True)

    def get_point(self):

        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        id_pass_list = []

        id_pass_list += [(inifile.get('rakuten', 'login_id1'),
                          inifile.get('rakuten', 'login_pass1'))]
        id_pass_list += [(inifile.get('rakuten', 'login_id2'),
                          inifile.get('rakuten', 'login_pass2'))]

        ret_str = []
        ret_str.append("■楽天ポイント")
        for id_pass in id_pass_list:

            self.driver = self.__create_driver()
            self.__login(id_pass[0], id_pass[1])
            time.sleep(5)
            tp = self.get_dl_point_tp(id_pass[0])
            time.sleep(5)
            self.driver.quit()

            ret_str.append("id : {}\n".format(id_pass[0]))
            ret_str.append("合計ポイント : {}\n".format(tp[0]))
            ret_str.append("期間限定ポイント : {}\n".format(tp[1]))
            ret_str.append("1ヵ月以内失効ポイント : {}\n".format(
                int(tp[1]) - int(tp[2])))
            ret_str.append("\n")

        return "".join(ret_str)

    def __login(self, id, pw):
        self.driver.get(
            'https://grp02.id.rakuten.co.jp/rms/nid/vc?__event=login&service_id=13&return_url=/')
        self.driver.find_element_by_name(
            'u').send_keys(id)
        self.driver.find_element_by_name(
            'p').send_keys(pw)
        self.driver.find_element_by_name(
            'submit').click()

    def get_dl_point_tp(self, id):
        page = self.driver.page_source.encode('utf-8')
        html = BeautifulSoup(page, "lxml")

        dl = html.find('dl', attrs={'class': 'point-total'})
        dd = dl.find('dd')
        total_point = dd.text.replace(",", "")

        dl = html.find('dl', attrs={'class': 'point-list-sum'})
        dd = dl.find('dd')
        lim_point = dd.text.replace(",", "")

        ul = html.find('ul', attrs={'class': 'point-list-detail'})
        div = ul.find('div', attrs={'class': 'point-cnt'})
        over_1m_ahead_lim_point = div.text.replace(",", "")

        return (total_point, lim_point, over_1m_ahead_lim_point)


def main():

    rpg = RakutenPoint_Getter()
    print(rpg.get_point())


if __name__ == '__main__':
    main()
