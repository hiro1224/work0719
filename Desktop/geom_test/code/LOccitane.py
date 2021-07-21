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

#class

        df = pd.DataFrame(store_info, columns=['store_name', 'address'])
        print(df)
        return df

if __name__ == '__main__':
    try:
        print(os.path.basename(__file__) + 'について処理しています、、、')
        # getStoreInfo()はインスタンスメソッドなのでこのように呼び出します
        df = LOccitane(LOccitane.BASE_URL).getStoreInfo()
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

    # df.to_csv('~/Desktop/geom_test/csv/LOccitane.csv', index=True)
