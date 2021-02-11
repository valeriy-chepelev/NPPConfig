import lxml.etree as ET
import os, sys
import misc_utils as MU
from misc_utils import ns
      
hwLibrary = None
langStat = None
lang = 'RU'

def getLangStat():
    langs = {item.get('lang') for item in hwLibrary.iter() if 'lang' in item.attrib}
    summ = len({term.get('name') for term in hwLibrary.findall('./npp:Term', ns)}) + 2 * len(
        hwLibrary.findall('./npp:Unit', ns))
    summ = float(summ) if summ else 1.0
    return {g : str(int( 0.5 + 100.0 * float(
        len(hwLibrary.findall('./npp:Term[@lang="%s"]' % g, ns)) +
        len(hwLibrary.findall('./npp:Unit/npp:Name[@lang="%s"]' % g, ns)) +
        len(hwLibrary.findall('./npp:Unit/npp:Description[@lang="%s"]' % g, ns))) /
                             summ)) + '%'
            for g in langs}

def loadLib(path, name = 'NPP module description.xml'):
    global hwLibrary, langStat, lang
    if hwLibrary is not None:
        return
    tree = ET.parse(os.path.join(path,name))
    hwLibrary = tree.getroot()
    for unit in hwLibrary.findall('./npp:Unit', ns):
        unit.set('id', unit.get('edition')+'-'+unit.get('ver')+'-'+unit.get('rev'))
        unit.set('tag','')
    #TODO: check id's is uniq
    langStat = getLangStat()
    #TODO: select lang with max library coverage
    

# Terms

def listTerms():
    return {term.get('name') : term.text for term in
            hwLibrary.findall('./npp:Term[@lang="%s"]' % lang, ns)}

def getTerm(id):
    return hwLibrary.find('./npp:Term[@name="%s"][@lang="%s"]' % (id,lang), ns).text

# Units

def _recodeReq(rec):
    return { key: int(rec[key]) if rec[key].isdigit() else rec[key]
             for key in rec}

def _dumpUnit(unit, matching_slot = None):
    return {'id': unit.get('id'),
            'type': unit.get('type'),
            'edition': unit.get('edition'),
            'ver': unit.get('ver'),
            'rev': unit.get('rev'),
            'name': MU.safeName(unit, lang),
            'desc': MU.safeDesc(unit, lang),
            'prop': [prop.get('name') for prop in
                     unit.findall('./npp:Property', ns)],
            'req': [_recodeReq(dict(req.items())) for req in
                    unit.findall('./npp:Required', ns)],
            #TODO: 'status'
            'tag': unit.get('tag'),
            'match': matching_slot is not None and MU.is_compatible(conn = unit.find('./npp:Connect', ns),
                                                                    slot = matching_slot) }
    
 
def getUnit(id, matching_slot = None):
    return _dumpUnit(hwLibrary.find('./npp:Unit[@id="%s"]' % id, ns), matching_slot)

def idByTag(tag):
    return hwLibrary.find('./npp:Unit[@tag="%s"]' % MU.normalTag(tag), ns).get('id')
    
def setUnitTag(id, tag:str = ''):
    s = MU.normalTag(tag)
    hwLibrary.find('.//npp:Unit[@id="%s"]' % id, ns).set('tag', s)
    return s
                
def listUnits(matching_slot = None):
    return [_dumpUnit(unit, matching_slot) for unit in hwLibrary.findall('./npp:Unit', ns)]

def setLang(newlang):
    global lang
    if newlang in langStat: lang = newlang
    return lang
    

# main - tester
        
def main():
    app_path = os.path.dirname(os.path.abspath(__file__))
    loadLib(app_path)
    print(langStat)

if __name__ == "__main__": 
    main()     
