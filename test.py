"""Tests that the remote webdriver works."""
import unittest
from src.webdriver import Remote
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class RemoteFirefoxTestCase(unittest.TestCase):

    def setUp(self):
        self.browser = Remote(
            command_executor='http://127.0.0.1:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.FIREFOX)
        self.addCleanup(self.browser.quit)

    def testPageTitle(self):
        self.browser.get('http://www.google.com')
        self.assertIn('Google', self.browser.title)
        
    def testRun(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
