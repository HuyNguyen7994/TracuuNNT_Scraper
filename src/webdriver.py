import logging
from abc import abstractmethod
from unicodedata import normalize
from bs4 import BeautifulSoup as bs
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from .solverutility import (decode_image, preprocess_raw_image,
                            array_to_label, image_to_tensor, load_model)

logger = logging.getLogger(__name__)

def normalize_nav_string(string):
    return normalize('NFKC', string.text.strip())

class ProfileScraper(webdriver.Firefox):
    """Abstract class for scraper"""
    scopes = None
    site = None
    field_xpath = None
    def __init__(self, solver_path=None, headless=True, executable_path='geckodriver', *args, **kwargs):
        options = Options()
        options.headless = headless
        super().__init__(options=options, executable_path=executable_path, *args, **kwargs)
        if solver_path:
            self.set_solver(solver_path)
        else:
            self.solver = None
        if not all((self.scopes, self.site, self.field_xpath)):
            raise NotImplementedError("Attributes 'scopes', 'site', 'field_xpath' must all be implemented")
        
    def set_solver(self, path):
        """Set the solver to be used for captcha regconition. Must be a Tensorflow/Keras model that
        supports predict method"""
        logger.info('Loading solver at %s', path)
        self.solver = load_model(path)

    def _get_captcha_image(self):
        """Capture the captcha returned by server, then decode and preprocess to a (1,64,128,1) Tensor"""
        for request in self.requests[::-1]:
            if 'captcha' in request.url:
                img_content = request.response.body
                img = decode_image(img_content) # bytes to cv2 array
                img = preprocess_raw_image(img) # cv2 array to np array
                img = image_to_tensor(img) # np array to Tensor array
                return img

    def _answer_captcha(self):
        """Use model to predict characters in captcha"""
        img = self._get_captcha_image()
        answer = self.solver.predict(img)
        answer = ''.join(array_to_label(answer[0])) # since Tensor has an extra dimension
        return answer

    def _submit_captcha(self, answer, click=True):
        elem = self.find_element_by_xpath("//input[@id='captcha']")
        elem.send_keys(answer)
        elem = self.find_element_by_xpath("//input[@class='subBtn']")
        if click:
            elem.click()

    def _goto_detail(self, profile_index=0):
        """Go to nth-profile"""
        if profile_index == 0:
            self.find_element_by_xpath("//a[contains(@href, 'javascript:submitform')]").click()
        else:
            elems = self.find_elements_by_xpath("//a[contains(@href, 'javascript:submitform')]")
            elems[profile_index].click()

    def _goto_next_page(self, next_page):
        """Go to next page"""
        next_elem = self.find_element_by_xpath(f"//a[@href='javascript:gotoPage({next_page})']")
        next_elem.click()
        
    def _process_outer(self, soup):
        """Process the outermost page right after submitted the answer and received the first response"""
        text = soup.get_text()
        # all of these checks are expensive. Consider improving
        if "Bạn chưa nhập đủ các thông tin cần thiết." in text:
            return -1
        elif "Không tìm thấy người nộp thuế nào phù hợp." in text:
            return -1
        elif "Không tìm thấy kết quả." in text:
            return -1
        elif "Vui lòng nhập đúng mã xác nhận!" in text:
            return 0
        parse_result = []
        table = soup.find('table', attrs={'class':'ta_border'})
        rows = table.find_all('tr')
        rows = rows[:-1]
        headers = rows[0]
        headers = [normalize_nav_string(h) for h in headers.find_all('th')]
        contents = rows[1:]
        for data in contents:
            data = (normalize_nav_string(d) for d in data.find_all('td'))
            parse_result.append({h:d for h,d in zip(headers,data)})
        return parse_result

    def _parse_inner(self, soup):
        """Parse the inner table returned by clicking on a profile"""
        parse_result = []
        table = soup.find('table', attrs={'class':'ta_border'})
        headers = table.find_all('th')
        for header in headers:
            data = normalize_nav_string(header.find_next_sibling('td'))
            header = normalize_nav_string(header)
            parse_result.append({header:data})
        return parse_result

    def _send_search_terms(self, search_terms):
        """Send the search terms to approriate field. Accept dict-like object"""
        for term in search_terms:
            value = search_terms[term]
            xpath = self.field_xpath[term]
            elem = self.find_element_by_xpath(xpath)
            elem.clear() # field persists data during session, no matter where you are
            elem.send_keys(value)

    @abstractmethod
    def pinpoint(self, search_terms):
        """Method to scrape a single profile in detail"""

    @abstractmethod
    def sweep(self, search_terms):
        """Method to scrape multiple records in outer page"""
        
    def run(self, command, search_terms):
        """Main entry point for program"""
        commands = {'pinpoint': self.pinpoint,
                    'sweep': self.sweep}
        assert command in commands, "Invalid command. Supported command: 'pinpoint' for single profile in detail; 'sweep' for multiple profiles in outer page"
        return {'command':command,
                'result':commands[command](search_terms)}
        
