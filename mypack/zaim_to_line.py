import zaim_csv_downloader
import zaim_info_creater
import linepush
from datetime import date
from dateutil.relativedelta import relativedelta
import rakuten_point_getter


def main():
    today_date = date.today()
    current_month_start_date = today_date.replace(day=1)
    last_month_end_date = current_month_start_date - relativedelta(days=1)
    last_month_start_date = last_month_end_date.replace(day=1)

    # zaim csvファイルダウンロード
    zdl = zaim_csv_downloader.ZaimCsvDownloader(
        last_month_start_date, today_date)
    zdl.download_zaim_csvfile()

    # 先月の予実分析をLineに通知
    zic = zaim_info_creater.ZaimInfoCreater(last_month_start_date, today_date)

    linepush.pushMessage(zic.get_merge_balance_group())
    linepush.pushMessage(zic.get_merge_card_group())
    linepush.pushMessage(zic.get_merge_category_group())
    linepush.pushMessage(zic.get_current_balance())
    linepush.pushMessage(zic.get_current_card())
    linepush.pushMessage(zic.get_current_category())

    # 終了処理
    zic.end()

    # 楽天ポイント
    rpg = rakuten_point_getter.RakutenPoint_Getter()
    linepush.pushMessage(rpg.get_point())


if __name__ == '__main__':
    main()
