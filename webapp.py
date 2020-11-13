# -*- coding: utf-8 -*-
import logging
import logging.config
logger = logging.getLogger(__name__)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # hack to suppress tensorflow logging (https://github.com/tensorflow/tensorflow/issues/31870). Anti-pattern. Consider changing it later

from pathlib import Path
from src import DriverFirefox
from src.config import ConfigManager

def import_config(config_folder=None):
    Config = ConfigManager()
    config_path = Path(config_folder or r'.\config')
    if not config_path.exists():
        Config.create_template('template.yaml',r'.\config')
        Config.loads_yaml(r'.\config')
    else:
        Config.loads_yaml(config_folder)
    return Config

def init_logger(config_dict):
    Path(config_dict['handlers']['file']['filename']).parent.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(config_dict)

def run_scraper(site, command, term_value, config):
    logger.info('Initialising webdriver...')
    config['default']['site'] = site or config['default']['site']
    if config['default']['site'] == 'business':
        logger.info('Navigating to TracuuNNT\\Doanh nghiep')
        run_driver = DriverFirefox.business_scraper
    elif config['default']['site'] == 'personal':
        logger.info('Navigating to TracuuNNT\\Ca nhan')
        run_driver = DriverFirefox.personal_scraper
    with run_driver(solver_path=config['default']['solver_path'], 
                    headless=True, executable_path=config['default']['webdriver_path']) as driver:
        commands = {'scrape':driver.scrape,
                    'scan': driver.scan,
                    'scrape_all': driver.scrape_all}
        logger.info('Start scraping...')
        search_term, search_value = term_value.split('=')
        result = commands[command]({search_term:search_value})
        search_keys = str({search_term:search_value})
        result = {search_keys:result}
        logger.info('Finished scraping.')
    return result

def main(site, command, term_value):
    config_path = Path(r'.\config')
    if config_path.exists():
        config = import_config(config_path)
    else:
        config = import_config()
    init_logger(config['logging'])
    result = run_scraper(site, command, term_value, config)
    return result