import os
import requests
import json
import time
import shutil
import threading

BACKUP_PATH = './backups'
REQ_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'application/json+javascript'
}

if not os.path.exists(BACKUP_PATH):
    os.makedirs(BACKUP_PATH)

# 쿠키 정보 읽기
cookies = {}

def is_kakao_cookie(line):
    return line.startswith('drive.kakao.com') or line.startswith('.kakao.com')

with open('drive.kakao.com_cookies.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()
    cookie_lines = [line for line in lines if is_kakao_cookie(line)]
    for cookie_line in cookie_lines:
        name, value = cookie_line.split('\t')[5:7]
        cookies[name.strip()] = value.strip()

# 요청 및 다운로드

def request_list(url):
    try:
        response = requests.get(url, cookies=cookies, headers=REQ_HEADERS)
        response_json = response.json()
        return response_json
    except Exception as e:
        print('error on request get list', url)
        print(e)
        return None

def request_photo(url):
    try:
        response = requests.get(f'{url}?attach', cookies=cookies, headers=REQ_HEADERS)
        return response.content
    except Exception as e:
        print('error on request get photo', url)
        print(e)
        return None

offset = 0

while True:
    file_list_json = request_list(f'https://drawer-api.kakao.com/mediaFile/list?verticalType=MEDIA&fetchCount=100&joined=true&direction=ASC&offset={offset}')
    
    if not file_list_json or 'items' not in file_list_json or len(file_list_json['items']) == 0:
        break  # 더 이상 받아올 목록이 없음

    timestamp = int(time.time())
    download_path = f'{BACKUP_PATH}/{timestamp}'
    os.makedirs(download_path)

    PHOTO_COUNT = 100
    THREADS_COUNT = 5
    
    def worker(photo_item_list):
        for photo_item in photo_item_list:
            photo = request_photo(photo_item['url'])
            if photo:
                print('download', photo_item['id'])
                with open(f"{download_path}/{photo_item['url'].split('/')[-1]}", 'wb') as f:
                    f.write(photo)

    photo_item_list_list = [[] for _ in range(THREADS_COUNT)]
    
    for index, photo_item in enumerate(file_list_json['items']):
        photo_item_list_list[index % THREADS_COUNT].append(photo_item)
    
    threads = [threading.Thread(target=worker, args=(photo_item_list_list[i],)) for i in range(THREADS_COUNT)]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    shutil.make_archive(f'{download_path}_photo', 'zip', download_path)
    shutil.rmtree(download_path)
    
    offset = file_list_json['items'][-1]['drawerId']
