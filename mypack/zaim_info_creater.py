import configparser
import numpy as np
from datetime import date
import datetime
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

    def __get_stdout_2(self, title, df_tran, key, value, rjust_num):

        df_wk = df_tran.copy()
        # 万単位に変換
        df_wk[value] = round(df_wk[value] / 10000, 1)

        # 出力
        ret_str = []
        ret_str.append("＜{}＞\n".format(title))
        for index, row in df_wk.iterrows():

            wk_value = str(row[value]).rjust(4)
            wk_key = row[key]
            ret_str.append("{} {}\n".format(wk_value, wk_key))

        return "".join(ret_str)

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

        # 詳細出力対象のみ出力
        df_wk = df_wk.loc[df_wk["詳細出力フラグ"] == 1]

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

        # # 固定費
        # ret_str.append("\n■固定費\n")
        # df_wk_fix = df_wk.loc[df_wk[display_name].str.contains("_固_")]
        # ret_str.append(self._ZaimInfoCreater__get_userate_str(
        #     df_wk_fix, key, value, display_name, sort, buget, vsbuget))

        df_wk_fix_var = df_wk.loc[~df_wk[display_name].str.contains("_固_")]
        df_wk_fix_var = df_wk_fix_var.sort_values([vsbuget])
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

    def __get_category_average(self, mst_df, tran_df):
        # 支出毎に直近3ヵ月、6ヵ月、12ヵ月の支出平均を算出
        three_months_ago_m = self.end_date.month - 3
        three_months_ago_y = self.end_date.year
        if three_months_ago_m < 1:
            three_months_ago_m = three_months_ago_m + 12
            three_months_ago_y = three_months_ago_y - 1
        three_months_ago = date(
            three_months_ago_y, three_months_ago_m, 1)

        six_months_ago_m = self.end_date.month - 6
        six_months_ago_y = self.end_date.year
        if six_months_ago_m < 1:
            six_months_ago_m = six_months_ago_m + 12
            six_months_ago_y = six_months_ago_y - 1
        six_months_ago = date(
            six_months_ago_y, six_months_ago_m, 1)
        one_years_ago = date(
            self.end_date.year - 1, self.end_date.month, 1)

        last_end_date_str = self.last_end_date.strftime("%Y/%m/%d")
        three_months_ago_str = three_months_ago.strftime("%Y/%m/%d")
        six_months_ago_str = six_months_ago.strftime("%Y/%m/%d")
        one_years_ago_str = one_years_ago.strftime("%Y/%m/%d")

        ret_df = pandas.DataFrame(
            columns=["カテゴリ", "3ヵ月平均", "6ヵ月平均", "12ヵ月平均", "12ヵ月予実割合"])

        for index, row in mst_df.iterrows():

            # カテゴリ・先月末以前で抽出
            loop_tran_df = tran_df.loc[tran_df["カテゴリ"]
                                       == row["カテゴリ"]]
            loop_tran_df = loop_tran_df.loc[loop_tran_df["日付"]
                                            <= last_end_date_str]

            # 3ヵ月分
            wk_df = loop_tran_df.loc[loop_tran_df["日付"]
                                     >= three_months_ago_str]
            three_months_ave = round(wk_df.sum()["支出"]/3, 0)

            # 6ヵ月分
            wk_df = loop_tran_df.loc[loop_tran_df["日付"]
                                     >= six_months_ago_str]
            six_months_ave = round(wk_df.sum()["支出"]/6, 0)

            # 12ヵ月分
            wk_df = loop_tran_df.loc[loop_tran_df["日付"]
                                     >= one_years_ago_str]
            one_years_ave = round(wk_df.sum()["支出"] / 12, 0)

            # 12ヵ月予実割合
            if row["予算"] > 0:
                one_years_vs_budget = round(
                    one_years_ave / row["予算"] * 100, 0)
            else:
                one_years_vs_budget = 999

            # 行追加
            ret_df = ret_df.append(
                {"カテゴリ": row["カテゴリ"], "3ヵ月平均": three_months_ave, "6ヵ月平均": six_months_ave, "12ヵ月平均": one_years_ave, "12ヵ月予実割合": one_years_vs_budget}, ignore_index=True)

        return ret_df

    def __get_total_spend_average(self, total_tran_df):

        wk_df = total_tran_df.copy()
        # ソート
        wk_df = wk_df.sort_values("日付", ascending=True)
        ret_df = pandas.DataFrame(columns=["日付", "支出"])

        for index, row in wk_df.iterrows():

            start_date = datetime.datetime.strptime(row["日付"], "%Y/%m/%d")
            end_date = date(
                start_date.year + 1, start_date.month, 1)
            end_date = end_date - relativedelta(days=1)

            start_date_str = start_date.strftime("%Y/%m/%d")
            end_date_str = end_date.strftime("%Y/%m/%d")

            loop_df = wk_df.loc[wk_df["日付"] >= start_date_str]
            loop_df = loop_df.loc[wk_df["日付"] <= end_date_str]

            # 12ヵ月平均のレコードを生成
            date_value = end_date_str
            ave_value = round(loop_df["支出"].sum() / 12, 0)

            ret_df = ret_df.append(
                {"日付": date_value, "支出": ave_value}, ignore_index=True)

            if wk_df["日付"].max() < end_date_str:
                break

        return ret_df

    def get_merge_category_total(self):

        wk_tran_df = self.df_tran_merge_category.copy()

        # 合計支出推移
        wk_total_df = wk_tran_df.groupby("日付").sum()["支出"].reset_index()

        # # 出力
        ret_str = []

        # 合計支出推移の出力
        wk_total_df = wk_total_df.sort_values(["日付"])
        total_spend_str = self.__get_stdout_2(
            "合計支出推移", wk_total_df, "日付", "支出", 4)
        ret_str.append(total_spend_str)
        ret_str.append("\n")

        return "".join(ret_str)

    def get_merge_category_total_ave(self):

        wk_tran_df = self.df_tran_merge_category.copy()

        # 合計支出推移
        wk_total_df = wk_tran_df.groupby("日付").sum()["支出"].reset_index()

        # 12ヵ月平均合計支出
        wk_total_ave_df = self.__get_total_spend_average(wk_total_df)

        # # 出力
        ret_str = []

        # 合計支出（12ヵ月平均）推移の出力
        wk_total_ave_df = wk_total_ave_df.sort_values(["日付"])
        total_ave_str = self.__get_stdout_2(
            "合計支出（12ヵ月平均）推移", wk_total_ave_df, "日付", "支出", 4)
        ret_str.append(total_ave_str)
        ret_str.append("\n")

        return "".join(ret_str)

    def get_merge_category_cate(self):

        wk_mst_df = self.df_mst_category.copy()
        wk_tran_df = self.df_tran_merge_category.copy()

        # 支出毎に直近3ヵ月、6ヵ月、12ヵ月の支出平均を算出
        wk_ave_df = self.__get_category_average(wk_mst_df, wk_tran_df)

        # 直近12ヵ月分のみ出力
        one_years_ago = date(
            self.end_date.year - 1, self.end_date.month, 1)
        one_years_ago_str = one_years_ago.strftime("%Y/%m/%d")
        wk_tran_df = wk_tran_df.loc[wk_tran_df["日付"]
                                    >= one_years_ago_str]

        # 詳細出力対象のみ出力
        df_wk = wk_mst_df.loc[wk_mst_df["詳細出力フラグ"] == 1]

        # # 出力
        ret_str = []

        # カテゴリ別支出推移の出力
        df_wk = pandas.merge(
            df_wk, wk_ave_df, on=["カテゴリ"], how="inner")
        df_wk = df_wk.sort_values(["ソート順"])

        # 万単位に変換
        df_wk["3ヵ月平均"] = round(df_wk["3ヵ月平均"] / 10000, 1)
        df_wk["6ヵ月平均"] = round(df_wk["6ヵ月平均"] / 10000, 1)
        df_wk["12ヵ月平均"] = round(df_wk["12ヵ月平均"] / 10000, 1)
        df_wk["予算"] = round(df_wk["予算"] / 10000, 1)
        wk_tran_df["支出"] = round(wk_tran_df["支出"] / 10000, 1)

        ret_str.append("＜{}＞\n".format("カテゴリ別支出推移"))
        for index, row in df_wk.iterrows():
            df_wk_loop = wk_tran_df.loc[wk_tran_df["カテゴリ"] == row["カテゴリ"]]
            df_wk_loop = df_wk_loop.sort_values(["日付"])

            ret_str.append("■{}（予算：{}）\n".format(row["カテゴリ"], row["予算"]))
            for index_loop, row_loop in df_wk_loop.iterrows():
                loop_value = str(row_loop["支出"]).rjust(4)
                ret_str.append("{} {}\n".format(
                    loop_value, row_loop["日付"]))

            three_m_value = str(row["3ヵ月平均"]).rjust(4)
            six_m_value = str(row["6ヵ月平均"]).rjust(4)
            one_y_value = str(row["12ヵ月平均"]).rjust(4)
            ret_str.append("{} {} {}\n".format(
                three_m_value, six_m_value, one_y_value))

            ret_str.append("\n")

        return "".join(ret_str)

    def end(self):
        self.df_tran_merge_balance.to_csv(self.TRAN_BALANCE_PATH,
                                          encoding="utf-8", index=False)
        self.df_tran_merge_card.to_csv(self.TRAN_CARD_PATH,
                                       encoding="utf-8", index=False)
        self.df_tran_merge_category.to_csv(self.TRAN_CATEGORY_PATH,
                                           encoding="utf-8", index=False)

    def create_old_tran_category_file(self):

        df_wk1 = self.____get_tran_current_category(
            2, "2020/02/28")
        df_wk2 = self.____get_tran_current_category(
            3, "2020/03/28")
        df_wk3 = self.____get_tran_current_category(
            4, "2020/04/28")
        df_wk4 = self.____get_tran_current_category(
            5, "2020/05/28")
        df_wk5 = self.____get_tran_current_category(
            6, "2020/06/28")
        df_wk6 = self.____get_tran_current_category(
            7, "2020/07/28")
        df_wk7 = self.____get_tran_current_category(
            8, "2020/08/28")
        df_wk8 = self.____get_tran_current_category(
            9, "2020/09/28")
        df_wk9 = self.____get_tran_current_category(
            10, "2020/10/28")
        df_wk10 = self.____get_tran_current_category(
            11, "2020/11/28")
        df_wk11 = self.____get_tran_current_category(
            12, "2020/12/28")
        df_wk12 = self.____get_tran_current_category(
            1, "2021/01/28")

        df_wk = df_wk1.copy()
        df_wk = df_wk.append(
            df_wk2, ignore_index=True)
        df_wk = df_wk.append(
            df_wk3, ignore_index=True)
        df_wk = df_wk.append(
            df_wk4, ignore_index=True)
        df_wk = df_wk.append(
            df_wk5, ignore_index=True)
        df_wk = df_wk.append(
            df_wk6, ignore_index=True)
        df_wk = df_wk.append(
            df_wk7, ignore_index=True)
        df_wk = df_wk.append(
            df_wk8, ignore_index=True)
        df_wk = df_wk.append(
            df_wk9, ignore_index=True)
        df_wk = df_wk.append(
            df_wk10, ignore_index=True)
        df_wk = df_wk.append(
            df_wk11, ignore_index=True)
        df_wk = df_wk.append(
            df_wk12, ignore_index=True)
        df_wk.to_csv(
            self.TRAN_CATEGORY_PATH, encoding="utf-8", index=False)


def main():
    today_date = date.today()
    current_start_date = today_date.replace(day=1)
    last_end_date = current_start_date - relativedelta(days=1)
    last_start_date = last_end_date.replace(day=1)

    zic = ZaimInfoCreater(last_start_date, last_end_date, today_date)

    linepush.pushMessage(zic.get_merge_balance_group())
    linepush.pushMessage(zic.get_merge_category_cate())
    linepush.pushMessage(zic.get_current_balance())
    linepush.pushMessage(zic.get_merge_category_total())
    linepush.pushMessage(zic.get_merge_category_total_ave())
    linepush.pushMessage(zic.get_current_last_category())
    linepush.pushMessage(zic.get_current_category())

    # zic.create_old_tran_category_file()

    # zic.end()


if __name__ == '__main__':
    main()
