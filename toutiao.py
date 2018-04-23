import json
from urllib.parse import urlencode

import re

import pymongo
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def get_page_index(offset,keyword):
    data={
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': '3'
    }
    url='https://www.toutiao.com/search_content/?'+urlencode(data)
    try:
        response=requests.get(url)
        if response.status_code==200:
            return response.text
        return None
    except RequestException:
        print('请求页面错误')
        return None

def parse_page_index(html):
    data=json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')

def get_page_detail(url):
    try:
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
        response=requests.get(url,headers=headers)
        if response.status_code==200:
            return response.text
        return None
    except RequestException:
        print('请求详情页错误',url)
        return None

def pares_page_detail(html,url):
    soup=BeautifulSoup(html,'lxml')
    title=soup.select('title')[0].get_text()
    print(title)
    images_pattern=re.compile('gallery: JSON.parse\\((.*?)\\),',re.S)
    result=re.search(images_pattern,html)
    if result:
        data=json.loads(json.loads(result.group(1)))
        print(data)
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images=[item.get('url') for item in sub_images]
            return {
                'title':title,
                'url':url,
                'images':images
            }

def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到MongoDB成功',result)
        return True
    return False

def main():
    html=get_page_index(0,'街拍')
    for url in parse_page_index(html):
        html=get_page_detail(url)
        if html:
            result=pares_page_detail(html,url)
            save_to_mongo(result)

if __name__ == '__main__':
    main()