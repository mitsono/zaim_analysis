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

    balance_str = zic.get_balance()
    lastmonth_userate_str = zic.get_lastmonth_userate()
    currentmonth_userate_str = zic.get_currentmonth_userate()
    diff_userate_str = zic.get_diff_userate()
    summary_str = zic.get_summary()

    linepush.pushMessage(diff_userate_str)
    linepush.pushMessage(summary_str)
    linepush.pushMessage(balance_str)
    linepush.pushMessage(lastmonth_userate_str)
    linepush.pushMessage(currentmonth_userate_str)

    # 終了処理
    zic.end()


if __name__ == '__main__':
    main()