class PersonalProfileScraper(ProfileScraper):
    """Scraper for personal site http://tracuunnt.gdt.gov.vn/tcnnt/mstcn.jsp"""
    scopes = ['.+captcha.png.+', '.+mstcn.jsp$']
    site = r'http://tracuunnt.gdt.gov.vn/tcnnt/mstcn.jsp'
    field_xpath = {'taxnum': "//input[@name='mst1']",
                   'name': "//input[@name='fullname1']",
                   'address': "//input[@name='address']",
                   'idnum':"//input[@name='cmt2']"}
    
    max_page = 2
    max_attempts = 5
    def pinpoint(self, search_terms):
        logger.info("Pinpoint a single profile ... Search terms=%s", str(search_terms))
        self.get(self.site)
        parse_result = {}
        attempt = 0
        
        self._send_search_terms(search_terms) # the site never clears its data in field so don't need to resend every loop
        while True:
            assert attempt <= self.max_attempts, """Maximum loop reached. Either captcha solver has problem or there are some edge cases that the program failed to catch. Please record the search terms and submit an issue on Github"""
            answer = self._answer_captcha()
            del self.requests # avoid catching previous request
            self._submit_captcha(answer)
            req = self.wait_for_request(r'.+/mstcn.jsp$')
            soup = bs(req.response.body,'lxml')
            outer = self._process_outer(soup)
            if outer == 0: # captcha failed
                attempt += 1
                continue
            elif outer == -1: # empty table
                logger.info('Finished scraping. Record is empty.')
                return None
            break
        
        parse_result['outer'] = outer
        del self.requests
        self._goto_detail()
        req = self.wait_for_request(r'.+/mstcn.jsp$')
        soup = bs(req.response.body,'lxml')
        parse_result['inner'] = self._parse_inner(soup)
        
        del self.requests # final clean before exit
        logger.info('Finished scraping. Record is present.')
        return parse_result
    
    def sweep(self, search_terms):
        logger.info("Sweep all profiles produced under search terms ... Search terms=%s", str(search_terms))
        self.get(self.site)
        parse_result = []
        attempt = 0
        next_page = 1
        
        self._send_search_terms(search_terms) # the site never clears its data in field so don't need to resend every loop
        while True:
            assert attempt <= self.max_attempts, """Maximum loop reached. Either captcha solver has problem or there are some edge cases that the program failed to catch. Please record the search terms and submit an issue on Github"""
            answer = self._answer_captcha()
            del self.requests # avoid catching previous request.
            if next_page == 1:
                self._submit_captcha(answer)
            else:
                self._submit_captcha(answer, False)
                self._goto_next_page(next_page)
            req = self.wait_for_request(r'.+/mstcn.jsp$')
            soup = bs(req.response.body,'lxml')
            outer = self._process_outer(soup)
            if outer == 0: # captcha failed
                attempt += 1
                if next_page > 1:
                    self.back()
                continue
            elif outer == -1: # empty table
                logger.info('Finished sweeping. Record is empty.')
                break
            parse_result += outer
            next_page += 1
            if len(outer) < 15 or next_page > self.max_page: # page contains max 15 profiles
                break
            attempt = 0
        logger.info('Finished sweeping. %d records found', len(parse_result))
        return {'outer':parse_result}

