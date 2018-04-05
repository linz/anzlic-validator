
import unittest
import os
import sys
import urllib.request
from numpy.random import sample

sys.path.append('../scripts/')

from validate import Remote, Local,ValidatorParseException,ValidatorAccessException
from cache import CacheHandler,ThrottlingProcessor, CACHE_HEADER,THROTTLE_HEADER
from authenticate import Authentication


TEST_CACHE = '.testcache'
TEST_URL = 'http://www.internic.net/'
            
class Test_1_setup(unittest.TestCase):
    
    
    def setUp(self):
        self.ch = CacheHandler(TEST_CACHE)
        
    def tearDown(self):
        self.ch._flush(TEST_CACHE)
        del self.ch
        
    def test_1_raw(self):
        req = urllib.request.Request(TEST_URL)
        self.ch.default_open(req)
        
class Test_2_canned(unittest.TestCase):
    
    def setUp(self):
        # Clear cache
        CacheHandler._flush(TEST_CACHE)
        # Clear throttling timeouts
        ThrottlingProcessor().lastRequestTime.clear()    
        
    def tearDown(self):
        pass

    def test_1_cache(self):
        opener = urllib.request.build_opener(CacheHandler(TEST_CACHE))
        resp = opener.open(TEST_URL)
        self.assertTrue(CACHE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(CACHE_HEADER))
        resp = opener.open(TEST_URL)
        self.assertTrue(CACHE_HEADER in resp.info(),'Cannot find header {} in response'.format(CACHE_HEADER))
        
    def test_2_throttle(self):
        opener = urllib.request.build_opener(ThrottlingProcessor(30))
        resp = opener.open(TEST_URL)
        self.assertTrue(THROTTLE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(THROTTLE_HEADER))
        resp = opener.open(TEST_URL)
        self.assertTrue(THROTTLE_HEADER in resp.info(),'Cannot find header {} in response'.format(THROTTLE_HEADER))
 
    def test_3_combined(self):
        opener = urllib.request.build_opener(CacheHandler(TEST_CACHE), ThrottlingProcessor(30))
        resp = opener.open(TEST_URL)
        self.assertTrue(CACHE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(CACHE_HEADER))
        self.assertTrue(THROTTLE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(THROTTLE_HEADER))
        resp = opener.open(TEST_URL)
        self.assertTrue(CACHE_HEADER in resp.info(),'Cannot find header {} in response'.format(CACHE_HEADER))
        self.assertTrue(THROTTLE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(THROTTLE_HEADER))



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLDSRead']
    unittest.main()