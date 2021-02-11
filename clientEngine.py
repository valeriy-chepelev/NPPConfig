import requests as RQ

BASE_URL = 'http://127.0.0.1:5000/'

def _url(url):
    return BASE_URL+url

def getTerm(term):
    payload = {'term' : term}
    r = RQ.get(_url('hwlib/terms'), data=payload)
    if r.status_code == 200: return r.json()
    return term

def getLibUnits(lib='', unit=''):
    payload = dict()
    if lib != '':
        payload.update({'id' : lib})
    if unit != '':
        if '|' in unit:
            spl_unit = unit.split('|')
            unitId = spl_unit[0]
            addr = spl_unit[1]
        if '@' in unit:
            spl_unit = unit.split('@')
            unitId = spl_unit[1]
            addr = spl_unit[2]
        payload.update({'unit' : unitId, 'addr' : addr})
        
    r = RQ.get(_url('hwlib/units'), data=payload)
    if r.status_code == 200: return r.json()
    raise AssertionError('Server error ' + str(r.status_code))


def getPrjUnits(unit='', lib='', mode='full'):
    payload = {'mode' : mode}
    if unit != '': payload.update ({'unit' : unit})
    if lib !='': payload.update ({'id' : lib})
    r = RQ.get(_url('cfg/units'), data=payload)
    if r.status_code == 200: return r.json()
    raise AssertionError('Server error ' + str(r.status_code))

def getStatus():
    r = RQ.get(_url('cfg/stat'))
    if r.status_code == 200: return r.json()
    raise AssertionError('Server error ' + str(r.status_code))
    
     
def main():
    print (getTerm('Power'))

if __name__ == '__main__':
    main()
