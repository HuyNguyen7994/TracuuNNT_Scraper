# -*- coding: utf-8 -*-
import logging
import logging.config
logger = logging.getLogger(__name__)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # hack to suppress tensorflow logging (https://github.com/tensorflow/tensorflow/issues/31870). Anti-pattern. Consider changing it later

import json
import argparse
from pathlib import Path
from src.DriverFirefox import DriverFirefox
from src.config import ConfigManager

def import_config(config_folder=None):
    Config = ConfigManager()
    if not config_folder:
        Config.create_template('template.yaml',r'.\config')
        Config.loads_yaml(r'.\config')
    else:
        Config.loads_yaml(config_folder)
    return Config

def init_logger(config_dict):
    Path(config_dict['handlers']['file']['filename']).parent.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(config_dict)

def init_argparser(config):
    parser = argparse.ArgumentParser(description='Scrape records from http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp.\nGo to https://github.com/HuyNguyen7994/TracuuNNT_Scraper for more details.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('command', help="specify how it scrapes. Supported command: scrape, scan, scrape_all")
    parser.add_argument('input', help="""search terms for scraper. Supported input: single search term (only tax number is supported at the moment), planned feature_path to txt/csv file contains multiple search terms""")
    parser.add_argument('output', help="path to output folder. Configured in config/main.yaml", nargs='?', default=config['default']['output_folder'])

    args = parser.parse_args()
    return args

def run_scraper(args, config):
    logger.info('Initialising webdriver...')
    with DriverFirefox(solver_path=config['default']['solver_path'], 
                       headless=True, executable_path=config['default']['webdriver_path']) as driver:
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

def main():
    config_path = Path(r'.\config')
    if config_path.exists():
        config = import_config(config_path)
    else:
        config = import_config()
    init_logger(config['logging'])
    args = init_argparser(config)
    run_scraper(args, config)
    
if __name__ == '__main__':
    main()

# 030344323
