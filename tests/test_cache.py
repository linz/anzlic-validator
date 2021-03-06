
import unittest
import os
import sys
import urllib
from numpy.random import sample

script_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'../scripts'))
sys.path.append(script_path)

from validate import Remote, Local,ValidatorParseException,ValidatorAccessException
from cache import CacheHandler,ThrottlingProcessor, CACHE_HEADER,THROTTLE_HEADER
from authenticate import Authentication


TEST_CACHE = '.test_cache'
TEST_URL = 'http://www.internic.net/'
            
class Test_1_setup(unittest.TestCase):
    
    
    def setUp(self):
        self.ch = CacheHandler(TEST_CACHE)
        
    def tearDown(self):
        self.ch._flush(TEST_CACHE)
        del self.ch
        
    def test_10_raw(self):
        '''Compare reqular vs cached response attrs'''
        req = urllib.request.Request(TEST_URL)
        httpresp = urllib.request.urlopen(req)
        cacheresp = self.ch.default_open(req)
        self.assertTrue(
            all( [httpresp.__getattribute__(a) == cacheresp.__getattribute__(a) for a in ('code','msg','url')] )
        )
class Test_2_canned(unittest.TestCase):
    
    def setUp(self):
        # Clear cache
        CacheHandler._flush(TEST_CACHE)
        # Clear throttling timeouts
        ThrottlingProcessor().lastRequestTime.clear()  
        
    def tearDown(self):
        pass

    def test_10_cache(self):
        opener = urllib.request.build_opener(CacheHandler(TEST_CACHE))
        resp = opener.open(TEST_URL)
        self.assertTrue(CACHE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(CACHE_HEADER))
        resp = opener.open(TEST_URL)
        self.assertTrue(CACHE_HEADER in resp.info(),'Cannot find header {} in response'.format(CACHE_HEADER))
        
    def test_20_throttle(self):
        opener = urllib.request.build_opener(ThrottlingProcessor(30))
        resp = opener.open(TEST_URL)
        self.assertTrue(THROTTLE_HEADER not in resp.info(),'Unexpectedly found header {} in response'.format(THROTTLE_HEADER))
        resp = opener.open(TEST_URL)
        self.assertTrue(THROTTLE_HEADER in resp.info(),'Cannot find header {} in response'.format(THROTTLE_HEADER))
 
    def test_30_combined(self):
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
