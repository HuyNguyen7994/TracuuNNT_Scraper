# -*- coding: utf-8 -*-
import logging
import logging.config
logger = logging.getLogger(__name__)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # hack to suppress tensorflow logging (https://github.com/tensorflow/tensorflow/issues/31870). Anti-pattern. Consider changing it later

from pathlib import Path
from src import webdriver, apputility

def run(site, command, term, value, config):
    logger.info('Initialising webdriver...')
    if site == 'business':
        logger.info('Navigating to mstdn.jsp')
        run_driver = webdriver.BusinessProfileScraper
    elif site == 'personal':
        logger.info('Navigating to mstcn.jsp')
        run_driver = webdriver.PersonalProfileScraper
    with run_driver(solver_path=config['default']['solver_path'], 
                    headless=True) as driver:
        logger.info('Start scraping...')
        result = driver.run(command, {term:value})
        search_keys = str({term:value})
        result = {search_keys:result}
        logger.info('Finished scraping. Spin down driver.')
    return result

def main(site, command, term, value):
    config_path = Path(r'config')
    config = apputility.import_config(config_path)
    apputility.init_logger(config['logging'])
    result = run(site, command, term, value, config)
    return result