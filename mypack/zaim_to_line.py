import zaim_csv_downloader
import zaim_info_creater
import linepush
from datetime import date
from dateutil.relativedelta import relativedelta


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
    linepush.pushMessage(zic.get_lastmonth_userate())
    linepush.pushMessage(zic.get_currentmonth_userate())
    linepush.pushMessage(zic.get_diff_userate())
    linepush.pushMessage(zic.get_summary())

    # 終了処理
    zic.end()


if __name__ == '__main__':
    main()
