''' NPP repositories module
contain functions for repository data processing
Repository is a store of a followed data:

HW - hardware module description library
LD - logigal device template
LN - logical node template (SCL)

DO - CDC template (SCL)
DA - data attribute template (SCL)
ENUM - enumeration template (SCL)

One repository is ?

'''

import lxml.etree as ET
import os, sys
import misc_utils as MU
from misc_utils import ns, nsURI, nsMap

def have(module, name):
    ''' check is named resource present in a repository module
    returns boolean
    '''
    if name is None or name == '': return False
    return True

class RepositoryError(Exception):
    pass

def get(module, name):
    ''' retrieves named resource from a repository module
    returns resource (XML)
    '''
    if not have(module, name): raise RepositoryError ('"%s" not found in "%s".' % (name, module))
    if module == "DO": f = lib.find('.//61850:DOType[@id="%s"]'% name, ns)    
    if module == "DA": f = lib.find('.//61850:DAType[@id="%s"]'% name, ns)    
    if module == "LN": f = lns.find('.//61850:LNodeType[@id="%s"]'% name, ns)
    if f is None: raise RepositoryError ('"%s" not found in "%s".' % (name, module))
    return f
    
libpath = os.path.dirname(os.path.abspath(__file__))
lib = ET.parse(os.path.join(libpath,'tst.xml')).getroot()
lns = ET.parse(os.path.join(libpath,'NPP HW LN templates.xml')).getroot()
