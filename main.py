import requests
from selenium import webdriver
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import sys
import time
import itertools
import csv

baseurl = 'https://urlfiltering.paloaltonetworks.com/'
loginurl = urljoin(baseurl, 'accounts/login/')
queryurl = urljoin(baseurl, 'query/')

driver = webdriver.Chrome()
driver.get(loginurl)

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


session = requests.Session()
cookies = driver.get_cookies()
for cookie in cookies:
    session.cookies.set(cookie['name'], cookie['value'])

response = session.get(queryurl)
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})['value']

with open('./urllist.txt', 'r') as f:
    urllist = f.read().splitlines()

headers={
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://urlfiltering.paloaltonetworks.com/query/'
    }


fieldnames = ['URL', 'Category', 'Risk Level']
with open("result.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for url in urllist:
        urldict = {}
        urldict['URL'] = url
        data=f'csrfmiddlewaretoken={csrf_token}&url={url}'
    
        result = session.post(queryurl, headers=headers, data=data)
        soup = BeautifulSoup(result.text, 'html.parser')
        
        for li in soup.find_all('li'):
            bc = li.find('b', string='Categories')
            if bc:
                category = bc.next_sibling.strip(': \n')
                print(category)
                urldict['Category'] = category
            br = li.find('b', string='Risk Level')
            if br:
                risklevel = br.next_sibling.strip(': \n')
                print(risklevel)
                urldict['Risk Level'] = risklevel
                break
        writer.writerow(urldict)