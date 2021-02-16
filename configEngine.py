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

def get_slot(unitId, addr):
    unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns)
    return HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@addr="%s"]' %
                              (unit.get('lib'), addr) , ns)

def canConnectUnit(libId, unitId, addr):
    # check is library unit can be connected to a selected slot
    connector = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' % libId, ns)
    unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unitId, ns)
    slot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@addr="%s"]' %
                              (unit.get('lib'), addr) , ns)
    connected = unit.find('./npp:Unit[@addr="%s"]' % addr, ns)
    return connected is None and MU.is_compatible(conn = connector, slot = slot)

def move_unit(unit_id, dir_up = False, dry_run = False):
    '''Check and moves unit up in structure.
    arguments:
    unit_id - moved unit uuid
    dir_up = True for move up, otherwise move down
    dry_run = True to only check-up without actual move
    Returns True on success, False - if move is not possible
    '''

    def _parse_slots(slot_list, owner, chain = False):
        nonlocal my_unit, my_connector, my_slot, dir_up, dry_run
        for slot in slot_list:
            replacer = owner.find('./npp:Unit[@addr="%s"]' % slot.get('addr'), ns)
            # check my_connector match to slot
            if MU.is_compatible(conn = my_connector, slot = slot):
                # check is slot busy                
                if replacer is None and not owner is my_unit:
                    # reinstall to new free place, return true
                    if not dry_run:
                        #TODO: undo_stack_add()
                        owner.append(my_unit)
                        my_unit.set('addr', slot.get('addr'))
                    return True
                elif replacer is not None and not replacer is my_unit:
                    # get rep_connector
                    rep_connector = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' %
                                                       replacer.get('lib'), ns)
                    # check rep match to my_slot
                    if MU.is_compatible(conn = rep_connector, slot = my_slot):
                        # swap units, return true
                        if not dry_run:
                            #TODO: undo_stack_add()
                            my_unit.getparent().append(replacer)
                            replacer.set('addr', my_slot.get('addr'))
                            owner.append(my_unit)
                            my_unit.set('addr', slot.get('addr'))
                        return True
            elif not chain and replacer is not None:
                #recursevly check inner units according to direction
                inner_slot_list = HWL.hwLibrary.findall('./npp:Unit[@id="%s"]/npp:Slot' %
                                                        replacer.get('lib'), ns)
                if dir_up: inner_slot_list.reverse()
                if _parse_slots(inner_slot_list, replacer): return True
        return False

    
    # take my.connector and my.parent_slot
    my_unit = hwConfig.find('.//npp:Unit[@id="%s"]' % unit_id, ns)
    my_connector = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Connect' %
                                      my_unit.get('lib'), ns)
    my_slot = HWL.hwLibrary.find('./npp:Unit[@id="%s"]/npp:Slot[@addr="%s"]' %
                              (my_unit.getparent().get('lib'), my_unit.get('addr')) , ns)
    # look for replacers
    # first - look in childs/parents for case of chain connection
    if my_slot.get('chain'):
        if dir_up:
            target_parent = my_unit.getparent()
            child = my_unit
            while target_parent.get('id') != ROOT_ID:
                slot_list = HWL.hwLibrary.findall('./npp:Unit[@id="%s"]/npp:Slot[@chain="1"]' %
                                                  target_parent.get('lib'), ns)
                if _parse_slots(slot_list, target_parent, chain = True): return True
                child = target_parent
                target_parent = child.getparent()
        else:
            slot_list = HWL.hwLibrary.findall('./npp:Unit[@id="%s"]/npp:Slot[@chain="1"]' %
                                          my_unit.get('lib'), ns)
            if _parse_slots(slot_list, my_unit, chain = True): return True
        return False

    # second - look in parental structures
    target_parent = my_unit.getparent()
    child = my_unit
    while target_parent.get('id') != ROOT_ID:
        slot_list = HWL.hwLibrary.findall('./npp:Unit[@id="%s"]/npp:Slot' %
                                          target_parent.get('lib'), ns)
        child_pos = next(i for i, slot in enumerate(slot_list)
                         if slot.get('addr') == child.get('addr'))
        slot_list = slot_list[: child_pos] if dir_up else slot_list[child_pos+1 :]
        if dir_up: slot_list.reverse()
        if _parse_slots(slot_list, target_parent): return True
        child = target_parent
        target_parent = child.getparent()
    return False

    

