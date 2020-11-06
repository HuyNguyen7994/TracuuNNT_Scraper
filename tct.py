# -*- coding: utf-8 -*-
import logging
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # hack to suppress tensorflow logging (https://github.com/tensorflow/tensorflow/issues/31870). Anti-pattern. Consider changing it later

import DriverFirefox

# aux function


# create main logger
logger = logging.getLogger('TracuuNNT')
logger.setLevel(logging.INFO)
# create file handler
today = datetime.today().strftime(r'%Y%m%d')
fh = logging.FileHandler(f'.\\log\\{today}_run_log.txt', encoding='utf-8')
fh.setLevel(logging.INFO)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# intialize argparser
parser = argparse.ArgumentParser(description='Scrape records from http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp.\nGo to https://github.com/HuyNguyen7994/TracuuNNT_Scraper for more details.',
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('command', help="specify how it scrapes. Supported command: scrape, scan, scrape_all")
parser.add_argument('input', help="""search terms for scraper. Supported input: single search term (only tax number is supported at the moment), planned feature_path to txt/csv file contains multiple search terms""")
parser.add_argument('output', help="path to output folder. Default to '.\output'", nargs='?', default='.\\output')

args = parser.parse_args()
# 030344323

logger.info('Initialising webdriver...')
with DriverFirefox.DriverFirefox(solver_path=r'.\solver\CNN5_v10_acc_98.h5') as driver:
    commands = {'scrape':driver.scrape,
                'scan': driver.scan,
                'scrape_all': driver.scrape_all}
    logger.info('Start scraping...')
    result = commands[args.command]({'TaxNumber':args.input})
    search_keys = str({'TaxNumber':args.input})
    result = {search_keys:result}
    logger.info('Finished scraping.')

logger.debug('Writing output...')
output_folder = Path(args.output)
output_folder.mkdir(parents=True, exist_ok=True)
output_file = output_folder / 'result.json'
with open(output_file, 'a', encoding='utf-8') as f:
    f.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))

logger.info('Finished writing to %s.', output_file)
