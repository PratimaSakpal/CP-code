"""
Description: Script to get contact details of School.
Link: 'https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true'
Fields to be extracted:
    - Bid Solicitation
    - Buyer
    - Description
    - Bid Opening Date
    - Navigate to the individual webpage by clicking on bid solicitation number. Extract all header information in dictionary format till Bill-to Address. 
    - Download the corresponding file attachments for each record. There can be multiple files as well.
"""
import time
import re
import json
import warnings
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
warnings.filterwarnings("ignore")

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
        soup = BeautifulSoup(response.text, "html.parser")
    except AttributeError:
        soup = BeautifulSoup(response.page_source, "html.parser")
    return soup

def get_item_details(item_soup):
    """
    Get details of "Item Information"
    """
    item_list = []
    item_head = item_soup.find_all('tr', {'class':'tableStripe-02'})
    item_head = [item for item in item_head if 'Item #' in item.text]
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
                item_dict['Item #'] = item_num[0].strip()
                item_dict['Item title'] = item_num[1].strip()
                tds = t.find_all('td', {'class':'tableText-01 whcmFix'})
                for index, td in enumerate(tds[:4]):
                    item_dict[td.text.strip()] = tds[index+4].text.strip()
                count += 1
        except IndexError:
            pass
        if item_dict.get('Qty') and item_dict.get('NIGP Code'):
            item_list.append(item_dict)
    return item_list

def download_attachments(driver, all_tds):
    """
    Download files
    """
    file_attachments = []
    for al in all_tds:
        if 'File Attachments:' in al.text.strip():
            file_attachments = al.find_all_next('a')
    file_attachments = [f.text.strip() for f in file_attachments if not f.text.isdigit()]
    files = driver.find_elements(By.CLASS_NAME, 'link-01')
    for f in files:
        if f.text.strip() in file_attachments and 'Form' not in f.text.strip():
            f.click()
            time.sleep(0.5)

def get_bid_details(soup):
    """
    Crawling of Bid Details
    """
    header = soup.find(
        'thead', {'id':'bidSearchResultsForm:bidResultId_head'}).find('tr').find_all('th')
    header = [head.text for head in header]

    all_data = []
    table = soup.find(
        'tbody', {'id':'bidSearchResultsForm:bidResultId_data'}).find_all('tr')

    for tab in table[:1]:
        datas = tab.find_all('td')
        new_dict = {}
        for index, data in enumerate(datas):
            if header[index] in ['Bid Solicitation #', 'Buyer', 'Description', 'Bid Opening Date']:
                new_dict[header[index]] = data.text.strip()
        bid_num = new_dict['Bid Solicitation #']
        bid_link = 'https://nevadaepro.com/bso/external/bidDetail.sdo?docId='+bid_num+'&external=true&parentUrl=close'
        print('Crawling of Bid: ', bid_num)
        prefs = {"download.default_directory" : "E:\\attachment\\" + bid_num}
        options.add_experimental_option("prefs",prefs)
        driver = webdriver.Chrome(options=options)
        driver.get(bid_link)
        time.sleep(1)
        inner_soup = get_soup(driver)
        item_list = []
        item_details = get_item_details(inner_soup)
        item_list.extend(item_details)
        all_tds = inner_soup.find_all('td', {'class':'t-head-01'})
        download_attachments(driver, all_tds)
        count = 0
        for td in all_tds:
            count += 1
            inner_header = td.text
            data = td.find_next('td', {'class':'tableText-01'}).text
            inner_header = re.sub(r':|\s+', ' ', inner_header).strip()
            new_dict[inner_header] = data.strip()
            if inner_header == 'Bill-to Address':
                break  
        page_count = 0  
        while True:
            bottom = driver.find_elements(By.XPATH, '/html/body/form/table/tbody/tr/td/table/tbody/tr[4]/td/table[6]/tbody/tr[2]/td/table/tbody')
            if not bottom:
                break
            if re.search(r'\d+\-\d+\sof\s\d+', bottom[0].text):
                pages = bottom[0].find_elements(By.CLASS_NAME, 'link-01')
                page = pages[page_count]
                page_count += 1
                page.click()
                time.sleep(1)
                item_soup = get_soup(driver)
                all_tds = item_soup.find_all('td', {'class':'t-head-01'})
                download_attachments(driver, all_tds)
                item_soup = BeautifulSoup(driver.page_source)
                item_details = get_item_details(item_soup)
                item_list.extend(item_details)
                if page_count == len(pages):
                    break
        new_dict['Item Information'] = item_list
        all_data.append(new_dict)
        driver.close()
    print('Provide a path to write JSON file.')
    path_for_write = input()
    with open(path_for_write + "\\Bid Details.json", "w") as json_file:
        json.dump(all_data, json_file)
    print('CSV file is create on "' + path_for_write + '\\Bid Details.json"')

def main():
    """
    Calls
    """
    response = get_request(LINK)
    soup = get_soup(response)
    get_bid_details(soup)

if __name__ == '__main__':
    main()
