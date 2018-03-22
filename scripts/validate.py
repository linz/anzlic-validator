import os
import re
#import urllib2
import urllib.request as U_LIB

#from urllib2 import HTTPError, ProxyHandler, URLError
from urllib.request import HTTPError, ProxyHandler, URLError
from lxml import etree
from lxml.etree import XMLSyntaxError
from lxml.isoschematron import _schematron_root

from abc import ABCMeta, abstractmethod

#from cache import CacheHandler
from authenticate import Authentication

#Raw AS recipe is py2, modified as cache import above
#import importlib.util
#spec = importlib.util.spec_from_file_location('CacheHandler','../ActiveStateCode/recipes/Python/491261_Caching_throttling/recipe-491261.py')
#module = importlib.util.module_from_spec(spec)
#spec.loader.exec_module(module)

key = Authentication.apikey('~/.apikey3')

NSX = {'xlink'   : 'http://www.w3.org/1999/xlink',
       'xsi'     : 'http://www.w3.org/2001/XMLSchema-instance',  
       'dc'      : 'http://purl.org/dc/elements/1.1/',
       'g'       : 'http://data.linz.govt.nz/ns/g', 
       'r'       : 'http://data.linz.govt.nz/ns/r', 
       'ows'     : 'http://www.opengis.net/ows/1.1', 
       'csw'     : 'http://www.opengis.net/cat/csw/2.0.2',
       'wms'     : 'http://www.opengis.net/wms',
       'ogc'     : 'http://www.opengis.net/ogc',
       'gco'     : 'http://www.isotc211.org/2005/gco',
       'gmd'     : 'http://www.isotc211.org/2005/gmd',
       'gmx'     : 'http://www.isotc211.org/2005/gmx',
       'gsr'     : 'http://www.isotc211.org/2005/gsr',
       'gss'     : 'http://www.isotc211.org/2005/gss',
       'gts'     : 'http://www.isotc211.org/2005/gts',
       'f'       : 'http://www.w3.org/2005/Atom',
       'null'    : '',
       'wfs'     : 'http://www.opengis.net/wfs/2.0',
       'gml'     : 'http://www.opengis.net/gml/3.2',
       'v'       : 'http://wfs.data.linz.govt.nz',
       'lnz'     : 'http://data.linz.govt.nz'}

class SCHMD(object):
    
    __metaclass__ = ABCMeta
    
    _sch = None
    _md = None
    
    @property
    def sch(self): return self._sch
    @sch.setter
    def sch(self,value): self._sch = value    
    
    @property
    def md(self): return self._md
    @md.setter
    def md(self,value): self._md = value
    
    sch = None
    md = None
    
    def __init__(self):
        self.schema()
        #self.metadata()
        
    @abstractmethod
    def schema(self):
        '''schema init'''    
        
    @abstractmethod
    def metadata(self):
        '''schema init'''
        
class Local(SCHMD):
    
    SP = '../../ANZLIC-XML/standards.iso.org/iso/19110/gfc/1.1/'
    TP = '../tests/data/'
    
    def __init__(self):
        super(Local,self).__init__()
    
    def schema(self):
        sch_name = 'featureCatalogue.xsd'#metadataEntity?
        sch_path = os.path.abspath(os.path.join(os.path.dirname(__file__),self.SP,sch_name))
        
        sch_doc = etree.parse(sch_path)
        self.sch = etree.XMLSchema(sch_doc)
        
    def metadata(self):
        md_name = 'nz-primary-parcels.iso.xml'    
        md_path = os.path.abspath(os.path.join(os.path.dirname(__file__),self.TP,md_name))
        self.md = etree.parse(md_path)

