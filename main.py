# -*- coding: utf-8 -*-
import logging
import logging.config
logger = logging.getLogger(__name__)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # hack to suppress tensorflow logging (https://github.com/tensorflow/tensorflow/issues/31870). Anti-pattern. Consider changing it later

import json
import argparse
from time import time
from pathlib import Path
from src import webdriver, apputility

def init_argparser(config):
    parser = argparse.ArgumentParser(description='Scrape records from http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp.\nGo to https://github.com/HuyNguyen7994/TracuuNNT_Scraper for more details.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('command', help="specify how it scrapes. Supported command: scrape, scan, scrape_all")
    parser.add_argument('input', help="""search terms for scraper. Supported input: single search term ('TaxNumber', 'Name', 'Address', 'IdNumber') with value in format term=value, planned feature_path to txt/csv file contains multiple search terms""")
    parser.add_argument('output', help="path to output folder. Configured in config/main.yaml", nargs='?', default=config['default']['output_folder'])
    parser.add_argument('--site', '-s', help="to scrape business or personal record")
    args = parser.parse_args()
    return args

def run_scraper(args, config):
    logger.info('Initialising webdriver...')
    config['default']['site'] = args.site or config['default']['site']
    if config['default']['site'] == 'business':
        logger.info('Navigating to TracuuNNT\\Doanh nghiep')
        run_driver = webdriver.BusinessProfileScraper
    elif config['default']['site'] == 'personal':
        logger.info('Navigating to TracuuNNT\\Ca nhan')
        run_driver = webdriver.PersonalProfileScraper
    with run_driver(solver_path=config['default']['solver_path'], 
                    headless=True, executable_path=config['default']['webdriver_path']) as driver:
        logger.info('Start scraping...')
        search_term, search_value = args.input.split('=')
        result = driver.run(args.command, {search_term:search_value})
        search_keys = str({search_term:search_value})
        result = {search_keys:result}
        logger.info('Finished scraping.')

    logger.debug('Writing output...')
    output_folder = Path(args.output)
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / (str(int(time())) + '.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))

    logger.info('Finished writing to %s.', output_file)

def main():
    config_path = Path(r'config')
    if config_path.exists():
        config = apputility.import_config(config_path)
    else:
        config = apputility.import_config()
    apputility.init_logger(config['logging'])
    args = init_argparser(config)
    run_scraper(args, config)
    
if __name__ == '__main__':
    main()
