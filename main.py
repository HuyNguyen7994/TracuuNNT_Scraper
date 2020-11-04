# %%
import logging
import DriverFirefox
import tensorflow as tf
import argparse
import json

# initalize logger module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(r'.\log\running_log.csv')
file_handler.setLevel(logging.INFO)

log_formatter = logging.Formatter("%(relativeCreated)d,%(levelname)s,%(message)s")
file_handler.setFormatter(log_formatter)

logger.addHandler(file_handler)

# intialize argparser
# parser = argparse.ArgumentParser(description='Scrape records from http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp')

if __name__ == '__main__':
    logger.info('Loading solver model...')
    model = tf.keras.models.load_model(r'.\solver\CNN5_v10_acc_98.h5')
    logger.info('Initialising webdriver...')
    with DriverFirefox.DriverFirefox(model) as driver:
        logger.info('Start scraping.')
        result = driver.scrape_all({'Mã số thuế':'090018928'})
        result = {'result':result}
        logger.info('Finished scraping.')
    with open(r'.\output\result.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))

# %%