class BusinessProfileScraper(ProfileScraper):
    """Scraper for business site http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp"""
    scopes = ['.+captcha.png.+', '.+mstdn.jsp$', '.+doanhnghiepchuquan.jsp$', '.+chinhanh.jsp$',
              '.+tructhuoc.jsp$', '.+daidien.jsp$', '.+loaithue.jsp$', '.+nganhkinhdoanh.jsp$']
    site = r'http://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp'
    field_xpath = {'taxnum': "//input[@name='mst']",
                   'name': "//input[@name='fullname']",
                   'address': "//input[@name='address']",
                   'idnum':"//input[@name='cmt']"}
    
    def _parse_subtable(self, soup):
        parse_result = []
        soup = soup.find_all('tr')
        headers = soup[0]
        headers = [normalize_nav_string(h) for h in headers.find_all('th')]
        contents = soup[1:]
        for data in contents:
            data = (normalize_nav_string(d) for d in data.find_all('td'))
            parse_result.append({h:d for h,d in zip(headers,data)})
        return parse_result
    
    max_page = 9
    max_attempts = 5
    def pinpoint(self, search_terms):
        logger.info("Pinpoint a single profile ... Search terms=%s", str(search_terms))
        self.get(self.site)
        parse_result = {}
        attempt = 0
        
        self._send_search_terms(search_terms) # the site never clears its data in field so don't need to resend every loop
        while True:
            assert attempt <= self.max_attempts, """Maximum loop reached. Either captcha solver has problem or there are some edge cases that the program failed to catch. Please record the search terms and submit an issue on Github"""
            answer = self._answer_captcha()
            del self.requests # avoid catching previous request
            self._submit_captcha(answer)
            req = self.wait_for_request(r'.+/mstdn.jsp$')
            soup = bs(req.response.body,'lxml')
            outer = self._process_outer(soup)
            if outer == 0: # captcha failed
                attempt += 1
                continue
            elif outer == -1: # empty table
                logger.info('Finished scraping. Record is empty.')
                return None
            break
        
        parse_result['outer'] = outer
        del self.requests
        self._goto_detail()
        req = self.wait_for_request(r'.+/mstdn.jsp$')
        soup = bs(req.response.body,'lxml')
        parse_result['inner'] = self._parse_inner(soup)
        
        # working on subtables inside each profile
        sub = {}
        elems = self.find_elements_by_xpath("//input[@value='...']")
        elems_pattern = [r'.+/doanhnghiepchuquan.jsp$', r'.+/chinhanh.jsp$', r'.+/tructhuoc.jsp$', 
                         r'.+/daidien.jsp$', r'.+/loaithue.jsp$', r'.+/nganhkinhdoanh.jsp$']
        assert len(elems) == 6, 'There must be 6 sub-tables'
        for ele, pattern in zip(elems, elems_pattern):
            logger.debug('Scraping sub-table=%s...', pattern[3:-5])
            ele.click()
            req = self.wait_for_request(pattern)
            header = req.url.split('/')[-1][:-4]
            soup = bs(req.response.body, 'lxml')
            sub[header] = self._parse_subtable(soup)
        parse_result['sub'] = sub
        
        del self.requests # final clean before exit
        logger.info('Finished scraping. Record is present.')
        return parse_result
    
    def sweep(self, search_terms):
        logger.info("Sweep all profiles produced under search terms ... Search terms=%s", str(search_terms))
        self.get(self.site)
        parse_result = []
        attempt = 0
        next_page = 1
        
        self._send_search_terms(search_terms) # the site never clears its data in field so don't need to resend every loop
        while True:
            assert attempt <= self.max_attempts, """Maximum loop reached. Either captcha solver has problem or there are some edge cases that the program failed to catch. Please record the search terms and submit an issue on Github"""
            answer = self._answer_captcha()
            del self.requests # avoid catching previous request
            if next_page == 1:
                self._submit_captcha(answer)
            else:
                self._submit_captcha(answer, False)
                self._goto_next_page(next_page)
            req = self.wait_for_request(r'.+/mstdn.jsp$')
            soup = bs(req.response.body,'lxml')
            outer = self._process_outer(soup)
            if outer == 0: # captcha failed
                attempt += 1
                if next_page > 1:
                    self.back()
                continue
            elif outer == -1: # empty table
                logger.info('Finished sweeping. Record is empty.')
                break
            parse_result += outer
            next_page += 1
            if len(outer) < 15 or next_page > self.max_page: # page contains max 15 profiles
                break
            attempt = 0
        logger.info('Finished sweeping. %d records found', len(parse_result))
        return {'outer':parse_result}
