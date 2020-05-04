import configparser

from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError


inifile = configparser.ConfigParser()
inifile.read('../config.ini', 'UTF-8')

# botのチャンネルトークン
channel_token = inifile.get('line', 'channel_token1')
# 送信先のID
receiver = [inifile.get('line', 'mid1'), inifile.get('line', 'mid2')]
line_bot_api = LineBotApi(channel_token)


def pushMessage(message):
    try:
        line_bot_api.multicast(receiver, TextSendMessage(text=message))
        print("success")
    except LineBotApiError as e:
        print(e)
