import configparser
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
import glob
import os
import pandas
import linepush
import calendar


class ZaimInfoCreater(object):

    WORK_DIR = '../work/zaim'

    DL_FILE_PREFIX = 'Zaim'
    DL_BALANCE_PATH = WORK_DIR + '/dl_balance.csv'
    DL_BALANCE_FIX_PATH = WORK_DIR + '/dl_balance_fix.csv'

    MST_BALANCE_PATH = WORK_DIR + '/mst_balance.csv'
    MST_BALANCE_GROUP_PATH = WORK_DIR + '/mst_balance_group.csv'
    MST_CARD_PATH = WORK_DIR + '/mst_card.csv'
    MST_CARD_GROUP_PATH = WORK_DIR + '/mst_card_group.csv'
    MST_CATEGORY_PATH = WORK_DIR + '/mst_category.csv'
    MST_CATEGORY_GROUP_PATH = WORK_DIR + '/mst_category_group.csv'

    TRAN_BALANCE_PATH = WORK_DIR + '/tran_balance.csv'
    TRAN_CARD_PATH = WORK_DIR + '/tran_card.csv'
    TRAN_CATEGORY_PATH = WORK_DIR + '/tran_category.csv'

    def __init__(self, start_date, last_end_date, end_date):
        self.start_date = start_date
        self.last_end_date = last_end_date
        self.end_date = end_date

        # DLファイル
        self.df_dl_zaim = None
        self.df_dl_balance = None
        self.df_dl_balance_fix = None

        # マスタファイル
        self.df_mst_balance = None
        self.df_mst_balance_group = None
        self.df_mst_card = None
        self.df_mst_card_group = None
        self.df_mst_category = None
        self.df_mst_category_group = None

        # 前回トランファイル
        self.df_tran_before_balance = None
        self.df_tran_before_card = None
        self.df_tran_before_category = None

        # 今回のトランファイル
        self.df_tran_current_balance = None
        self.df_tran_current_card = None
        self.df_tran_current_category = None
        self.df_tran_current_last_category = None

        # マージ済トランファイル
        self.df_tran_merge_balance = None
        self.df_tran_merge_card = None
        self.df_tran_merge_category = None

        #  ファイル読み込み
        self.__read_file()
        # 今回のトランファイル設定
        self.____set_tran_current_balance()
        self.____set_tran_current_card()
        self.____set_tran_current_category()
        # マージ済トランファイル設定
        self.__set_tran_merge()

    def __read_file(self):

        # DLファイル
        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        dl_dir = inifile.get('chrome', 'dl_dir')
        list_of_files = glob.glob(
            dl_dir + '/' + self.DL_FILE_PREFIX + '*')
        cur_run_csv_path = max(list_of_files, key=os.path.getctime)
        self.df_dl_zaim = pandas.read_csv(
            cur_run_csv_path, index_col="日付", parse_dates=True)
        self.df_dl_balance = pandas.read_csv(self.DL_BALANCE_PATH)
        self.df_dl_balance_fix = pandas.read_csv(self.DL_BALANCE_FIX_PATH)

        # マスタファイル
        self.df_mst_balance = pandas.read_csv(self.MST_BALANCE_PATH)
        self.df_mst_balance_group = pandas.read_csv(
            self.MST_BALANCE_GROUP_PATH)
        self.df_mst_card = pandas.read_csv(self.MST_CARD_PATH)
        self.df_mst_card_group = pandas.read_csv(self.MST_CARD_GROUP_PATH)
        self.df_mst_category = pandas.read_csv(self.MST_CATEGORY_PATH)
        self.df_mst_category_group = pandas.read_csv(
            self.MST_CATEGORY_GROUP_PATH)

        # 前回トランファイル
        self.df_tran_before_balance = pandas.read_csv(self.TRAN_BALANCE_PATH)
        self.df_tran_before_card = pandas.read_csv(self.TRAN_CARD_PATH)
        self.df_tran_before_category = pandas.read_csv(self.TRAN_CATEGORY_PATH)

        # 前回トランファイルから今回分削除
        start_date_str = self.start_date.strftime("%Y/%m/%d")
        last_15_date_str = self.start_date.replace(day=15).strftime("%Y/%m/%d")
        self.df_tran_before_balance = self.df_tran_before_balance.loc[
            self.df_tran_before_balance["日付"] <= last_15_date_str]
        self.df_tran_before_card = self.df_tran_before_card.loc[
            self.df_tran_before_card["日付"] < start_date_str]
        self.df_tran_before_category = self.df_tran_before_category.loc[
            self.df_tran_before_category["日付"] < start_date_str]

    def ____set_tran_current_balance(self):

        df_wk = self.df_dl_balance.copy()
        df_wk = df_wk.append(self.df_dl_balance_fix, ignore_index=True)
        # 日付列追加
        df_wk["日付"] = self.end_date.strftime("%Y/%m/%d")
        self.df_tran_current_balance = df_wk

    def ____set_tran_current_card(self):
        self.df_tran_current_card = self.____get_tran_current_card(
            self.end_date.month, self.end_date.strftime("%Y/%m/%d"))

    def ____get_tran_current_card(self, target_month, date_str):

        # 当月分抽出
        df_wk = self.df_dl_zaim[self.df_dl_zaim.index.month ==
                                target_month]
        # 集計に含めないを除く
        df_wk = df_wk.loc[df_wk["集計の設定"] != "集計に含めない"]
        # 支払元毎に支出を集計
        df_wk = df_wk.groupby("支払元").sum()["支出"].reset_index()
        # 支出が0のデータを除外
        df_wk = df_wk.loc[df_wk["支出"] > 0]
        # 日付列追加
        df_wk["日付"] = date_str
        return df_wk

    def ____set_tran_current_category(self):

        self.df_tran_current_category = self.____get_tran_current_category(
            self.end_date.month, self.end_date.strftime("%Y/%m/%d"))
        self.df_tran_current_last_category = self.____get_tran_current_category(
            self.start_date.month, self.last_end_date.strftime("%Y/%m/%d"))

    def ____get_tran_current_category(self, target_month, date_str):

        # 当月分抽出
        df_wk = self.df_dl_zaim[self.df_dl_zaim.index.month ==
                                target_month]
        # 集計に含めないを除く
        df_wk = df_wk.loc[df_wk["集計の設定"] != "集計に含めない"]
        # 支払元毎に支出を集計
        df_wk = df_wk.groupby("カテゴリ").sum()["支出"].reset_index()
        # 支出が0のデータを除外
        df_wk = df_wk.loc[df_wk["支出"] > 0]
        # 日付列追加
        df_wk["日付"] = date_str
        return df_wk

    def __set_tran_merge(self):

        df_wk = self.df_tran_before_balance.copy()
        self.df_tran_merge_balance = df_wk.append(
            self.df_tran_current_balance, ignore_index=True)

        df_wk = self.df_tran_before_card.copy()
        df_wk_1 = self.____get_tran_current_card(
            self.end_date.month, self.end_date.strftime("%Y/%m/%d"))
        df_wk_2 = self.____get_tran_current_card(
            self.start_date.month, self.last_end_date.strftime("%Y/%m/%d"))
        df_wk = df_wk.append(
            df_wk_1, ignore_index=True)
        self.df_tran_merge_card = df_wk.append(
            df_wk_2, ignore_index=True)

        df_wk = self.df_tran_before_category.copy()
        df_wk = df_wk.append(
            self.df_tran_current_category, ignore_index=True)
        self.df_tran_merge_category = df_wk.append(
            self.df_tran_current_last_category, ignore_index=True)

    def __get_stdout(self, title, df_tran, df_mst, key, value):

        display_name = "表示名"
        sort = "ソート順"

        # マスタ紐づけ
        df_wk = pandas.merge(
            df_tran, df_mst, on=[key], how="inner")
        # 表示名で集計
        df_wk = df_wk.groupby([display_name], as_index=False).agg(
            {value: 'sum', sort: 'max'})
        # 万単位に変換
        df_wk[value] = round(df_wk[value] / 10000, 1)

        # 出力
        ret_str = []
        ret_str.append("＜{}＞\n".format(title))
        for index, row in df_wk.iterrows():

            wk_value = str(row[value]).rjust(4)
            wk_display_name = row[display_name]
            ret_str.append("{} {}\n".format(wk_value, wk_display_name))

        return "".join(ret_str)

    def __get_merge_stdout(self, title, df_tran, df_mst, key, value):

        display_name = "表示名"
        date = "日付"
        sort = "ソート順"

        # マスタ紐づけ
        df_wk = pandas.merge(
            df_tran, df_mst, on=[key], how="inner")
        # 表示名で集計
        df_wk = df_wk.groupby([display_name, date], as_index=False).agg(
            {value: 'sum', sort: 'max'})
        # 万単位に変換
        df_wk[value] = round(df_wk[value] / 10000, 1)

        # ループ用データセット生成
        df_wk_mst = df_mst.copy()
        df_wk_mst = df_wk_mst.groupby([display_name], as_index=False).agg(
            {sort: 'max'})
        df_wk_mst = df_wk_mst.sort_values([sort])

        # 出力
        ret_str = []
        ret_str.append("＜{}＞\n".format(title))
        for index, row in df_wk_mst.iterrows():

            # 見出し
            ret_str.append("■{}\n".format(row[display_name]))

            df_wk_loop = df_wk.loc[df_wk[display_name] == row[display_name]]
            df_wk_loop = df_wk_loop.sort_values([date])

            for index_loop, row_loop in df_wk_loop.iterrows():
                ret_str.append("{} {}\n".format(
                    row_loop[value], row_loop[date]))

            ret_str.append("\n")

        return "".join(ret_str)

    def __get_userate_str(self, df_wk, key, value, display_name, sort, buget, vsbuget):

        ret_str = []

        for index, row in df_wk.iterrows():

            if np.isinf(row[vsbuget]):
                rate = "-"
            else:
                rate = int(row[vsbuget])
            rate = str(rate) + "%"
            rate = rate.rjust(5)

            perform = row[value]
            perform = str(perform).rjust(4)

            budget = row[buget]
            budget = str(budget).rjust(4)

            category = row[display_name]
            ret_str.append("{} {} / {} {}\n".format(rate,
                                                    perform, budget, category))

        return "".join(ret_str)

    def __get_over_budget_str(self, df_wk_gr_high, std_userate, key, value, display_name, sort, buget, vsbuget):
        ret_str = []
        df_wk_gr = df_wk_gr_high

        df_wk_gr["中途予算"] = df_wk_gr[buget] * std_userate / 100
        df_wk_gr["超過金額"] = df_wk_gr[value] - df_wk_gr["中途予算"]

        # ソート
        df_wk_gr = df_wk_gr.sort_values("超過金額", ascending=False)

        over_budget_sum = df_wk_gr["超過金額"].sum()
        ret_str.append("\n ＜予算超過：{}＞\n".format(round(over_budget_sum, 1)))
        for index, row in df_wk_gr.iterrows():

            over_budget = row["超過金額"]
            over_budget = str(round(over_budget, 1)).rjust(4)

            perform = row[value]
            perform = str(round(perform, 1)).rjust(4)

            budget = row["中途予算"]
            budget = str(round(budget, 1)).rjust(4)

            category = row[display_name]

            ret_str.append("　{} {} / {} {}\n".format(over_budget,
                                                     perform, budget, category))
        return "".join(ret_str)

    def __get_category_stdout(self, use_rate, df_tran, df_mst, date, key, value):

        display_name = "表示名"
        sort = "ソート順"
        buget = "予算"
        vsbuget = "予実"

        # マスタ紐づけ
        df_wk = pandas.merge(
            df_tran, df_mst, on=[key], how="inner")
        # 表示名で集計
        df_wk = df_wk.groupby([display_name], as_index=False).agg(
            {value: 'sum', sort: 'max', buget: 'max'})
        # 万単位に変換
        df_wk[value] = round(df_wk[value] / 10000, 1)
        df_wk[buget] = round(df_wk[buget] / 10000, 1)
        #  予実列追加
        df_wk[vsbuget] = df_wk[value] / df_wk[buget] * 100

        # 出力
        ret_str = []

        # 見出し出力
        ret_str.append("{}月 目安使用率：{}%\n".format(
            date.month, use_rate))
        # 支出合計
        sum_spending = df_wk[value].sum()
        ret_str.append("支出合計：{}\n".format(
            sum_spending))

        # 固定費
        ret_str.append("\n■固定費\n")
        df_wk_fix = df_wk.loc[df_wk[display_name].str.contains("_固_")]
        ret_str.append(self._ZaimInfoCreater__get_userate_str(
            df_wk_fix, key, value, display_name, sort, buget, vsbuget))

        df_wk_fix_var = df_wk.loc[~df_wk[display_name].str.contains("_固_")]
        # 標準未満
        ret_str.append("\n■順調\n")
        df_wk_low = df_wk_fix_var.loc[df_wk_fix_var[vsbuget] <= use_rate]
        ret_str.append(self._ZaimInfoCreater__get_userate_str(
            df_wk_low, key, value, display_name, sort, buget, vsbuget))

        # 標準以上
        ret_str.append("\n■やばし\n")
        df_wk_high = df_wk_fix_var.loc[df_wk_fix_var["予実"] > use_rate]
        ret_str.append(self._ZaimInfoCreater__get_userate_str(
            df_wk_high, key, value, display_name, sort, buget, vsbuget))
        ret_str.append(self._ZaimInfoCreater__get_over_budget_str(
            df_wk_high, use_rate, key, value, display_name, sort, buget, vsbuget))

        return "".join(ret_str)

    def get_current_balance(self):
        str_a = self.__get_stdout("当月資産",
                                  self.df_tran_current_balance, self.df_mst_balance, "口座", "残高")
        return str_a

    def get_current_card(self):
        str_a = self.__get_stdout("当月カード利用",
                                  self.df_tran_current_card, self.df_mst_card, "支払元", "支出")
        return str_a

    def get_current_category(self):
        month_range = calendar.monthrange(
            self.end_date.year, self.end_date.month)[1]
        use_rate = round(self.end_date.day / month_range * 100, 0)
        str_a = self.__get_category_stdout(use_rate,
                                           self.df_tran_current_category, self.df_mst_category, self.end_date, "カテゴリ", "支出")
        return str_a

    def get_current_last_category(self):
        use_rate = 100
        str_a = self.__get_category_stdout(use_rate,
                                           self.df_tran_current_last_category, self.df_mst_category, self.last_end_date, "カテゴリ", "支出")
        return str_a

    def get_merge_balance_group(self):
        str_a = self.__get_merge_stdout("カテゴリ別資産推移",
                                        self.df_tran_merge_balance, self.df_mst_balance_group, "口座", "残高")
        return str_a

    def get_merge_card_group(self):
        str_a = self.__get_merge_stdout("カテゴリ別カード利用推移",
                                        self.df_tran_merge_card, self.df_mst_card_group, "支払元", "支出")
        return str_a

    def get_merge_category_group(self):
        str_a = self.__get_merge_stdout("カテゴリ別支出推移",
                                        self.df_tran_merge_category, self.df_mst_category_group, "カテゴリ", "支出")
        return str_a

    def end(self):
        self.df_tran_merge_balance.to_csv(self.TRAN_BALANCE_PATH,
                                          encoding="utf-8", index=False)
        self.df_tran_merge_card.to_csv(self.TRAN_CARD_PATH,
                                       encoding="utf-8", index=False)
        self.df_tran_merge_category.to_csv(self.TRAN_CATEGORY_PATH,
                                           encoding="utf-8", index=False)


def main():
    today_date = date.today()
    current_start_date = today_date.replace(day=1)
    last_end_date = current_start_date - relativedelta(days=1)
    last_start_date = last_end_date.replace(day=1)

    zic = ZaimInfoCreater(last_start_date, last_end_date, today_date)

    # print(zic.get_merge_balance_group())
    # print(zic.get_merge_card_group())
    # print(zic.get_merge_category_group())
    # print(zic.get_current_balance())
    # print(zic.get_current_card())
    print(zic.get_current_last_category())
    print(zic.get_current_category())

    zic.end()


if __name__ == '__main__':
    main()
