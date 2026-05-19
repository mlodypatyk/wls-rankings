from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
load_dotenv()


def get_auth_token(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    for input in soup.find_all('input'):
        if input.get('name') == 'authenticity_token':
            return input.get('value')
    return ''

def get_form_values(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    forms = []
    for form in soup.find_all('form'):
        form_json = {}
        for input in form.find_all('input'):
            form_json[input.get('name')] = input.get('value')
        forms.append(form_json)
    return forms


def update_tabs():
    WCA_PATH = "https://www.worldcubeassociation.org"
    wca_user = os.getenv('WCA_USER')
    wca_pass = os.getenv('WCA_PASS')


    session = requests.sessions.Session()
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "pl-PL,pl;q=0.9",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Brave\";v=\"144\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "Referer": "https://www.worldcubeassociation.org/"
    }

    login_url = WCA_PATH + "/users/sign_in"

    response = session.get(login_url, headers=headers)
    auth_token = get_auth_token(response.text)

    login_payload = {'user[login]': wca_user, 'user[password]': wca_pass, 'user[remember_me]': 0, 'authenticity_token': auth_token}
    login_response = session.post(login_url, headers=headers, data=login_payload)

    if 'Zalogowano pomyślnie' in login_response.text:
        print('logged in')
    else:
        print('fail')

    competitions = ['WLSStyczen2026', 'WLSLuty2026', 'WLSMarzec2026', 'WLSKwiecien2026', 'WLSMaj2026', 'WLSCzerwiec2026']
    WLS_TAB_NAME = 'WLS Klasyfikacja'

    new_tab_content = ""
    result = open('output.md', encoding='utf-8')
    new_tab_content = ''.join([line for line in result])
    result.close()


    for comp in competitions:
        api_url = WCA_PATH + f'/api/v0/competitions/{comp}/tabs'
        api_response = session.get(api_url)
        for tab in api_response.json():
            if tab['name'] == WLS_TAB_NAME:
                tab_url = WCA_PATH + f'/competitions/{comp}/tabs/{tab['id']}'
                tab_edit_url = tab_url + "/edit"
                print(f'Uploading tab {WLS_TAB_NAME} for comp {comp} with id {tab['id']}')

                tab_response = session.get(tab_edit_url, headers=headers)
                tab_edit_auth_token = get_auth_token(tab_response.text)


                tab_change_payload = {'competition_tab[name]': WLS_TAB_NAME, 'competition_tab[content]': new_tab_content, '_method': 'patch', 'authenticity_token': tab_edit_auth_token, 'image': '', 'commit': 'Update'}
                response = session.post(tab_url, headers=headers, data=tab_change_payload)
                print(response)
    
    
