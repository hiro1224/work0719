#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import numpy as np
import argparse
from os import path
import pathlib
import time
import sys
import os
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import chromedriver_binary
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(current_dir) + '/../')
from modules.db_util import *
from modules.update_db import *
from modules.detect_diff import *
from modules.slack_util import *
from modules.check_df import *

class KrispyKremeDoughnuts:  # 'Brand'には対象のブランド名をキャメルケースで入れてください
    BASE_URL = "https://krispykreme.jp/store/search/?prefectures%5B%5D="

    def __init__(self, base_url):  # 初期化： インスタンス作成時に自動的に呼ばれる
        self.base_url = base_url

    def getHtmlData(self, url_list):
        '''
        対象ページのhtmlデータを返すメソッド
        Parameters
        ----------
        url_list : list
            urlが格納されたリスト
        Returns
        -------
        html_contents : list
            htmlデータが格納されたリスト
        '''
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        
        html_contents = []
        try:
            for url in url_list:
                driver.get(url)
                time.sleep(2)  # サイトによっては描画に時間がかかるため、適宜変更してください
                html_contents.append(driver.page_source)
                
        except Exception as e:
            print('driver関連のerr msg', e)
        finally:
            driver.quit()
        return html_contents

    def getStoreInfo(self):
        '''
        対象ページの店舗名と住所を返すメソッド
        Returns
        -------
        store_info: DataFrame
            店舗名と住所が格納されたデータフレーム
        '''
        html_contents = []
        html_contents = self.getHtmlData([self.base_url])
        store_info = []

        for html in html_contents:
            soup = BeautifulSoup(html, "html.parser")
            stores = soup.find('ul',{'id':'addressInfo'}).find_all('li',{'class':'addressBox'})
            for store in stores:
                name = store.find('h3',{'class':'ttl'}).text.strip()
                address = ' '.join(store.find('p',{'class':'address'}).text.split('\n'))
                store_info.append((name, address))

        df = pd.DataFrame(store_info, columns=['store_name', 'address'])
        print(df)
        return df

if __name__ == '__main__':
    try:
        print(os.path.basename(__file__) + 'について処理しています、、、')
        # getStoreInfo()はインスタンスメソッドなのでこのように呼び出します
        df = KrispyKremeDoughnuts(KrispyKremeDoughnuts.BASE_URL).getStoreInfo()
        # 「ファイル名.csv」の名前でcsvファイルが生成されます。slackに提出をお願いします。
        # 「$python -f 0」でcsvを生成することができます
        if CheckDf.nullCheck(df):
            df = CheckDf.regex(df)
            brand_id = UpdateDB.getBrandId(os.path.basename(__file__))
            df['brand_id'] = brand_id
            new_brand_df = DetectDiff.extractStoresToUpdate(brand_id, df)
            conn_pg = DBUtil.getConnect()
            insert_brand_stores_df = GeocodingUtil.geocode_address(new_brand_df)
            UpdateDB.updateBrandStores(brand_id, insert_brand_stores_df)
        else:
            SlackUtil(f"""brand_id: {brand_id}の取得結果にnullが含まれています""")
    except BaseException as e:
        t, v, tb = sys.exc_info()
        text = str(traceback.format_exception(t, v, tb))
        text = text + str(traceback.format_tb(e.__traceback__))
        SlackUtil.slackNotify(text)

    # df.to_csv('~/Desktop/geom_test/csv/KrispyKremeDoughnuts.csv', index=True)
