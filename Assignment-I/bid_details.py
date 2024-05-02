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
        prefs = {"download.default_directory" : "E:\\attachment\\" + bid_num}
        options.add_experimental_option("prefs",prefs)
        driver = webdriver.Chrome(options=options)
        driver.get(bid_link)
        inner_soup = get_soup(driver)
        
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
        attachments = driver.find_element(By.XPATH, '/html/body/form/table/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr['+str(count+2)+']')
        files = attachments.find_elements(By.CLASS_NAME, 'link-01')
        for file in files:
            file.click()
        driver.close()
        print(new_dict)
        input()
        
        # all_data.append(new_dict)

if __name__ == '__main__':
    response = get_request(LINK)
    soup = get_soup(response)
    get_bid_details(soup)