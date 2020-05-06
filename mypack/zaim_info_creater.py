import configparser
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
import shutil
import glob
import os
import pandas
import calendar


class ZaimInfoCreater(object):

    WORK_DIR = '../work/zaim'
    DL_FILE_PREFIX = 'Zaim'
    MST_BUDGET_PATH = WORK_DIR + '/mst_budget_by_category.csv'
    TRAN_USERATE_PATH = WORK_DIR + '/tran_userate.csv'
    DL_BALANCE_PATH = WORK_DIR + '/dl_balance.csv'
    DL_BALANCE_DC_PATH = WORK_DIR + '/dl_balance_dc.csv'
    DL_BALANCE_INS_PATH = WORK_DIR + '/dl_balance_ins.csv'
    MST_BALANCE_PATH = WORK_DIR + '/mst_balance.csv'
    TRAN_BALANCE = WORK_DIR + '/tran_balance.csv'
    MST_CARD_PATH = WORK_DIR + '/mst_card.csv'

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

        # 前回実行時のファイルパス
        list_of_files = glob.glob(
            self.WORK_DIR + '/' + self.DL_FILE_PREFIX + '*')
        self.last_run_csv_path = max(list_of_files, key=os.path.getctime)

        # 今回処理対象とするファイルパス
        inifile = configparser.ConfigParser()
        inifile.read('../config.ini', 'UTF-8')
        dl_dir = inifile.get('chrome', 'dl_dir')
        list_of_files = glob.glob(
            dl_dir + '/' + self.DL_FILE_PREFIX + '*')
        self.cur_run_csv_path = max(list_of_files, key=os.path.getctime)

        self.df_cur_csv = None
        self.df_add_csv = None
        self.df_buget_csv = None
        self.df_balance = None
        self.df_tran_balance = None

        self.df_dict = {}
        self.df_balance_af = None

        # ファイル読み込み
        self.__set_dataframe()

    def get_balance(self):
        ret_str = []

        # グループ毎に集計
        df_wk_gr = self.df_balance.groupby("group", as_index=False).agg(
            {'value': 'sum', 'sort': 'max'})

        # sort列でソート
        df_wk_gr = df_wk_gr.sort_values("sort")

        # 万単位に変換
        df_wk_gr["value"] = round(df_wk_gr["value"] / 10000, 1)

        # 分析行追加
        cus_group_list = []
        cus_value_list = []

        # 合計(保険・年金・出資予定除外)
        df_wk1 = self.df_balance.loc[self.df_balance["title"] != "生命保険_由衣"]
        df_wk1 = df_wk1.loc[df_wk1["title"] != "個人年金_由衣"]
        df_wk1 = df_wk1.loc[df_wk1["group"] != "確定拠出_先進国株"]
        df_wk1 = df_wk1.loc[df_wk1["group"] != "確定拠出_国内株"]
        df_wk1 = df_wk1.loc[df_wk1["group"] != "出費予定資金(出産・学費)"]
        sum = round(df_wk1.sum()["value"] / 10000, 1)
        cus_group_list += ["合計(保険・年金・出資予定除外)"]
        cus_value_list += [sum]

        # 証券リスク比率(50%～70%)
        df_wk1 = df_wk_gr.loc[df_wk_gr["group"] == "証券_リスク資産"]
        risk = df_wk1.sum()["value"]
        df_wk1 = df_wk_gr.loc[df_wk_gr["group"] == "証券_無リスク資産"]
        non_risk = df_wk1.sum()["value"]
        rate = round(risk / (risk + non_risk) * 100, 0)
        cus_group_list += ["証券リスク比率(50%～70%)"]
        cus_value_list += [str(rate) + "%"]

        # 確定拠出海外株比率(50%～70%)
        df_wk1 = df_wk_gr.loc[df_wk_gr["group"] == "確定拠出_先進国株"]
        kokusai = df_wk1.sum()["value"]
        df_wk1 = df_wk_gr.loc[df_wk_gr["group"] == "確定拠出_国内株"]
        kokunai = df_wk1.sum()["value"]
        rate = round(kokusai / (kokusai + kokunai) * 100, 0)
        cus_group_list += ["確定拠出海外株比率(50%～70%)"]
        cus_value_list += [str(rate) + "%"]

        # 確定拠出リスク比率(50%～70%)
        df_wk1 = df_wk_gr.loc[df_wk_gr["group"] == "確定拠出_リスク資産"]
        risk = df_wk1.sum()["value"]
        df_wk1 = df_wk_gr.loc[df_wk_gr["group"] == "確定拠出_無リスク資産"]
        non_risk = df_wk1.sum()["value"]
        rate = round(risk / (risk + non_risk) * 100, 0)
        cus_group_list += ["確定拠出リスク比率(50%～70%)"]
        cus_value_list += [str(rate) + "%"]

        # 行追加
        bl_cus = pandas.DataFrame(
            data={'group': cus_group_list, 'value': cus_value_list}, columns={'group', 'value'})
        df_wk_gr = df_wk_gr.append(bl_cus, ignore_index=True)

        # 日付列追加
        df_wk_gr["date"] = self.end_date.strftime("%Y/%m/%d")

        # 退避
        self.df_balance_af = df_wk_gr

        for index, row in df_wk_gr.iterrows():

            # 見出し
            ret_str.append("■{}\n".format(row["group"]))

            # tranファイルから過去データ取得
            df_wk_tran = self.df_tran_balance.loc[self.df_tran_balance["group"]
                                                  == row["group"]]
            df_wk_tran = df_wk_tran.loc[df_wk_tran["date"].str.endswith("/15")]

            # 過去データ date列でソート
            df_wk_tran = df_wk_tran.sort_values("date")

            # 過去データ出力
            for index2, row2 in df_wk_tran.iterrows():
                value = str(row2["value"]).rjust(4)
                ret_str.append("{} {}\n".format(row2["date"], value))

            value = str(row["value"]).rjust(4)
            ret_str.append("{} {}\n".format(row["date"], value))

            ret_str.append("\n")

        return "".join(ret_str)

    def get_lastmonth_userate(self):
        return self.__get_userate(self.start_date.month)

    def get_currentmonth_userate(self):
        return self.__get_userate(self.end_date.month)

    def get_diff_userate(self):
        ret_str = []
        ret_str.append("■前回からの増分\n")

        output_flg = False
        df_last_run = pandas.read_csv(self.TRAN_USERATE_PATH)
        for key in self.df_dict:
            df = self.df_dict[key]
            for index, row in df.iterrows():

                # 月、カテゴリを元に前回実行時のレコードを抽出
                df_last_ex = df_last_run[
                    (df_last_run["月"] == key) & (df_last_run['カテゴリ'] == row["カテゴリ"])]

                if df_last_ex.empty:
                    last_spending = 0
                else:
                    last_spending = df_last_ex["支出"].iloc[0]

                if row["支出"] != last_spending:
                    diff_spending = row["支出"] - last_spending
                    diff_spending = str(
                        round(diff_spending / 10000, 1)).rjust(4)
                    current_spending = str(
                        round(row["支出"] / 10000, 1)).rjust(4)
                    last_spending = str(
                        round(last_spending / 10000, 1)).rjust(4)

                    ret_str.append(
                        "{} {} / {} {}月 {}\n".format(diff_spending, current_spending, last_spending, key, row["カテゴリ"]))

                    output_flg = True
        if not output_flg:
            ret_str.append("なし\n")

        return "".join(ret_str)

    def get_summary(self):
        ret_str = []

        df_add_income = self.df_add_csv.loc[self.df_add_csv["収入"] > 0]
        df_add_spending = self.df_add_csv.loc[self.df_add_csv["支出"] > 0]

        ret_str.append("■新規収入\n")
        if df_add_income["収入"].count() == 0:
            ret_str.append("なし\n")
        else:
            ret_str.append("{}件 {}円\n".format(
                df_add_income["収入"].count(), "{:,}".format(df_add_income["収入"].sum())))

        ret_str.append("\n■新規支出\n")
        if df_add_spending["支出"].count() == 0:
            ret_str.append("なし\n")
        else:
            ret_str.append("{}件 {}円\n".format(
                df_add_spending["支出"].count(), "{:,}".format(df_add_spending["支出"].sum())))

        ret_str.append("\n■個別残高\n")
        df_bal_detail = self.df_balance.loc[self.df_balance["detail_out_flg"] > 0]
        for index, row in df_bal_detail.iterrows():
            value = str(round(row["value"] / 10000, 1)).rjust(5)
            title = row["display_name"]
            ret_str.append("{} {}\n".format(value, title))

        return "".join(ret_str)

    def end(self):

        # 処理済みのファイルをDLフォルダからWORKフォルダへ移動
        shutil.move(self.cur_run_csv_path, self.WORK_DIR)

        # 前回実行時のファイル削除
        os.remove(self.last_run_csv_path)

        # 集計結果をcsvファイルに上書き保存
        df_merge = pandas.DataFrame()
        for key in self.df_dict:
            df = self.df_dict[key]
            df["月"] = key
            df_merge = df_merge.append(df, ignore_index=True)

        df_merge.to_csv(
            path_or_buf=self.TRAN_USERATE_PATH, encoding="utf-8")

        # 資産集計結果をcsvファイルに上書き保存
        df_merge = self.df_tran_balance.append(
            self.df_balance_af, ignore_index=True)
        df_merge.to_csv(
            path_or_buf=self.TRAN_BALANCE, encoding="utf-8")

    def __set_dataframe(self):
        self.df_cur_csv = pandas.read_csv(
            self.cur_run_csv_path, index_col="日付", parse_dates=True)
        df_last_csv = pandas.read_csv(
            self.last_run_csv_path, index_col="日付", parse_dates=True)

        self.df_add_csv = self.__get_add_datafram(
            df_last_csv, self.df_cur_csv)

        self.df_buget_csv = pandas.read_csv(self.MST_BUDGET_PATH)

        df_dl_bal = pandas.read_csv(self.DL_BALANCE_PATH)
        df_dl_bal_dc = pandas.read_csv(self.DL_BALANCE_DC_PATH)
        df_dl_bal_ins = pandas.read_csv(self.DL_BALANCE_INS_PATH)
        df_mst_bal = pandas.read_csv(self.MST_BALANCE_PATH)

        df_dl_merge = df_dl_bal.append(df_dl_bal_dc, ignore_index=True)
        df_dl_merge = df_dl_merge.append(df_dl_bal_ins, ignore_index=True)
        self.df_balance = pandas.merge(
            df_mst_bal, df_dl_merge, on=["title"], how="left")

        df_wk = pandas.read_csv(self.TRAN_BALANCE, index_col=0)

        # 同一日付のデータ除外
        end_date_str = self.end_date.strftime("%Y/%m/%d")
        self.df_tran_balance = df_wk.loc[df_wk["date"] != end_date_str]

        # カード
        self.df_mst_card = pandas.read_csv(self.MST_CARD_PATH)

    def __get_add_datafram(self, df_old, df_new):

        comparison_df = df_old.merge(df_new,
                                     indicator=True,
                                     how='outer')
        diff_df = comparison_df[comparison_df['_merge'] == 'right_only']
        return diff_df

    def __get_userate(self, target_month):

        ret_str = []

        std_userate = self.__get_std_userate(target_month)
        df_wk = self.df_cur_csv

        # 見出し出力
        ret_str.append("{}月 目安使用率：{}%\n".format(
            target_month, int(std_userate)))

        # 対象月のデータを抽出
        df_wk = df_wk[df_wk.index.month == target_month]
        df_target_month = df_wk

        # 集計に含めないを除く
        df_wk = df_wk.loc[df_wk["集計の設定"] != "集計に含めない"]

        # 収支集計出力
        sum_income = round(df_wk["収入"].sum() / 10000, 1)
        sum_spending = round(df_wk["支出"].sum() / 10000, 1)
        sum_diff = sum_income - sum_spending
        ret_str.append("収支：{} ({} - {})\n".format(sum_diff,
                                                  sum_income, sum_spending))

        # カテゴリ毎に支出を集計
        df_wk_gr = df_wk.groupby("カテゴリ").sum()["支出"].reset_index()

        # 支出が0のデータを除外
        df_wk_gr = df_wk_gr.loc[df_wk_gr["支出"] > 0]

        # 予算をジョイン
        df_wk_gr = pandas.merge(
            df_wk_gr, self.df_buget_csv, on=["カテゴリ"], how="left")

        #  予実列追加
        df_wk_gr["予実"] = df_wk_gr["支出"] / df_wk_gr["予算"] * 100

        # ソート
        df_wk_gr = df_wk_gr.sort_values("予実")

        # 辞書に退避
        self.df_dict[target_month] = df_wk_gr

        # 固定費
        ret_str.append("\n■固定費\n")
        df_wk_gr_fix = df_wk_gr.loc[df_wk_gr["カテゴリ"].str.contains("固_")]
        ret_str.append(self.__get_userate_by_category(df_wk_gr_fix))

        df_wk_gr_var = df_wk_gr.loc[~df_wk_gr["カテゴリ"].str.contains("固_")]
        # 標準未満
        ret_str.append("\n■順調\n")
        df_wk_gr_low = df_wk_gr_var.loc[df_wk_gr_var["予実"] <= std_userate]
        ret_str.append(self.__get_userate_by_category(df_wk_gr_low))

        # 標準以上
        ret_str.append("\n■やばし\n")
        df_wk_gr_high = df_wk_gr_var.loc[df_wk_gr_var["予実"] > std_userate]
        ret_str.append(self.__get_userate_by_category(df_wk_gr_high))
        ret_str.append(self.__get_over_budget(df_wk_gr_high, std_userate))

        # 用途不明
        df_add_unknown = df_target_month.loc[df_target_month["カテゴリの内訳"] == "由衣_用途不明"]
        ret_str.append("\n■用途不明\n")
        if df_add_unknown["支出"].count() == 0:
            ret_str.append("なし\n")
        else:
            ret_str.append("{}件 {}円\n".format(
                df_add_unknown["支出"].count(), "{:,}".format(df_add_unknown["支出"].sum())))

        # カードマスタに当該月のデータをjoin
        df_card_join = pandas.merge(
            self.df_mst_card, df_target_month, on=["支払元"], how="left")
        df_card_join = df_card_join.groupby(
            "display_name", as_index=False).agg({'支出': 'sum'})

        # 名称でソーﾄ
        df_card_join = df_card_join.sort_values("display_name")

        ret_str.append("\n■カード利用\n")
        for index, row in df_card_join.iterrows():
            value = str(round(row["支出"] / 10000, 1)).rjust(4)
            title = row["display_name"]
            ret_str.append("{} {}\n".format(value, title))

        return "".join(ret_str)

    def __get_userate_by_category(self, df_wk_gr):
        ret_str = []

        for index, row in df_wk_gr.iterrows():

            if np.isinf(row["予実"]):
                rate = "-"
            else:
                rate = int(row["予実"])
            rate = str(rate) + "%"
            rate = rate.rjust(5)

            perform = round(row["支出"] / 10000, 1)
            perform = str(perform).rjust(4)

            budget = round(row["予算"] / 10000, 1)
            budget = str(budget).rjust(4)

            category = row["カテゴリ"]
            ret_str.append("{} {} / {} {}\n".format(rate,
                                                    perform, budget, category))

        return "".join(ret_str)

    def __get_over_budget(self, df_wk_gr_high, std_userate):
        ret_str = []
        df_wk_gr = df_wk_gr_high

        df_wk_gr["中途予算"] = df_wk_gr["予算"] * std_userate / 100
        df_wk_gr["超過金額"] = df_wk_gr["支出"] - df_wk_gr["中途予算"]

        # ソート
        df_wk_gr = df_wk_gr.sort_values("超過金額", ascending=False)

        over_budget_sum = round(df_wk_gr["超過金額"].sum() / 10000, 1)
        ret_str.append("\n ＜予算超過：{}＞\n".format(over_budget_sum))
        for index, row in df_wk_gr.iterrows():

            over_budget = round(row["超過金額"] / 10000, 1)
            over_budget = str(over_budget).rjust(4)

            perform = round(row["支出"] / 10000, 1)
            perform = str(perform).rjust(4)

            budget = round(row["中途予算"] / 10000, 1)
            budget = str(budget).rjust(4)

            category = row["カテゴリ"]

            ret_str.append("　{} {} / {} {}\n".format(over_budget,
                                                     perform, budget, category))
        return "".join(ret_str)

    def __get_std_userate(self, target_month):
        if target_month == self.end_date.month:
            month_range = calendar.monthrange(
                self.end_date.year, self.end_date.month)[1]
            return self.end_date.day / month_range * 100
        else:
            return 100


def main():
    today_date = date.today()
    current_start_date = today_date.replace(day=1)
    last_end_date = current_start_date - relativedelta(days=1)
    last_start_date = last_end_date.replace(day=1)

    zic = ZaimInfoCreater(last_start_date, today_date)
    print(zic.get_balance())
    print(zic.get_lastmonth_userate())
    print(zic.get_currentmonth_userate())
    print(zic.get_diff_userate())
    print(zic.get_summary())
    # linepush.pushMessage(zic.get_balance())
    # linepush.pushMessage(zic.get_lastmonth_userate())
    # linepush.pushMessage(zic.get_currentmonth_userate())
    # linepush.pushMessage(zic.get_diff_userate())
    # linepush.pushMessage(zic.get_summary())

    # zic.end()


if __name__ == '__main__':
    main()
