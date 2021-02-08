
ns = {'61850': 'http://www.iec.ch/61850/2003/SCL',
      'NSD': 'http://www.iec.ch/61850/2016/NSD',
      'efsk': 'http://www.fsk-ees.ru/61850/2020',
      'npp': 'http://www.mtrele.ru/npp/2021'}

nsURI = '{%s}' % (ns['npp'])
nsMap = {None : ns['npp']}

def indentXML(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indentXML(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def normalTag(tag):
    return ''.join(e for e in tag if e.isalnum())

def safeName(unit, lang):
    name = unit.find('./npp:Name[@lang="%s"]' % lang, ns)
    return '' if name is None else name.text

def safeDesc(unit, lang):
    desc = unit.find('./npp:Description[@lang="%s"]' % lang, ns)
    return '' if desc is None else ('\n'.join(line.strip() for line in desc.text.splitlines())).strip()
