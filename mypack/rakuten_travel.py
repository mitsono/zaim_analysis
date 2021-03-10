# import time
# import configparser
import sys
import selenium_util
from bs4 import BeautifulSoup
import pandas


class RakutenTravel_Getter(object):

    def __init__(self):
        self.driver = None

    def __create_driver(self):

        return selenium_util.create_chrome_driver("", False)

    def __get_search_name_list(self):

        list = ['あたみ石亭', 'あたみ石亭別邸 桜岡茶寮', '熱海温泉　湯宿一番地', 'うたゆの宿　熱海四季ホテル', '星野リゾート　リゾナーレ熱海', 'ホテルニューさがみや', 'ラビスタ伊豆山', '伊東小涌園', 'ウェルネスの森　伊東', '淘心庵 米屋', '八幡野温泉郷　杜の湯　きらの里', '全室源泉かけ流し露天風呂付の宿　いさり火', '熱川温泉　粋光', 'ホテルカターラリゾート＆スパ', '稲取　銀水荘', 'いなとり荘', '食べるお宿　浜の湯', '伊豆今井浜東急ホテル', '湯回廊　菊屋', '鬼の栖', '京風料亭旅館　正平荘', '海のほてる　いさば', '松濤館', '堂ヶ島ニュー銀水', '絶景の宿　堂ヶ島ホテル天遊', 'ホテル伊豆急', '下田東急ホテル', '季一遊', 'THE HAMANAKO（ザ浜名湖）（旧：浜名湖ロイヤルホテル）', 'ホテルルートイン浜松ディーラー通り', 'ダイワロイネットホテル浜松', 'ホテルルートイン清水インター', 'ホテルルートイン島田吉田インター', 'カンデオホテルズ静岡島田', 'ダイワロイネットホテルぬまづ', '藤乃煌 富士御殿場', 'ホテルルートイン新富士駅南－国道1号バイパス沿-', 'ホテルルートイン富士中央公園東', '富士レークホテル', 'フジプレミアムリゾート', 'ホテルルートイン河口湖', '甲府湯村ホテルＢ＆Ｂ', '秀峰閣湖月', '山岸旅館', 'ホテルルートインコート富士吉田', 'ホテルルートイン山梨中央', 'ホテルルートインコート甲府', 'ホテルルートインコート甲府石和', 'ホテルルートインコート山梨', '星野リゾート　リゾナーレ八ヶ岳', 'ロイヤルホテル 八ヶ岳（旧：大泉高原　八ヶ岳ロイヤルホテル）', 'ホテルルートインコート韮崎', 'ホテルルートインコート南アルプス', 'ホテルルートインコート上野原（旧：ホテルルートインコート相模湖上野原）', '白馬東急ホテル', '軽井沢プリンスホテル（ウエスト）', 'ホテルルートインコート軽井沢', 'ホテルルートインコート佐久', 'ホテルルートインコート小諸', '上田東急REIホテル', 'ホテルルートインGrand上田駅前（旧：ホテルルートイングランド上田駅前）',
                '斎藤ホテル', 'ロイヤルホテル 長野（旧：信州松代ロイヤルホテル）', 'ホテルルートインコート松本インター', 'ホテルルートインコート南松本', 'ホテルルートイン塩尻', 'ホテルルートイン塩尻北インター', '黒部観光ホテル', 'ホテルルートインコート安曇野豊科駅南', 'カンデオホテルズ茅野', 'ホテルルートイン上諏訪', 'ホテルルートイン諏訪インター', 'ホテルルートイン第2諏訪インター', '蓼科東急ホテル', '白樺リゾート池の平ホテル', '中央アルプス眺望の宿　ホテル季の川', 'ホテルートイン駒ヶ根インター', '天然温泉　ホテルルートイン信濃大町駅前（旧：ホテルートイン信濃大町駅前）', 'ホテルルートインコート伊那', 'ホテルルートイン伊那インター', 'ホテルルートイン飯田', '江戸屋', '星野リゾート　界　日光', '鬼怒川温泉ホテル', '鬼怒川金谷ホテル', 'ホテル鬼怒川御苑', '星野リゾート　界　鬼怒川', '祝い宿寿庵', 'TOWAピュアコテージ', 'ロイヤルホテル 那須（旧：那須高原りんどう湖ロイヤルホテル）', 'ウェルネスの森　那須', 'かんすい苑　覚楽', '仙郷', '源泉湯の宿　紫翠亭', '吟松亭 あわしま', '源泉湯の宿　松乃井', '水上館', '源泉湯の宿　千の谷', 'ホテル一井', '湯宿　季の庭', 'お宿　木の葉', '草津温泉　奈良屋', '雀のお宿　磯部館', '花のおもてなし長生館', '龍宮城スパホテル三日月　龍宮亭', '龍宮城スパホテル三日月　富士見亭', 'ホテル＆リゾーツ 南房総（旧：南房総富浦ロイヤルホテル）', '鴨川シーワールドホテル', '潮騒の湯　鴨川館', '鴨川ホテル三日月', '勝浦ホテル三日月', 'マホロバ・マインズ三浦', 'ヒルトン小田原リゾート＆スパ', '川堰苑いすゞホテル', 'ニューウェルシティ湯河原', '湯本富士屋ホテル', '月の宿　紗ら', 'ホテル河鹿荘', '箱根小涌園　天悠', 'うたゆの宿　箱根', '箱根小涌谷温泉　水の音', 'ハイアット リージェンシー 箱根 リゾート＆スパ', '季の湯　雪月花', '季の湯　雪月花別邸　翠雲', '箱根ホテル']
        return list

    def get_info(self):

        # ドライバー生成
        self.driver = self.__create_driver()

        # 検索リスト取得
        list = self.__get_search_name_list()

        # 検索
        mergeDf = pandas.DataFrame()
        for ele in list:
            df = self.__get_info(ele)
            mergeDf = mergeDf.append(df, ignore_index=True)

        mergeDf.to_csv(sys.stdout, sep='|', index=False, header=True)

        return ""

    def __get_info(self, search_name):

        rate = ""
        reviewCount = ""
        price = ""
        city = ""

        # TOPページ表示
        self.driver.get(
            'https://travel.rakuten.co.jp/')
        # time.sleep(1)

        # 検索
        self.driver.find_element_by_name('f_query').send_keys(search_name)
        self.driver.find_element_by_id('kw-submit').click()

        try:

            # 一覧画面
            # HTML要素取得
            page = self.driver.page_source.encode('utf-8')
            # html = BeautifulSoup(page, "lxml")
            html = BeautifulSoup(page, "html.parser")
            # 価格取得
            priceDl = html.find('dl', attrs={'class': 'price'})
            priceEm = priceDl.find('em')
            price = priceEm.text
            # 町
            citySpan = html.find('span', attrs={'class': 'city'})
            city = citySpan.text

            # 先頭のリンククリック
            # //はルートから検索するという意味。直下から検索ではない。
            # 一度変数に入れた場合は、//を抜くと、変数でとった階層からの検索となる。
            self.driver.find_element_by_xpath(
                "//div[@class='hotelBox']/h2/a").click()

            # 詳細画面
            # HTML要素取得
            page = self.driver.page_source.encode('utf-8')
            # html = BeautifulSoup(page, "lxml")
            html = BeautifulSoup(page, "html.parser")

            # レート取得
            rateMeta = html.find('meta', attrs={'property': 'ratingValue'})
            rate = rateMeta['content']

            # レビュー数取得
            reviewCountA = html.find('a', attrs={'property': 'reviewCount'})
            reviewCount = reviewCountA['content']

        except Exception as e:
            print(e)

        # 返却データフレーム作成
        retDf = pandas.DataFrame(
            {'searchName': search_name, 'rate': rate, 'reviewCount': reviewCount, 'price': price, 'city': city}, index=[1])

        return retDf

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
        if div is None:
            over_1m_ahead_lim_point = "0"
        else:
            over_1m_ahead_lim_point = div.text.replace(",", "")

        return (total_point, lim_point, over_1m_ahead_lim_point)


def main():

    rtg = RakutenTravel_Getter()
    rtg.get_info()


if __name__ == '__main__':
    main()
