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
                msg = "ログイン検出、次の処理へ進みます"
                prev_len = print_progress(msg, prev_len)
                prev_len = len(msg)
                break
        msg = f"ログイン待機中... {next(chars)}"
        prev_len = len(msg)
        sys.stdout.write(f"\r{msg}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)
    return prev_len

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
    token_tag = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})
    return info, token_tag['value'] if token_tag else None

def caliculate_prev_len(msg, prev_len):
    """Calculate the previous length for the progress message."""
    return max(0, prev_len - len(msg))

def print_progress(msg, prev_len, line_feed=False):
    """Print the progress message, ensuring it overwrites the previous one."""
    message = f'\r{msg}{' ' * caliculate_prev_len(msg, prev_len)}'
    if line_feed:
        message += '\n'
    sys.stdout.write(message)
    sys.stdout.flush()
    return len(msg)

def main():
    driver = webdriver.Chrome()
    driver.get(LOGIN_URL)
    prev_len = wait_for_login(driver)

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
            msg = f'URL: {url} の情報を取得中...'
            prev_len = print_progress(msg, prev_len)
            urldict = {'URL': url}
            data = f'csrfmiddlewaretoken={csrf_token}&url={url}'
            result = session.post(QUERY_URL, headers=HEADERS, data=data)
            soup = BeautifulSoup(result.text, 'html.parser')
            info, updated_csrf_token = extract_info(soup)
            urldict.update(info)
            csrf_token = updated_csrf_token or csrf_token
            msg = f'URL: {url} の情報取得完了'
            prev_len = print_progress(msg, prev_len)
            writer.writerow(urldict)
        msg = "全てのURLの取得が完了しました"
        print_progress(msg, prev_len, True)


if __name__ == '__main__':
    main()