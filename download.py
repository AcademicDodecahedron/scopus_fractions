import requests
import random
import time
from sys import stdout
from requests.exceptions import HTTPError
from string import Template
from argparse import ArgumentParser
from lib import web, secret
from lib.log import Log
from lib.stepper import Stepper

def parse_args():
    argp = ArgumentParser()
    argp.add_argument('id')
    argp.add_argument('year_from', type=int)
    argp.add_argument('year_to', type=int)
    return argp.parse_args()
args = parse_args()

QUERY_TEMPLATE = Template('( AF-ID ( $id ) ) AND  ( PUBYEAR IS $year ) AND NOT  DOCTYPE ( ip )')
SORT = '&sort=orig-load-date&field=eid,citedby-count,prism:coverDisplayDate,source-id,prism:doi,subtype,prism:aggregationType,author,affiliation'
URL_START = 'https://api.elsevier.com/content/search/scopus?query='

def make_url(record_id, year, start, count):
    query = QUERY_TEMPLATE.substitute(id=record_id, year=year)
    return f"{URL_START}{query}&start={start}&count={count}{SORT}"

sess = requests.Session()
sess.headers = { #type:ignore
    'User-Agent': 'UrFU SciCube BI/0.2',
    'X-ELS-ApiKey': secret.API_KEY,
    'X-ELS-Insttoken': secret.INST_TOKEN,
    'X-ELS-ResourceVersion': "XOCS",
    'Accept': "application/json"
}

def try_get_record_count(record_id, year, start=1):
    url = make_url(record_id, year, start, 0)

    return web.try_get(sess, url) \
        .map(lambda resp: int(resp.json()['search-results']['opensearch:totalResults']))

log = Log('record.log')

def sleep_random(max_time):
    sleep_time = random.random() * max_time
    print(' (sleep {:.2f})'.format(sleep_time), end='')
    stdout.flush()
    time.sleep(sleep_time)

def load_record(record_id, year, start_record, record_count):
    sleep_random(45)
    url = make_url(record_id, year, start_record, record_count)
    return web.get_ok(sess, url).json()

for year in range(args.year_from, args.year_to + 1):
    start_record = 1
    for count in log.result(try_get_record_count(args.id, year, start_record)):
        log.print(f"Found {count} items for year {year}")

        stepper = Stepper(
            start=1,
            total=count,
            steps=[100,50,25,12,6,3,1]
        )

        for start_current, steps_current in stepper:
            print(f"Querying year {year} {start_current}-{start_current + steps_current - 1} [{start_record}-{count}]", end='')
            try:
                response = load_record(args.id, year, start_current, steps_current)
                print(' - OK')
                stepper.step_success()
                log.print(response)
            except HTTPError as err:
                print(' - Err')
                log.print(err)
                for skipped_record in stepper.step_failed():
                    log.print(f"Skipping record {skipped_record}")
