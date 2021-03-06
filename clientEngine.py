import requests as RQ

BASE_URL = 'http://127.0.0.1:5000/'

def _url(url):
    return BASE_URL+url

def getTerm(term):
    payload = {'term' : term}
    r = RQ.get(_url('hwlib/terms'), data=payload)
    if r.status_code == 200: return r.json()
    return term

def getLibUnits(lib='', parent='', addr=''):
    payload = dict()
    if lib != '':
        payload.update({'id' : lib})
    if parent != '':
        payload.update({'unit' : parent, 'addr' : addr})
        
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

def get_can_move_up(unit):
    payload = {'unit' : unit,
               'cmd' : 'up'}
    r = RQ.get(_url('cfg/units'), data=payload)
    if r.status_code == 200: return r.json()
    raise AssertionError('Server error ' + str(r.status_code))

def get_can_move_down(unit):
    payload = {'unit' : unit,
               'cmd' : 'down'}
    r = RQ.get(_url('cfg/units'), data=payload)
    if r.status_code == 200: return r.json()
    raise AssertionError('Server error ' + str(r.status_code))

def del_unit(unit):
    payload = {'unit' : unit}
    r = RQ.delete(_url('cfg/units'), data=payload)
    if r.status_code != 204:
        raise AssertionError('Server error ' + str(r.status_code))

def move_up_unit(unit):
    payload = {'unit' : unit,
               'cmd' : 'up'}
    r = RQ.put(_url('cfg/units'), data=payload)
    if r.status_code != 201:
        raise AssertionError('Server error ' + str(r.status_code))

def move_dn_unit(unit):
    payload = {'unit' : unit,
               'cmd' : 'down'}
    r = RQ.put(_url('cfg/units'), data=payload)
    if r.status_code != 201:
        raise AssertionError('Server error ' + str(r.status_code))

def ins_new_unit(parent, addr, lib):
    payload = {'unit' : parent,
               'addr' : addr,
               'id' : lib}
    r = RQ.post(_url('cfg/units'), data=payload)
    if r.status_code != 201:
        raise AssertionError('Server error ' + str(r.status_code))
    return r.json()

def set_unit_alias(unit, alias):
    payload = {'unit' : unit,
               'alias' : alias}
    r = RQ.put(_url('cfg/units'), data=payload)
    if r.status_code != 201:
        raise AssertionError('Server error ' + str(r.status_code))
    

    
def main():
    print (getTerm('Power'))

if __name__ == '__main__':
    main()
