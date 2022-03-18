import pandas as pd
pd.options.mode.chained_assignment = None 
import yaml
import requests
from ast import literal_eval
from tqdm import tqdm
from internetarchive import get_session
from time import sleep
import os
import argparse

MAX_RECURSIVE = 10
SLEEP_PAUSE = 0.75
MAX_CHECKS = 6

WAYBACK_EXISTS_URL = 'https://archive.org/wayback/available?url='
WAYBACK_SAVE_URL = 'https://web.archive.org/save/'

CLIENT_HEADERS = {
    'User-Agent': 'Sucho.org Data Rescue Python Wayback Backup API-Client'
}

def get_crawl_yaml(file_path: str) -> dict:
    """ Read crawl yaml file """
    with open(file_path) as f:
        crawl_yaml = yaml.safe_load(f)
    return crawl_yaml

def get_crawl_data(crawl_yaml: dict) -> pd.DataFrame:
    """ Get crawl data from yaml file """
    crawl_data = pd.DataFrame({'done_links': crawl_yaml['state']['done']})
    return crawl_data

def clean_links(row: pd.Series) -> dict:
    """ Clean links from yaml file """
    cleaned_link = row.done_links.replace(':false', ':False').replace(':true', ':True')
    return literal_eval(cleaned_link)


def get_failed_links(crawl_data: pd.DataFrame) -> pd.DataFrame:
    """ Get failed links from crawl data """
    crawl_data['cleaned_links'] = crawl_data.apply(clean_links, axis=1)
    crawled_links = pd.json_normalize(crawl_data['cleaned_links'])
    return crawled_links


def get_failed_links_to_wayback(crawled_links: pd.DataFrame) -> pd.DataFrame:
    """ Check if failed links are in wayback """
    crawled_links.failed.fillna(False, inplace=True)

    failed_links = crawled_links[crawled_links.failed == True]
    failed_links['process_wayback'] = False
    failed_links['wayback_snapshot'] = None
    for index, row in tqdm(failed_links.iterrows(), total=failed_links.shape[0], desc='Checking for URL in Wayback'):
        url = row.url
        response = requests.get(WAYBACK_EXISTS_URL + url)
        if response.status_code == 200:
            archived_snapshots = response.json()['archived_snapshots']
            if len(archived_snapshots) == 0:
                failed_links.at[index, 'process_wayback'] = True
            else:
                failed_links.at[index, 'wayback_snapshot'] = archived_snapshots
        else:
            print('Error: ' + url)
    return failed_links

def generate_links_for_wayback(failed_links: pd.DataFrame) -> pd.DataFrame:
    """ Generate links for wayback """
    for index, row in tqdm(failed_links.iterrows(), total=failed_links.shape[0], desc='Generating Wayback Links'):
        if row.process_wayback == True:
            continue
        else:
            if row.url in row.wayback_snapshot['closest']['url']:
                check_exact_urls = row.wayback_snapshot['closest']['url'].split(row.url)[-1]
                check_exact_urls = check_exact_urls.replace('/', '')
                if len(check_exact_urls ) > 0:

                    failed_links.at[index, 'process_wayback'] = True
    return failed_links

def start_ia_session():
    """ Copied from Eric Kansa's script https://github.com/opencontext/sucho-data-rescue-scrape/blob/main/scraper/scraper_archiver.py
    starts an internet archive session """
    config = dict(
        s3=dict(
            acccess=os.getenv('INTERNET_ARCHIVE_ACCESS_KEY'),
            secret=os.getenv('INTERNET_ARCHIVE_SECRET_KEY'),
        )
    )
    s = get_session(config=config, debug=True)
    s.access_key = os.getenv('INTERNET_ARCHIVE_ACCESS_KEY')
    s.secret_key = os.getenv('INTERNET_ARCHIVE_SECRET_KEY')
    return s

def wayback_archive_url(row: pd.Series, session=None, delay_before_request=SLEEP_PAUSE, client_headers=CLIENT_HEADERS, try_again=True):
    """ Copied from Eric Kansa's script https://github.com/opencontext/sucho-data-rescue-scrape/blob/main/scraper/scraper_archiver.py 
    Archive the URL with the Wayback Machine """
    if delay_before_request > 0:
        # default to sleep BEFORE a request is sent, to
        # give the remote service a break.
        sleep(delay_before_request)
    if not session:
        session = start_ia_session()
    ok = None
    try:
        # now execute the request to the internet archive API
        # s_url = self.wb_save_url + quote(url, safe='')
        s_url = WAYBACK_SAVE_URL + row.url
        r = session.post(s_url,
            params={
                'capture_all': 1,
                'capture_outlinks': 1,
                'delay_wb_availability': 1,
                'skip_first_archive': 1,
            },
            timeout=240,
            headers=client_headers
        )
        r.raise_for_status()
        ok = True
    except:
        ok = False
    if not ok and not try_again:
        print(f'Wayback failed to archive {row.url}')
    if not ok and try_again:
        ok = wayback_archive_url(
            url=row.url, 
            session=None, 
            delay_before_request=(delay_before_request * 2),
            client_headers=client_headers,
            try_again=False
        )
    return ok


def get_or_save_browsertrix_links(yaml_path: str, output_path: str, get_csv: bool = False, send_wayback: bool = False):
    """Function to get or save browsertrix links from a yaml file."""
    crawl_yaml = get_crawl_yaml(yaml_path)
    output_path = output_path + 'failed_browsertrix_links_' + crawl_yaml['collection'] + '.csv'
    crawl_data = get_crawl_data(crawl_yaml)
    crawled_links = get_failed_links(crawl_data)
    failed_links = get_failed_links_to_wayback(crawled_links)
    failed_links = generate_links_for_wayback(failed_links)
    if get_csv == True:
        failed_links[failed_links.process_wayback == True][['url']].reset_index(drop=True).to_csv(output_path, index=False)
    if send_wayback == True:
        session = start_ia_session()
        for index, row in tqdm(failed_links.iterrows(), total=failed_links.shape[0], desc='Sending to Wayback'):
            if row.process_wayback == True:
                wayback_archive_url(row, session)
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get or save failed browsertrix links')
    parser.add_argument('--yaml_path', type=str, help='Path to crawl yaml file')
    parser.add_argument('--output_path', type=str, help='Path to output file (only change if you want a different directory)')
    parser.add_argument('--get_csv', action=argparse.BooleanOptionalAction, help='Get csv of failed links for gsheets')
    parser.add_argument('--send_wayback', action=argparse.BooleanOptionalAction, help='Send failed links to wayback')
    args = parser.parse_args()

    get_or_save_browsertrix_links(args.yaml_path, args.output_path, args.get_csv, args.send_wayback)
