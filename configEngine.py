import lxml.etree as ET
import os, sys
import hwLibEngine as HWL
from hwLibEngine import lang
from uuid import uuid4 as uid
import misc_utils as MU
from misc_utils import ns, nsURI, nsMap

hwConfig = None

# fileops

ROOT_ID = '00000000-0000-4000-8000-000000000000'

def newConfig():
    global hwConfig
    hwConfig = ET.Element(nsURI+'HWConfig', nsmap=nsMap)
    sysroot = ET.SubElement(hwConfig,nsURI+'Unit', nsmap=nsMap )
    sysroot.attrib.update({'id' : ROOT_ID,
                           'lib' : 'ROOT-1-0',
                           'addr' : '',
                           'tag' : 'ROOT'})
    

def loadConfig(path, filename):
    global hwConfig
    tree = ET.parse(os.path.join(path,filename))
    hwConfig = tree.getroot()
    

def saveConfig(path, filename):
    tree = ET.ElementTree(hwConfig)
    MU.indentXML(hwConfig)
    tree.write(os.path.join(path, filename), encoding="utf-8", xml_declaration=True) 

# config status

def _calcProp(name):
    val = 0
    for unit in hwConfig.findall('.//npp:Unit', ns):
        val += len (HWL.hwLibrary.findall(
            './npp:Unit[@id="%s"]/npp:Property[@name="%s"]' % (unit.get('lib'), name), ns))
    return val

def listReqs():
    reqlist = list()
    for unit in hwConfig.findall('.//npp:Unit', ns):
        libId = unit.get('lib')
        for r in HWL.hwLibrary.findall(
            './npp:Unit[@id="%s"]/npp:Required' % libId, ns):
            reqlist.append({
                'unit' : unit.get('id'),
                'property' : r.get('property'),
                'min' : int(r.get('min')) if 'min' in r.keys() else 0,
                'max' : int(r.get('max')) if 'max' in r.keys() else sys.maxsize,
                'value' : _calcProp(r.get('property'))})
    return reqlist

def _calcRes(name):
    used = 0
    avail = 0
    for unit in hwConfig.findall('.//npp:Unit', ns):
        libId = unit.get('lib')
        used += sum( int (r.get('val'))
                     for r in HWL.hwLibrary.findall(
                         './npp:Unit[@id="%s"]/npp:Uses[@resource="%s"]' % (libId, name), ns))
        avail += sum( int (r.get('val'))
                     for r in HWL.hwLibrary.findall(
                         './npp:Unit[@id="%s"]/npp:Resource[@name="%s"]' % (libId, name), ns))
    return name, used, avail
    
def listResources():
    reslist = set()
    for unit in hwConfig.findall('.//npp:Unit', ns):
        libId = unit.get('lib')
        for r in HWL.hwLibrary.findall(
            './npp:Unit[@id="%s"]/npp:Resource' % libId, ns):
            reslist.add(r.get('name'))
        for r in HWL.hwLibrary.findall(
            './npp:Unit[@id="%s"]/npp:Uses' % libId, ns):
            reslist.add(r.get('resource'))
    return [dict(zip(('resource', 'used', 'available'),
                     _calcRes(r)))
            for r in reslist]

def getStatus():
    res = all( r.get('used') <= r.get('available')
               for r in listResources())
    req = all( r.get('min') <= r.get('value') <= r.get('max')
               for r in listReqs())
    return {'Requirements' : req,
            'Resources': res}


# aiming units

def _isConnectable(conn, slot):
    unit_type = slot.getparent().get('type')
    req_type = conn.get('unit') if 'unit' in conn.attrib else unit_type
    return all([
        unit_type == req_type, #required unit match
        slot.get('type') == conn.get('slot'), #slot is a same type
        int(slot.get('ver')) >= int(conn.get('ver'))]) # slot is newer (back-compatible)

def canConnectUnit(libId, unitId, addr):
    # check is library unit can be connected to a selected slot
    connector = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' % libId, ns)
    unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns)
    slot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@addr="%s"]' %
                              (unit.get('lib'), addr) , ns)
    connected = unit.find('./npp:Unit[@addr="%s"]' % addr, ns)
    return connected is None and _isConnectable(connector, slot)

# working with units

DUMP_FULL = True
DUMP_SHORT = False
DUMP_ONE = False
DUMP_ALL = True

def _dumpSlots(unit, match, recurse, mode):
    
    def subdata(unit, match, slot, recurse, mode):
        subunit = unit.find('./npp:Unit[@addr="%s"]' % slot.get('addr'), ns)
        if subunit is None:
            return 'FREE' if match is not None and _isConnectable(match, slot) else None
        return _dumpUnit(subunit, match, recurse, mode) if recurse else subunit.get('id')
        
    return [ {'addr' : slot.get('addr'),
              'type' : slot.get('type'),
              'unit' : subdata(unit, match, slot, recurse, mode)}
        for slot in HWL.hwLibrary.findall('./npp:Unit[@id="%s"]/npp:Slot' % unit.get('lib'), ns)]

