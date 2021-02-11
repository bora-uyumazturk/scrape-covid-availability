import json
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup

CVS_VACCINE_PAGE = '/immunizations/covid-19-vaccine?icid=cvs-home-hero1-banner-1-coronavirus-vaccine'
CVS_ROOT = 'https://www.cvs.com'
OUTPUT_PATH = 'data/vaccine_info.csv'


def get_resource(url):
    """Make request and handle response."""
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f'Recieved code: {page.status_code}')
    return resp


def cvs_json_to_df(state, state_data):
    """Transform CVS state vaccine availability data to dataframe."""
    data = state_data['responsePayloadData']['data']
    timestamp = state_data['responsePayloadData']['currentTime']
    if state not in data.keys():
        return pd.DataFrame(columns=['state', 'city', 'totalAvailable', 'pctAvailable', 'status', 'lastUpdated'])
    df = pd.DataFrame.from_records(data[state])
    df.loc[:, 'lastUpdated'] = timestamp
    return df


def scrape_cvs():
    """Scrape and return CVS data."""
    page = get_resource(CVS_ROOT + CVS_VACCINE_PAGE)

    soup = BeautifulSoup(page.content, 'html.parser')

    modals = [elem for elem in soup.find_all(
        class_='modal__box') if elem.get('id').startswith('vaccineinfo')]

    state_urls = {}
    for modal in modals:
        state = modal.get('id').split('-')[-1]
        state_urls[state] = CVS_ROOT + \
            modal.find(class_='covid-status').get('data-url')

    state_dfs = []
    for state, url in state_urls.items():
        state_response = get_resource(url)
        state_df = cvs_json_to_df(state, state_response.json())
        state_dfs.append(state_df)

    return pd.concat(state_dfs)


def save_data(filepath, df):
    """Save dataframe to filepath."""
    df.to_csv(filepath)


def main():
    """Scrape and save data for all sources."""
    cvs_data = scrape_cvs()
    cvs_data.loc[:, 'queryTime'] = pd.Timestamp.now()
    save_data(OUTPUT_PATH, cvs_data)


if __name__ == '__main__':
    main()
