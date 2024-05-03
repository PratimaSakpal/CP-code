#  apt instal chromium-ch ronedriver
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import re

LINK = 'https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true'
options = Options()
options.add_argument("--headless=new")

def get_request(link):
    """
    Get response for a link using requests
    """
    response = requests.get(link, timeout=2)
    if response.status_code == 200:
        return response
    return None

def get_soup(response):
    """
    Create soup of response object using beautifulsoup
    """
    try:
        soup = BeautifulSoup(response.text, features="html.parser")
    except:
        soup = BeautifulSoup(response.page_source, features="html.parser")
    return soup

def get_item_details(item_soup):
    item_list = []
    item_head = item_soup.find_all('tr', {'class':'tableStripe-02'})
    tbodys = item_soup.find_all('tr', {'class':'tableStripe-01'})
    nigp_codes = []
    for t in tbodys:
        if t.find('tbody') and t.find('tbody').find_all('td')[0].text.strip() == 'NIGP Code:':
            nigp_codes.append(t.find('tbody').find_all('td')[1].text.strip())
    count = 0
    for index, t in enumerate(tbodys):
        item_dict = {}
        try:
            tds = t.find_all('td', {'class':'tableText-01 whcmFix'})
            if tds[0].text.strip() == 'Qty':
                item_dict['NIGP Code'] = nigp_codes[count]
                item_num = re.sub(r'\s\s+', ' ', item_head[count].find('td', {'class':'t-head-01'}).text.strip()).split(':')
                item_dict['item #'] = item_num[0].strip()
                item_dict['item title'] = item_num[1].strip()
                tds = t.find_all('td', {'class':'tableText-01 whcmFix'})
                for index, td in enumerate(tds[:4]):
                    item_dict[td.text.strip()] = tds[index+4].text.strip()
                count += 1
        except IndexError:
            pass
        if item_dict:
            item_list.append(item_dict)
    return item_list

def download_attachments(driver, all_tds):
    file_attachments = []
    for al in all_tds:
        if 'File Attachments:' in al.text:
            file_attachments = al.find_all_next('a')   
    file_attachments = [f.strip() for f in file_attachments]

    files = driver.find_elements(By.CLASS_NAME, 'link-01')
    for f in files:
        if f.text.strip() in file_attachments:
            f.click()

def get_bid_details(soup):
    header = soup.find(
        'thead', {'id':'bidSearchResultsForm:bidResultId_head'}).find('tr').find_all('th')
    header = [head.text for head in header]

    all_data = []
    table = soup.find(
        'tbody', {'id':'bidSearchResultsForm:bidResultId_data'}).find_all('tr')

    for tab in table:
        datas = tab.find_all('td')
        new_dict = {}
        for index, data in enumerate(datas):
            if header[index] in ['Bid Solicitation #', 'Buyer', 'Description', 'Bid Opening Date']:
                new_dict[header[index]] = data.text.strip()
        bid_num = new_dict['Bid Solicitation #']
        bid_link = 'https://nevadaepro.com/bso/external/bidDetail.sdo?docId='+bid_num+'&external=true&parentUrl=close'
        print(bid_link)
        prefs = {"download.default_directory" : "E:\\attachment\\" + bid_num}
        options.add_experimental_option("prefs",prefs)
        driver = webdriver.Chrome(options=options)
        driver.get(bid_link)
        inner_soup = get_soup(driver)
        item_list = []
        item_details = get_item_details(inner_soup)
        item_list.extend(item_details)
        all_tds = inner_soup.find_all('td', {'class':'t-head-01'})
        count = 0
        for td in all_tds:
            count += 1
            inner_header = td.text
            data = td.find_next('td', {'class':'tableText-01'}).text
            inner_header = re.sub(r':|\s+', ' ', inner_header).strip()
            new_dict[inner_header] = data.strip()
            if inner_header == 'Bill-to Address':
                break
        download_attachments(driver, all_tds)
        
        bottom = driver.find_elements(By.XPATH, '/html/body/form/table/tbody/tr/td/table/tbody/tr[4]/td/table[6]/tbody/tr[2]/td/table/tbody')
        for b in bottom:
            pages = b.find_elements(By.CLASS_NAME, 'link-01')
            for page in pages:
                page.click()
                item_soup = BeautifulSoup(driver.page_source)
                all_tds = item_soup.find_all('td', {'class':'t-head-01'})
                download_attachments(driver, all_tds)
                item_details = get_item_details(item_soup)
                item_list.extend(item_details)
        new_dict['Item Information'] = item_list
        driver.close()
        print(new_dict)
        input()

if __name__ == '__main__':
    response = get_request(LINK)
    soup = get_soup(response)
    get_bid_details(soup)

