from requests_oauthlib import OAuth1Session
import pandas
import configparser

inifile = configparser.ConfigParser()
inifile.read('../config.ini', 'UTF-8')

consumer_key = inifile.get('zaim', 'consumer_key')
consumer_secret = inifile.get('zaim', 'consumer_secret')
callback_url = 'https://www.zaim.net'
base_hostname = 'https://api.zaim.net'

# get parameters
oauth_verifier = inifile.get('zaim', 'oauth_verifier')
access_token = inifile.get('zaim', 'access_token')
access_token_secret = inifile.get('zaim', 'access_token_secret')

# get money
url = base_hostname + '/v2/home/money'
zaim_api = OAuth1Session(client_key=consumer_key,
                         client_secret=consumer_secret,
                         resource_owner_key=access_token,
                         resource_owner_secret=access_token_secret,
                         callback_uri=callback_url,
                         verifier=oauth_verifier
                         )
params = {"mapping": "1", "start_date": "2020-03-01"}
money_dict_list = zaim_api.get(url, params=params).json()["money"]

zaim_api = OAuth1Session(client_key=consumer_key,
                         client_secret=consumer_secret,
                         resource_owner_key=access_token,
                         resource_owner_secret=access_token_secret,
                         callback_uri=callback_url,
                         verifier=oauth_verifier
                         )

# get money
url = base_hostname + '/v2/home/money'
# params = {"mapping": "1", "start_date": "2020-03-01"}
params = {"mapping": "1", "limit": "100"}
money_dlist = zaim_api.get(url, params=params).json()["money"]
money_df = pandas.io.json.json_normalize(money_dlist)
money_df.to_csv("../money.csv")

# get category
url = base_hostname + '/v2/home/category'
params = {"mapping": "1"}
category_dlist = zaim_api.get(url, params=params).json()["categories"]
category_df = pandas.io.json.json_normalize(category_dlist)
category_df.to_csv("../category.csv")

# get genre
url = base_hostname + '/v2/home/genre'
params = {"mapping": "1"}
genre_dlist = zaim_api.get(url, params=params).json()["genres"]
genre_df = pandas.io.json.json_normalize(genre_dlist)
genre_df.to_csv("../genre.csv")

# left outer join
join_df = pandas.merge(money_df, category_df,
                       left_on=['category_id'], right_on=['id'], how='left', suffixes=("_x", "_y"))
join2_df = pandas.merge(join_df, genre_df,
                        left_on=['genre_id'], right_on=['id'], how='left', suffixes=("", "_z"))
join2_df.to_csv("../join.csv")
