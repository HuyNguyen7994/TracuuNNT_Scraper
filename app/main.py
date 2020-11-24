# -*- coding: utf-8 -*-

import logging
import logging.config
from pathlib import Path
import utility
from webdriver import BusinessProfileScraper, PersonalProfileScraper
from solver import SolverManager

logger = logging.getLogger(__name__)

def run(site, command, term, value, config):
    logger.info('Initialising webdriver...')
    if site == 'business':
        logger.info('Navigating to mstdn.jsp')
        run_driver = BusinessProfileScraper
    elif site == 'personal':
        logger.info('Navigating to mstcn.jsp')
        run_driver = PersonalProfileScraper
    with run_driver(solver=SolverManager(MODEL_API = r"http://solver:8501/v1/models/solver:predict"),
                    headless=True) as driver:
        logger.info('Start scraping...')
        result = driver.run(command, {term:value})
        search_keys = str({term:value})
        result = {search_keys:result}
        logger.info('Finished scraping. Spin down driver.')
    return result

def search(site, command, term, value):
    config_path = Path(r'config')
    config = utility.import_config(config_path)
    utility.init_logger(config['logging'])
    result = run(site, command, term, value, config)
    return result

if __name__ == '__main__':
    search('business', 'pinpoint', 'name', 'hòa bình')