# working with units

DUMP_FULL = True
DUMP_SHORT = False
DUMP_ONE = False
DUMP_ALL = True

def _dumpSlots(unit, match, recurse, mode):
    
    def subdata(unit, match, slot, recurse, mode):
        subunit = unit.find('./npp:Unit[@addr="%s"]' % slot.get('addr'), ns)
        if subunit is None: return None
        return _dumpUnit(subunit, match, recurse, mode) if recurse else subunit.get('id')
        
    return [ {'addr' : slot.get('addr'),
              'type' : slot.get('type'),
              'match' : match is not None and MU.is_compatible(conn = match, slot = slot),
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
        if MU.is_compatible(conn = connector, slot = slot):
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
    print('base')
    assert not move_unit(unit_id = 'ac27fc8b-9186-49aa-a390-0bc9c3df7999', dry_run = True, dir_up = True)
    assert not move_unit(unit_id = 'ac27fc8b-9186-49aa-a390-0bc9c3df7999', dry_run = True, dir_up = False)
    print('first x')
    assert not move_unit(unit_id = '89c61247-bf9f-46c7-9d77-ad09d3590614', dry_run = True, dir_up = True)
    assert     move_unit(unit_id = '89c61247-bf9f-46c7-9d77-ad09d3590614', dry_run = True, dir_up = False)
    print('second x up')
    assert     move_unit(unit_id = '1fe57d04-2a84-4cda-80a5-3f581bc6bcf2', dry_run = True, dir_up = True)
    print('second x down')
    assert not move_unit(unit_id = '1fe57d04-2a84-4cda-80a5-3f581bc6bcf2', dry_run = True, dir_up = False)
    print('----------------------------------')
    print('mpc')
    assert     move_unit(unit_id = 'f0e70876-9c29-4ac0-9fa9-09bd808183e2', dry_run = True, dir_up = True)
    assert not move_unit(unit_id = 'f0e70876-9c29-4ac0-9fa9-09bd808183e2', dry_run = True, dir_up = False)
    print('dis 55bdc1a9')
    assert  move_unit(unit_id = '55bdc1a9-e880-497f-8128-0ce8d443ca9b',dry_run = True, dir_up = True)
    assert  move_unit(unit_id = '55bdc1a9-e880-497f-8128-0ce8d443ca9b',dry_run = True, dir_up = False)
    print('dis 0b4087ce')
    assert  move_unit(unit_id = '0b4087ce-318a-4bd8-ae91-49c47d33214e',dry_run = True, dir_up = True)
    assert  move_unit(unit_id = '0b4087ce-318a-4bd8-ae91-49c47d33214e',dry_run = True, dir_up = False)
    print('dis 02f89c37')
    assert  move_unit(unit_id = '02f89c37-15a5-4d8a-8f27-62be45ae49a9',dry_run = True, dir_up = True)
    assert  move_unit(unit_id = '02f89c37-15a5-4d8a-8f27-62be45ae49a9',dry_run = True, dir_up = False)
    print('dis 24e779e4')
    assert  move_unit(unit_id = '24e779e4-6c5d-4b5d-be85-f5c3bd5fd39b',dry_run = True, dir_up = True)
    assert not move_unit(unit_id = '24e779e4-6c5d-4b5d-be85-f5c3bd5fd39b',dry_run = True, dir_up = False)



    

if __name__ == "__main__": 
    main()  
