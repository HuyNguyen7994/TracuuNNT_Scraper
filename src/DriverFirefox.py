# %%
import logging
from unicodedata import normalize
import cv2
import numpy as np
import tensorflow as tf
from bs4 import BeautifulSoup as bs
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from .solver_helper import preprocess_raw_image, array_to_label, image_to_tensor

logger = logging.getLogger(__name__)

class business_scraper(webdriver.Firefox):
    def __init__(self, solver_path=None, headless=True, executable_path='geckodriver', *args, **kwargs):
        options = Options()
        options.headless = headless
        super().__init__(options=options, executable_path=executable_path, *args, **kwargs)
        if solver_path:
            self.set_solver(solver_path)
        else:
            self.solver = None
        self.site = r'http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp'
        self.scopes = ['.+captcha.png.+', '.+mstdn.jsp$', '.+doanhnghiepchuquan.jsp$', '.+chinhanh.jsp$',
                       '.+tructhuoc.jsp$', '.+daidien.jsp$', '.+loaithue.jsp$', '.+nganhkinhdoanh.jsp$']
    
    def set_solver(self, path):
        """set solver to be used for breaking captcha. Must support
        input in form of (1,64,128,1) (bs,height,width,channel)
        and method predict() to return one-hot vector array"""
        logger.info('Loading solver at %s', path)
        self.solver = tf.keras.models.load_model(path)
    
    def _decode_image(self, bytes_string):
        img = cv2.imdecode(np.frombuffer(bytes_string, np.uint8),-1)
        img = img[:,:,-1]
        return img

    def _parse_summary_table(self, table):
        """Parse summary after successful captcha"""
        if "Không tìm thấy người nộp thuế nào phù hợp." in table.get_text():
            return None
        parse_result = []
        rows = table.find_all('tr')
        rows = rows[:-1]
        headers = rows[0]
        # check once to see if data exists in the data
        
        headers = [h.text.strip() for h in headers.find_all('th')]
        contents = rows[1:]
        for data in contents:
            data = (d.text.strip() for d in data.find_all('td'))
            parse_result.append({h:d for h,d in zip(headers,data)})
            
        return parse_result
    
    def _get_captcha_image(self):
        for request in self.requests[::-1]:
            if 'captcha' in request.url:
                img_content = request.response.body
                img = self._decode_image(img_content)
                return img

    def _process_captcha(self):
        image = self._get_captcha_image()
        image = preprocess_raw_image(image)
        image = image_to_tensor(image)
        image = tf.image.resize_with_pad(image, 64, 128)
        answer = self.solver.predict(image)
        answer = ''.join(array_to_label(answer[0]))

        return answer

    def _send_search_terms(self, search_dict):
        name2xpath = {'TaxNumber': "//input[@name='mst']",
                      'Name': "//input[@name='fullname']",
                      'Address': "//input[@name='address']",
                      'IdNumber':"//input[@name='cmt']"}
        for term in search_dict:
            xpath = name2xpath[term]
            elem = self.find_element_by_xpath(xpath)
            elem.clear()
            elem.send_keys(search_dict[term])
        return None

    def _submit_captcha(self, answer, click=True):
        elem = self.find_element_by_xpath("//input[@id='captcha']")
        elem.send_keys(answer)
        if click:
            elem = self.find_element_by_xpath("//input[@class='subBtn']")
            elem.click()
    
    def _go_to_1st_record(self):
        self.find_element_by_xpath("//a[contains(@href, 'javascript:submitform')]").click()
    
    def _parse_main_table(self):
        result = []
        
        soup = bs(self.page_source, 'lxml')
        soup = soup.find('table', attrs={'class':'ta_border'})
        soup = soup.find_all('th')
        
        for s in soup:
            header = normalize('NFKC', s.text.strip())
            data = normalize('NFKC', s.find_next_sibling('td').text.strip())
            result.append({header:data})
            
        return result
        
    def _parse_sub_table(self, soup):
        parse_result = []
        soup = soup.find_all('tr')
        headers = soup[0]
        headers = [h.text.strip() for h in headers.find_all('th')]
        contents = soup[1:]
        for data in contents:
            data = (d.text.strip() for d in data.find_all('td'))
            parse_result.append({h:d for h,d in zip(headers,data)})
            
        return parse_result
        
    def scrape(self, search_terms, max_attempts=5):
        """search and scrape the first record returned by provided search terms

        Args:
            search_terms (dict): Accepted dict_key: ('TaxNumber', 'Name', 'Address', 'IdNumber')
            max_attempts (int, optional): Maximum re-tries. To avoid infinite loop. Defaults to 5.

        Returns:
            if record exists: json-like dict
            if record not exists: None
        """
        logger.info('Scraping single record... Provided search terms=%s', str(search_terms))
        self.get(self.site) # reset the site
        parse_result = {}
        attempt = 0
        
        self._send_search_terms(search_terms)
        while True:
            assert attempt < max_attempts, 'Maximum attempts reached'
            logger.debug('Solving the captcha...')
            answer = self._process_captcha()
            del self.requests # avoid catching previous request
            self._submit_captcha(answer)
            req = self.wait_for_request(r'.+/mstdn.jsp$')
            table_soup = bs(req.response.body,'lxml').find('table', attrs={'class':'ta_border'})
            if table_soup: # if table exists (failed captcha otherwise)
                logger.debug('Captcha solved. Start scraping summary page...')
                summary = self._parse_summary_table(table_soup)
                logger.debug('Finished scraping summary.')
                if summary: # if table is empty (no result otherwise)
                    self._go_to_1st_record()
                    break
                else:
                    logger.info('Finished scraping. Record is empty.')
                    return None
            else:
                attempt += 1
                continue
        
        parse_result['summary'] = summary
        logger.debug('Scraping main table of 1st result...')
        parse_result['main'] = self._parse_main_table()
        logger.debug('Finished scraping main table.')
        
        elems = self.find_elements_by_xpath("//input[@value='...']")
        elems_pattern = [r'.+/doanhnghiepchuquan.jsp$', r'.+/chinhanh.jsp$', r'.+/tructhuoc.jsp$', 
                      r'.+/daidien.jsp$', r'.+/loaithue.jsp$', r'.+/nganhkinhdoanh.jsp$']
        assert len(elems) == 6, 'There must be 6 sub-tables'
        for ele, pattern in zip(elems, elems_pattern):
            logger.debug('Scraping sub-table=%s...', pattern[3:-5])
            ele.click()
            #req = self.last_request
            req = self.wait_for_request(pattern)
            header = req.url.split('/')[-1][:-4]
            parse_result[header] = self._parse_sub_table(bs(req.response.body, 'lxml'))
        logger.debug('Finished scraping sub-tables.')
     
        del self.requests # clear requests history
        logger.info('Finished scraping. Record is present.')
        return parse_result
                
    def scan(self, search_terms, max_page=10, max_attempts=5):
        """unstable feature - scan all pages yielded from search terms
        will not go into any specific record
        the site breaks after page 10 so the script stops there

        Args:
            search_terms ([type]): [description]
            max_attempts (int, optional): [description]. Defaults to 5.
            max_page (int, optional): if you want to stop the script early

        Returns:
            [array]: all items appear on the summary page, up to page 10
        """
        # TODO: handle next page scraping3
        # href="javascript:gotoPage(3)"
        logger.info('Scanning for possible records... Provided search terms=%s', str(search_terms))
        self.get(self.site) # reset the site
        attempt = 0
        parse_result = []
        next_page = 1
        
        self._send_search_terms(search_terms)
        while True:
            assert attempt < max_attempts, 'Maximum attempts reached'
            if next_page == 1: # on first page
                answer = self._process_captcha()
                del self.requests # avoid catching previous request
                self._submit_captcha(answer)
                req = self.wait_for_request(r'.+/mstdn.jsp$')
                table_soup = bs(req.response.body,'lxml').find('table', attrs={'class':'ta_border'})
                if table_soup: # if table exists (failed captcha otherwise)
                    summary = self._parse_summary_table(table_soup)
                    if summary: # if table is empty (no result otherwise)
                        parse_result += summary
                        if len(summary) < 15: # page contains maximum 15 result
                            break
                        next_page += 1
                        attempt = 0
                        continue
                    else:
                        break
                else:
                    attempt += 1
                    continue
            
            elif next_page >= 2 and next_page <= max_page and next_page < 10: # the site itself breaks after 10 page lmao
                answer = self._process_captcha()
                del self.requests # avoid catching previous request
                self._submit_captcha(answer, False)
                next_elem = self.find_element_by_xpath(f"//a[@href='javascript:gotoPage({next_page})']")
                next_elem.click()
                req = self.wait_for_request(r'.+/mstdn.jsp$')
                table_soup = bs(req.response.body,'lxml').find('table', attrs={'class':'ta_border'})
                if table_soup: # if table exists (failed captcha otherwise)
                    summary = self._parse_summary_table(table_soup)
                    if summary: # if table is empty (no result otherwise)
                        parse_result += summary
                        if len(summary) < 15: # page contains maximum 15 result
                            break
                        next_page += 1
                        attempt = 0
                        continue
                    else:
                        break
                else:
                    attempt += 1
                    self.back()
                    continue
            else:
                break
        logger.info('Finished scanning. %d records found', len(parse_result))
        return parse_result
    
    def scrape_all(self, search_terms, max_page=10, max_attempts=5):
        """scrape all records returned under search terms"""
        records = self.scan(search_terms, max_page=max_page, max_attempts=max_attempts)
        updated_records = []
        for record in records:
            record_id = record['MST']
            parse_result = self.scrape({'TaxNumber':record_id}, max_attempts=max_attempts)
            updated_records.append(parse_result)
        return {'scan': records, 'scrape': updated_records}

