import requests
import time
import signal
from sys import stdout
from requests.exceptions import HTTPError
from string import Template
from argparse import ArgumentParser
from pathlib import Path
from lib import tabular, secret
from lib.log import Log
from lib.stepper import Stepper
from lib.model import RequestResult

# Если не указан аргумент --secret,
# искать secret.json в папке со скриптом
def default_json_path():
    return str(Path(__file__).parent.joinpath('secret.json'))

def parse_args():
    argp = ArgumentParser()
    argp.add_argument('id', help='university id (AF-ID)')
    argp.add_argument('year_from', type=int, help='year range start')
    argp.add_argument('year_to', type=int, help='year range end (inclusive)')
    argp.add_argument('--secret', default=default_json_path(), help='json file containing "ApiKey" and "InstToken"')
    argp.add_argument('-l', '--log', default='record.log', help='log file')
    argp.add_argument('-o', '--out', default='out.txt', help='output file')
    return argp.parse_args()
args = parse_args()
api_key, inst_token = secret.load_secrets(args.secret)

QUERY_TEMPLATE = Template('( AF-ID ( $id ) ) AND  ( PUBYEAR IS $year ) AND NOT  DOCTYPE ( ip )')
SORT = '&sort=orig-load-date&field=eid,citedby-count,prism:coverDisplayDate,source-id,prism:doi,subtype,prism:aggregationType,author,affiliation'
URL_START = 'https://api.elsevier.com/content/search/scopus?query='

def make_url(record_id, year, start, count):
    query = QUERY_TEMPLATE.substitute(id=record_id, year=year)
    return f"{URL_START}{query}&start={start}&count={count}{SORT}"

sess = requests.Session()
sess.headers = { #type:ignore
    'User-Agent': 'UrFU SciCube BI/0.2',
    'X-ELS-ApiKey': api_key,
    'X-ELS-Insttoken': inst_token,
    'X-ELS-ResourceVersion': "XOCS",
    'Accept': "application/json"
}

# Делает запрос не чаще, чем в 2 секунды
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

# Количество записей в году
def get_record_count(record_id, year):
    url = make_url(record_id, year, 1, 0)

    response = get_safe(url)
    return int(response.json()['search-results']['opensearch:totalResults'])

# Запросить record_count записей, начиная со start_record
def load_record(record_id, year, start_record, record_count):
    url = make_url(record_id, year, start_record, record_count)
    return get_safe(url)

# По сигналу прерывания (Ctrl-C) сразу не закрывать,
# докачать текущую запись
interrupted = False
def on_interrupt(sig, frame):
    global interrupted
    interrupted = True
signal.signal(signal.SIGINT, on_interrupt)

with open(args.log, mode='a') as log_file:
    log = Log(log_file)
    year = args.year_from
    start_record = 1

    # Если есть файл с уже загруженными записями,
    # продолжить с последней строки
    try:
        last_line = tabular.read_last_line(args.out, RequestResult)
        if last_line is not None:
            year = last_line.year
            start_record = last_line.start
            if last_line.ok:
                start_record += last_line.count

            log.print(f"Continuing from year={year}, record={start_record}")
    except FileNotFoundError: pass

    with open(args.out, mode='a') as out_file:
        writer = tabular.Writer(out_file, RequestResult)
        while year <= args.year_to:
            if interrupted: break
            log_head = f"[id={args.id}, year={year}]"

            # Скачать количество записей (в случае ошибки, пропустить год)
            count = None
            try: count = get_record_count(args.id, year)
            except HTTPError as err:
                log.print(f"{log_head} Failed to get number of records: {err}")
                continue

            log.print(f"{log_head} Found {count} records")

            stepper = Stepper(
                start=start_record, # Начать с этой записи
                total=count, # Всего записей в году
                steps=[100,50,25,12,6,3,1] # В случае ошибки уменьшать диапазон
            )

            for start_current, steps_current in stepper:
                if interrupted: break
                log.print(f"{log_head} Requesting records {start_current}-{start_current + steps_current - 1} [Total: {start_record}-{count}]", end='')
                stdout.flush()

                try:
                    response = load_record(args.id, year, start_current, steps_current)
                    log.print(' - OK')
                    writer.write(RequestResult(year, start_current, steps_current, True, response.text))
                    stepper.step_success() # Шагнуть на диапазон steps_current
                except HTTPError as err:
                    log.print(f" - {err}")
                    writer.write(RequestResult(year, start_current, steps_current, False, str(err)))
                    skipped = stepper.step_failed() # Уменьшить диапазон или пропустить запись
                    if skipped is not None:
                        log.print(f"Skipping record {skipped}")
            year += 1
            start_record = 1