class Remote(SCHMD):
    
    def __init__(self):
        super(Remote,self).__init__()  
    
    def schema(self):
        '''Fetch and parse the ANZLIC metadata schema'''
        sch_name = 'http://www.isotc211.org/2005/gmd/metadataEntity.xsd'
        sch_handle = U_LIB.urlopen(sch_name)
        
        sch_doc = etree.parse(sch_handle)
        self.sch = etree.XMLSchema(sch_doc)    
        
    def metadata(self,lid):
        '''Get the default metadata for each layer identified by layer id'''
        md_name = 'https://data.linz.govt.nz/layer/{lid}/metadata/iso/xml/'    

        try:
            md_handle = U_LIB.urlopen(md_name.format(lid=lid[0]))
            self.md = etree.parse(md_handle)
            return True
        except XMLSyntaxError as xse:
            #Private layers are inaccessible
            if 'https://id.koordinates.com/login' in md_handle.url:
                print ('ERROR inaccessible private layer {}.\n{}'.format(lid,xse))
            else:
                print ('ERROR parsing metadata document {}.\n{}'.format(lid,xse))
        except HTTPError as he:
            print ('ERROR layer metadata unavailable {}.\n{}'.format(lid,he))
        except Exception as e:
            #catch any other error and continue, may not be what is wanted
            print ('ERROR processing {}.\n{}'.format(lid,e))
        return False

    def getids(self,wxs):
        '''Read the layer and table IDS from the getcapabilities for the WFS and WMS service types'''

        #default capabilities url
        cap1 = 'http://data.linz.govt.nz/services;key={key}/{wxs}?service={wxs}&request=GetCapabilities'
        #csw capabilities url
        cap2 = 'http://data.linz.govt.nz/services;key={key}/{wxs}?service={wxs}&request=GetCapabilities'
        #wfs/wms feature paths
        ftx = {'wfs':{'p':'//wfs:FeatureType','n':'./wfs:Name','t':'./wfs:Title'},
               'wms':{'p':'/Capability/Layer/Layer','n':'./Name','t':'./Title'}
               }[wxs]

        ret = {'layer':(),'table':()}
        content = None
        try:
            content = U_LIB.urlopen(cap1.format(key=key,wxs=wxs))
            tree = etree.parse(content)
            #find all featuretypes
            for ft in tree.findall(ftx['p'],namespaces=NSX):
                #regex out id and table/layer type
                match = re.search('(layer|table)-(\d+)',ft.find(ftx['n'], namespaces=NSX).text)
                lort = match.group(1)
                name = int(match.group(2))
                title = ft.find(ftx['t'], namespaces=NSX).text
                ret[lort] += ((name,title),)
        except HTTPError as he:
            print ('ERROR failed to get {} layer ids {}.\n{}'.format(wxs,he))
            raise
        #just return layer for now
        return ret['layer']
    
def conditionalTest(md):
    
    GMD = '{http://www.isotc211.org/2005/gmd}'
    GCO = '{http://www.isotc211.org/2005/gco}'
    DATASET = False
        
    tree = md
    root = tree.getroot()
        
    for element in root.find(GMD+'hierarchyLevel'):
        if element.get('codeListValue') == None:
            # 'ERROR: No Hierarchy Level Declared'
            return False
        elif element.get('codeListValue') == 'dataset':
            DATASET = True  
    
    if DATASET:
        IDIN = root.find(GMD+'identificationInfo')
        for MDDID in IDIN.iter(GMD+'MD_DataIdentification'):
            if MDDID.find(GMD+'topicCategory/'+GMD+'MD_TopicCategoryCode') is None:
                # 'ERROR: No Topic Category Declared'
                return False
            if MDDID.find(GMD+'extent') is None:
                # 'ERROR: No Extent Declared'
                return False
            else:
                EX = MDDID.find(GMD+'extent/'+GMD+'EX_Extent/'+GMD+'geographicElement')
                if EX.find(GMD+'EX_GeographicBoundingBox') is None and EX.find(GMD+'EX_GeographicDescription') is None:
                    #'ERROR: No Geographic Bounding Box or Geographic Description Declared'
                    return False

    if root.find(GMD+'language/'+GCO+'CharacterString') is None:
       return False
   
    if root.find(GMD+'characterSet/'+GMD+'MD_CharacterSetCode') is None:
       return False
   
    MDDID = root.find(GMD+'identificationInfo/'+GMD+'MD_DataIdentification')
    if MDDID.find(GMD+'language/'+GCO+'CharacterString') is None:
       return False
   
    if MDDID.find(GMD+'characterSet/'+GMD+'MD_CharacterSetCode') is None:
       return False
    
    return True

def _testvals():  
    return [(i,'succeed') for i in ('50772','50845','50789')] \
        + [(i,'fail') for i in ('50813','51362','51920')] \
        + [(i,'error') for i in ('52552',)]
        
def main():
    
    #v1 = Local()
    #print(v1.sch.validate(v1.md))]

    v2 = Remote()
    wfsi = v2.getids('wms')
    #for lid in _testvals():
    for lid in wfsi:
        if v2.metadata(lid):
            if v2.sch.validate(v2.md):
                print(lid,'CT',conditionalTest(v2.md))
            else:
                print(lid,'Validate',False)
        else:
            print(lid,'MD',False)
    
if __name__ == "__main__":
    main()