class personal_scraper(webdriver.Firefox):
    def __init__(self, solver_path=None, headless=False, executable_path='geckodriver', *args, **kwargs):
        options = Options()
        options.headless = headless
        super().__init__(options=options, executable_path=executable_path, *args, **kwargs)
        if solver_path:
            self.set_solver(solver_path)
        else:
            self.solver = None
        self.site = r'http://tracuunnt.gdt.gov.vn/tcnnt/mstcn.jsp'
        self.scopes = ['.+captcha.png.+', '.+mstcn.jsp$']
    
    def set_solver(self, path):
        """set solver to be used for breaking captcha. Must support
        input in form of (1,64,128,1) (bs,height,width,channel)
        and method predict() to return one-hot vector array"""
        logger.info('Loading solver at %s', path)
        self.solver = tf.keras.models.load_model(path)
    
    def _decode_image(self, bytes_string):
        img = cv2.imdecode(np.frombuffer(bytes_string, np.uint8),-1)
        img = img[:,:,-1]
        return img

    def _parse_summary_table(self, table):
        """Parse summary after successful captcha"""
        if "Không tìm thấy người nộp thuế nào phù hợp." in table.get_text():
            return None
        parse_result = []
        rows = table.find_all('tr')
        rows = rows[:-1]
        headers = rows[0]
        # check once to see if data exists in the data
        
        headers = [h.text.strip() for h in headers.find_all('th')]
        contents = rows[1:]
        for data in contents:
            data = (d.text.strip() for d in data.find_all('td'))
            parse_result.append({h:d for h,d in zip(headers,data)})
            
        return parse_result
    
    def _get_captcha_image(self):
        for request in self.requests[::-1]:
            if 'captcha' in request.url:
                img_content = request.response.body
                img = self._decode_image(img_content)
                return img

    def _process_captcha(self):
        image = self._get_captcha_image()
        image = preprocess_raw_image(image)
        image = image_to_tensor(image)
        image = tf.image.resize_with_pad(image, 64, 128)
        answer = self.solver.predict(image)
        answer = ''.join(array_to_label(answer[0]))

        return answer

    def _send_search_terms(self, search_dict):
        name2xpath = {'TaxNumber': "//input[@name='mst1']",
                      'Name': "//input[@name='fullname1']",
                      'Address': "//input[@name='address']",
                      'IdNumber':"//input[@name='cmt2']"}
        for term in search_dict:
            xpath = name2xpath[term]
            elem = self.find_element_by_xpath(xpath)
            elem.clear()
            elem.send_keys(search_dict[term])
        return None

    def _submit_captcha(self, answer, click=True):
        elem = self.find_element_by_xpath("//input[@id='captcha']")
        elem.send_keys(answer)
        if click:
            elem = self.find_element_by_xpath("//input[@class='subBtn']")
            elem.click()
    
    def _go_to_1st_record(self):
        self.find_element_by_xpath("//a[contains(@href, 'javascript:submitform')]").click()
    
    def _parse_main_table(self):
        result = []
        
        soup = bs(self.page_source, 'lxml')
        soup = soup.find('table', attrs={'class':'ta_border'})
        soup = soup.find_all('th')
        
        for s in soup:
            header = normalize('NFKC', s.text.strip())
            data = normalize('NFKC', s.find_next_sibling('td').text.strip())
            result.append({header:data})
            
        return result

    def scrape(self, search_terms, max_attempts=5):
        """search and scrape the first record returned by provided search terms

        Args:
            search_terms (dict): Accepted dict_key: ('TaxNumber', 'Name', 'Address', 'IdNumber')
            max_attempts (int, optional): Maximum re-tries. To avoid infinite loop. Defaults to 5.

        Returns:
            if record exists: json-like dict
            if record not exists: None
        """
        logger.info('Scraping single record... Provided search terms=%s', str(search_terms))
        self.get(self.site) # reset the site
        parse_result = {}
        attempt = 0
        
        self._send_search_terms(search_terms)
        while True:
            assert attempt < max_attempts, 'Maximum attempts reached'
            logger.debug('Solving the captcha...')
            answer = self._process_captcha()
            del self.requests # avoid catching previous request
            self._submit_captcha(answer)
            req = self.wait_for_request(r'.+/mstcn.jsp$')
            table_soup = bs(req.response.body,'lxml').find('table', attrs={'class':'ta_border'})
            if table_soup: # if table exists (failed captcha otherwise)
                logger.debug('Captcha solved. Start scraping summary page...')
                summary = self._parse_summary_table(table_soup)
                logger.debug('Finished scraping summary.')
                if summary: # if table is empty (no result otherwise)
                    self._go_to_1st_record()
                    break
                else:
                    logger.info('Finished scraping. Record is empty.')
                    return None
            else:
                attempt += 1
                continue
        
        parse_result['summary'] = summary
        logger.debug('Scraping main table of 1st result...')
        parse_result['main'] = self._parse_main_table()
        logger.debug('Finished scraping main table.')
 
        del self.requests # clear requests history
        logger.info('Finished scraping. Record is present.')
        return parse_result
                
    def scan(self, search_terms, max_page=2, max_attempts=5):
        """unstable feature - scan all pages yielded from search terms
        will not go into any specific record
        the site breaks after page 2 so the script stops there

        Args:
            search_terms ([type]): [description]
            max_attempts (int, optional): [description]. Defaults to 5.
            max_page (int, optional): if you want to stop the script early

        Returns:
            [array]: all items appear on the summary page, up to page 10
        """
        # TODO: handle next page scraping3
        # href="javascript:gotoPage(3)"
        logger.info('Scanning for possible records... Provided search terms=%s', str(search_terms))
        self.get(self.site) # reset the site
        attempt = 0
        parse_result = []
        next_page = 1
        
        self._send_search_terms(search_terms)
        while True:
            assert attempt < max_attempts, 'Maximum attempts reached'
            if next_page == 1: # on first page
                answer = self._process_captcha()
                del self.requests # avoid catching previous request
                self._submit_captcha(answer)
                req = self.wait_for_request(r'.+/mstcn.jsp$')
                table_soup = bs(req.response.body,'lxml').find('table', attrs={'class':'ta_border'})
                if table_soup: # if table exists (failed captcha otherwise)
                    summary = self._parse_summary_table(table_soup)
                    if summary: # if table is empty (no result otherwise)
                        parse_result += summary
                        if len(summary) < 15: # page contains maximum 15 result
                            break
                        next_page += 1
                        attempt = 0
                        continue
                    else:
                        break
                else:
                    attempt += 1
                    continue
            
            elif next_page == 2: # the site itself breaks after 2 pages sigh...
                answer = self._process_captcha()
                del self.requests # avoid catching previous request
                self._submit_captcha(answer, False)
                next_elem = self.find_element_by_xpath(f"//a[@href='javascript:gotoPage({next_page})']")
                next_elem.click()
                req = self.wait_for_request(r'.+/mstcn.jsp$')
                table_soup = bs(req.response.body,'lxml').find('table', attrs={'class':'ta_border'})
                if table_soup: # if table exists (failed captcha otherwise)
                    summary = self._parse_summary_table(table_soup)
                    if summary: # if table is empty (no result otherwise)
                        parse_result += summary
                        if len(summary) < 15: # page contains maximum 15 result
                            break
                        next_page += 1
                        attempt = 0
                        continue
                    else:
                        break
                else:
                    attempt += 1
                    self.back()
                    continue
            else:
                break
        logger.info('Finished scanning. %d records found', len(parse_result))
        return parse_result
    
    def scrape_all(self, search_terms, max_page=10, max_attempts=5):
        """scrape all records returned under search terms"""
        records = self.scan(search_terms, max_page=max_page, max_attempts=max_attempts)
        updated_records = []
        for record in records:
            record_id = record['Mã số thuế']
            parse_result = self.scrape({'TaxNumber':record_id}, max_attempts=max_attempts)
            updated_records.append(parse_result)
        return {'scan': records, 'scrape': updated_records}
# %%
# return Bạn chưa nhập đủ các thông tin cần thiết. if insufficient data is provided