def _dumpUnit(unit, match, recurse, mode):
    values = {'unit' : unit.get('id'),
              'lib' : unit.get('lib'),
              'slots' : _dumpSlots(unit, match, recurse, mode)}
    if mode:
        values.update(HWL.getUnit(unit.get('lib')))
        values.pop('id')
    else:
        values['type'] = HWL.getUnit(unit.get('lib')).get('type')
    values['tag'] = unit.get('tag')
    return values

def listUnits(matchlib, mode = DUMP_SHORT):
    match = None if matchlib is None else HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' % matchlib, ns)
    return _dumpUnit(hwConfig.find('.//npp:Unit[@id="%s"]' % ROOT_ID, ns), match, DUMP_ALL, mode)

def getUnit(unitId, matchlib, mode = DUMP_FULL):
    match = None if matchlib is None else HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' % matchlib, ns)
    return _dumpUnit(hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns), match, DUMP_ONE, mode)

def setUnitTag(unitId, tag:str = ''):
    if unitId == ROOT_ID: raise AssertionError()
    s = MU.normalTag(tag)
    hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns).set('tag', s)
    return s

def idByTag(tag):
    return hwConfig.find('.//npp:Unit[@tag="%s"]' % MU.normalTag(tag), ns).get('id')

class AddError(Exception):
    pass

def addUnit(libId, unitId, addr):
    if not canConnectUnit(libId, unitId, addr):
        raise AddError('Library unit incompatible to slot')
    lib = HWL.hwLibrary.find('./npp:Unit[@id="%s"]' % libId, ns)
    unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns)
    #Create unit and NOT copy all the data from lib
    newunit = ET.SubElement(unit,nsURI+'Unit', nsmap=nsMap )
    newunit.attrib.update({'id' : str(uid()),
                           'lib' : libId,
                           'addr' : addr,
                           'tag' : ''})
    return getUnit(newunit.get('id'), None)

def delUnit(unitId):
    if unitId == ROOT_ID: raise AssertionError()
    unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns)
    if unit is None: raise AssertionError()
    #Reconnect chain
    #find chained subunits
    chslot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@chain="1"]' % unit.get('lib'), ns)
    chained = None if chslot is None else unit.find('./npp:Unit[@addr="%s"]' % chslot.get('addr'), ns)
    parent = unit.getparent()
    if chained is not None:
        connector = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' % chained.get('lib'), ns)
        slot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@chain="1"]' % parent.get('lib'), ns)
        if _isConnectable(connector, slot):
            parent.append(chained)
            chained.attrib.update({'addr' : unit.get('addr')})
    parent.remove(unit)
    return unitId

# addressing

def getUnitAddr(unitId):
    addr = ''
    counter = 0 # chain counter
    unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns)
    slot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@addr="%s"]' %
                              (unit.getparent().get('lib'), unit.get('addr')), ns)
    while slot.get('type') != 'ROOT':
        if slot.get('chain'):
            counter += 1
            chainaddr = slot.get('addr')
        else:
            addr ='%s%s/%s' % (slot.get('addr'),
                               '' if not counter else '@' + str(counter),
                               addr)
            counter = 0
        unit = unit.getparent()
        slot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@addr="%s"]' %
                                  (unit.getparent().get('lib'), unit.get('addr')), ns)
    else:
        if counter: addr ='%s%s/%s' % (chainaddr,'@' + str(counter),addr)
    return addr[:-1]

def _termtodict(term):
    sub = term.split('@') if '@' in term else [term, 'None']
    if sub[0]=='':
        sub[0]='None'
    return dict(zip(('addr','chain'), sub))
    
def splitAddr(addr):
    return [_termtodict(term) for term in addr.split('/')]

def unitByAddr(addr):
    unit = hwConfig.find('./npp:Unit/npp:Unit', ns)
    if unit is None:
        return {}
    if len(addr):
        for term in addr.split('/'):
            if '@' in term:
                subterm = term.split('@')
                counter = int(subterm[1])
                while counter:
                    counter -= 1
                    unit = unit.find('./npp:Unit[@addr="%s"]' % subterm[0], ns)
            else: unit = unit.find('./npp:Unit[@addr="%s"]' % term, ns)
    return {} if unit is None else getUnit(unit.get('id'), None)         
                             

# advanced operations (cut copy paste move)

# main - tester
        
def main():
    libpath = os.path.dirname(os.path.abspath(__file__))
    HWL.loadLib(libpath)
    newConfig()
    loadConfig(libpath,'configtest.xml')
    for unit in hwConfig.findall('.//npp:Unit', ns):
        print ('-----------')
        print (unit.get('id') + ' ' + unit.get('addr'))
        try:
            addr = getUnitAddr(unit.get('id'))
            print (addr)
            ru = unitByAddr(addr)
            print (ru['unit'])
        except AttributeError as e:
            print (str(e))


    

if __name__ == "__main__": 
    main()  
