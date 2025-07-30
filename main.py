import requests
from selenium import webdriver
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import sys
import time
import itertools
import csv

BASE_URL = 'https://urlfiltering.paloaltonetworks.com/'
LOGIN_URL = urljoin(BASE_URL, 'accounts/login/')
QUERY_URL = urljoin(BASE_URL, 'query/')
URL_LIST_PATH = './urllist.txt'
RESULT_CSV_PATH = 'result.csv'
FIELDNAMES = ['URL', 'Category', 'Risk Level']
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': QUERY_URL
}

def wait_for_login(driver):
    idx = 0
    chars = itertools.cycle(r'/-\|')
    while True:
        if idx > 0 and idx % 25 == 0:
            cookies = driver.get_cookies()
            if any(cookie['name'] == 'csrftoken' for cookie in cookies):
                print("ログイン検出、次の処理へ進みます")
                break
        sys.stdout.write(f"\rログイン待機中... {next(chars)}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)

def get_csrf_token(session):
    response = session.get(QUERY_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    token_tag = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})
    return token_tag['value'] if token_tag else ''

def load_url_list(path):
    with open(path, 'r') as f:
        return f.read().splitlines()

def extract_info(soup):
    info = {}
    for li in soup.find_all('li'):
        bc = li.find('b', string='Categories')
        if bc:
            info['Category'] = bc.next_sibling.strip(': \n')
        br = li.find('b', string='Risk Level')
        if br:
            info['Risk Level'] = br.next_sibling.strip(': \n')
            break
    return info

def main():
    driver = webdriver.Chrome()
    driver.get(LOGIN_URL)
    wait_for_login(driver)

    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    driver.quit()

    csrf_token = get_csrf_token(session)
    urllist = load_url_list(URL_LIST_PATH)

    with open(RESULT_CSV_PATH, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
        writer.writeheader()
        for url in urllist:
            print(f'URL: {url} の情報を取得中...')
            urldict = {'URL': url}
            data = f'csrfmiddlewaretoken={csrf_token}&url={url}'
            result = session.post(QUERY_URL, headers=HEADERS, data=data)
            soup = BeautifulSoup(result.text, 'html.parser')
            urldict.update(extract_info(soup))
            print("取得完了")
            writer.writerow(urldict)
        print("全てのURLの取得が完了しました")

if __name__ == '__main__':
    main()