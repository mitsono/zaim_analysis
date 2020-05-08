from selenium.webdriver.chrome.options import Options
from selenium import webdriver


def create_chrome_driver(dl_dir, headless_flg):
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--proxy-server="direct://"')
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--start-maximized')

    if headless_flg:
        options.add_argument('--headless')

    driver = webdriver.Chrome(chrome_options=options)
    driver.implicitly_wait(10)

    if headless_flg:
        driver.command_executor._commands["send_command"] = (
            "POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {
            'behavior': 'allow', 'downloadPath': dl_dir}}
        driver.execute("send_command", params)

    return driver
