import requests
import time
import signal
from sys import stdout
from requests.exceptions import HTTPError
from string import Template
from typing import NamedTuple
from argparse import ArgumentParser
from lib import secret, tabular
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

MIN_TIME_GAP = 2
last_request_time = None
def get_safe(url):
    global last_request_time
    current_time = time.time()
    if last_request_time is not None and current_time - last_request_time < MIN_TIME_GAP:
        time.sleep(MIN_TIME_GAP + last_request_time - current_time)

    last_request_time = time.time()

    response = sess.get(url)
    response.raise_for_status()
    return response

def get_record_count(record_id, year, start):
    url = make_url(record_id, year, start, 0)

    response = get_safe(url)
    return int(response.json()['search-results']['opensearch:totalResults'])

def load_record(record_id, year, start_record, record_count):
    url = make_url(record_id, year, start_record, record_count)
    return get_safe(url)

class OutRow(NamedTuple):
    year: int
    start: int
    count: int
    ok: bool
    response: str

interrupted = False
def on_interrupt(sig, frame):
    global interrupted
    interrupted = True
signal.signal(signal.SIGINT, on_interrupt)

with open('record.log', mode='a') as log_file:
    log = Log(log_file)
    year = args.year_from
    start_record = 1

    try:
        last_line = tabular.read_last_line('out.txt', OutRow)
        if last_line is not None:
            year = last_line.year
            start_record = last_line.start
            if last_line.ok:
                start_record += last_line.count

            log.print(f"Continuing from year={year}, record={start_record}")
    except FileNotFoundError: pass

    with open('out.txt', mode='a') as out_file:
        writer = tabular.Writer(out_file, OutRow)
        while year <= args.year_to:
            if interrupted: break
            log_head = f"[id={args.id}, year={year}]"

            count = None
            try: count = get_record_count(args.id, year, start_record)
            except HTTPError as err:
                log.print(f"{log_head} Failed to get number of records: {err}")
                continue

            log.print(f"{log_head} Found {count} records")
            stepper = Stepper(
                start=start_record,
                total=count,
                steps=[100,50,25,12,6,3,1]
            )

            for start_current, steps_current in stepper:
                if interrupted: break
                log.print(f"{log_head} Requesting records {start_current}-{start_current + steps_current - 1} [Total: {start_record}-{count}]", end='')
                stdout.flush()

                try:
                    response = load_record(args.id, year, start_current, steps_current)
                    log.print(' - OK')
                    writer.write(OutRow(year, start_current, steps_current, True, response.text))
                    stepper.step_success()
                except HTTPError as err:
                    log.print(f" - {err}")
                    writer.write(OutRow(year, start_current, steps_current, False, str(err)))
                    skipped = stepper.step_failed()
                    if skipped is not None:
                        log.print(f"Skipping record {skipped}")
            year += 1
            start_record = 1
