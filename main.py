# %%
# -*- coding: utf-8 -*-
import logging
import DriverFirefox
import argparse
import json
from datetime import datetime

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
# parser = argparse.ArgumentParser(description='Scrape records from http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp')

if __name__ == '__main__':
    logger.info('Initialising webdriver...')
    with DriverFirefox.DriverFirefox(solver_path=r'.\solver\CNN5_v10_acc_98.h5') as driver, open(r'.\output\result.json', 'a', encoding='utf-8') as f:
        logger.info('Start scraping...')
        for i in range(10):
            result = driver.scrape_all({'TaxNumber':f'{i:02}'},1)
            search_keys = str({'TaxNumber':f'{i:02}'})
            result = {search_keys:result}
            f.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        logger.info('Finished scraping.')
        
    """
    with open(r'.\output\result.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    """

# %%

# %%
