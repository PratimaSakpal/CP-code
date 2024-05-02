"""
Description: Script to get contact details of School.
Link: 'https://isd110.org/our-schools/laketown-elementary/staff-directory'
Fields to be extracted:
    - School Name - Available in title of the page
    - Address
    - State
    - Zip
    - First Name
    - Last Name
    - Title
    - Phone
    - Email
"""
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

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
    soup = BeautifulSoup(response.text, features="html.parser")
    return soup

def get_contact_details(soup):
    """
    Extract details from page
    """
    all_details = []
    school_name = soup.find('div', {'class':'site-name'}).text.strip()
    address = soup.find(
        'div', {'class': 'field location label-above'}).find(
            'div', {'class': 'field-content'}).text
    address = re.sub(r'\s+|\n', ' ', address).replace('Directions', '').strip()
    zip_code = re.findall(r'\d{5,6}$', address)[0]
    state = address.replace(zip_code, '').strip().split(' ')[-1]
    contact_name = soup.find_all('div', {'class':'views-row'})
    for contact in contact_name:
        new_dict = {}
        new_dict['School Name'] = school_name
        new_dict['Address'] = address
        new_dict['State'] = state
        new_dict['Zip'] = zip_code
        name = contact.find('h2').text
        if not name:
            return None
        first_name = name.split(',')[0].strip()
        new_dict['First Name'] = first_name
        last_name = name.split(',')[-1].strip()
        new_dict['Last Name'] = last_name
        title = contact.find('div', {'class':'field job-title'})
        new_dict['Title'] = title.text.strip()
        phone = contact.find('div', {'class':'field phone'})
        new_dict['Phone'] = phone.text.strip()
        email = contact.find('div', {'class':'field email'})
        new_dict['Email'] = email.text.strip()
        all_details.append(new_dict)
    return all_details

def write_into_csv(final_details):
    """
    Create and write into CSV file.
    """
    print('Provide a path to write into csv')
    path_for_write = input()
    data_frame = pd.DataFrame(final_details)
    data_frame.to_csv(path_for_write + '/School Contact Deatils.csv', index=False)
    print('CSV file is create on "' + path_for_write + '/School Contact Deatils.csv"')

def main():
    """
    Main call
    """
    final_details = []
    next_page = 0
    while True:
        link = 'https://isd110.org/our-schools/laketown-elementary/staff-directory?amp%3Bpage=1&amp%3Bs=&s=&page=' + str(next_page)
        response = get_request(link)
        if response:
            soup = get_soup(response)
            details = get_contact_details(soup)
            if not details:
                break
            final_details.extend(details)
            next_page += 1
        else:
            print('Link is not working or blocked.')
            break
        print('Data crawled for page ' + str(next_page))
    write_into_csv(final_details)

if __name__ == '__main__':
    main()
