import lxml.etree as ET
import os, sys
import misc_utils as MU
from misc_utils import ns
import npp_repository as repo

nsURI = '{%s}' % (ns['61850'])
nsMap = {None : ns['61850']}

def add_IED(parent, * args):
    ''' Creates new empty IED under the parent
    according to the arguments
    '''
    pass

def add_LD(ied, inst, desc='', lnn_type='', gr_ref=None, template=None):
    ''' Find or creates new LD under the parent.
    For new LD creates LN0 according to the args and
    creates LNs according to the args.
    Changes desc value
    Returns LD tree element    
    arguments:
    - parent is tree element (Server!!!!!!!!!!!!!!!!!!), mandatory
    - inst is string, mandatory
    - desc is string, default empty
    - lnn_type is string of LLN0 lnType
    - template is id of LD library template
    '''
    server = ied.find('.//61850:Server', ns)
    ld = server.find('./61850:LDevice[@inst="%s"]' % inst, ns)
    if ld is None:
        ld = ET.SubElement(server, nsURI+'LDevice', nsmap = nsMap)
        ld.set('inst', inst)
        if repo.have('LN', lnn_type):
            add_LN(ld, lnn_type, is_LLN0 = True, ref_LLN0 = gr_ref)
        if repo.have('LD', template):
            pass #TODO: LD template insert
    if desc != '': ld.set('desc', desc)
    return ld
    
    
    

def add_LN(ldevice, ln_type, ref_LLN0 = None):
    ''' Creates new LN under the parent
    according to the ln_type
    arguments:
    parent is LD tree element
    ln_type is string id of lnType in templates
    '''
    def _scan_da(parent, template):
        is_struct = template.get('bType') == 'Struct'
        dai = ET.SubElement(parent, nsURI+('SDI' if is_struct else 'DAI'),
                            nsmap = nsMap)
        dai.set('name', template.get('name'))
        if is_struct:
            for bda in repo.get('DA', template.get('type')):
                _scan_da(dai, bda)
        else:
            ET.SubElement(dai, nsURI+'VAL', nsmap = nsMap).text = 'value'
    
    def _scan_do_sdo(parent, template):
        ret_flag = False
        for item in template:
            if 'SDO' in item.tag:
                sdi = ET.SubElement(parent, nsURI+'SDI', nsmap = nsMap)
                sdi.set('name', item.get('name'))
                sdo_template = repo.get('DO', item.get('type'))
                if _scan_do_sdo(sdi, sdo_template): ret_flag = True
                else: parent.remove(sdi)
            elif item.get('fc') in ('CF', 'SE', 'SG', 'SP'):
                _scan_da(parent, item)
                ret_flag = True
        return ret_flag
        
    #take template
    ln_template = repo.get('LN',ln_type)
    #find first free instance
    instances = {(item.get('inst')) for item in
                 ldevice.findall('./61850:LN[@prefix="%s"][@lnClass="%s"]' %
                                 (ln_template.get('{%(emt)s}prefix' % ns),
                                  ln_template.get('lnClass')), ns)}
    inst = str(next((i for i in range(1,len(instances)+2)
                     if not str(i) in instances)))
    #LLN0 special flag
    lln0 = ln_template.get('lnClass') == 'LLN0'
    #create node and fill main attributes
    lnode = ET.SubElement(ldevice, nsURI+('LN0' if lln0 else 'LN'),
                       nsmap = nsMap)
    lnode.set('lnType', ln_type)
    if not lln0: lnode.set('prefix', ln_template.get('{%(emt)s}prefix' % ns))
    lnode.set('lnClass', ln_template.get('lnClass'))
    lnode.set('inst', '' if lln0 else inst)
    lnode.set('desc', ln_template.get('desc'))
    
    #TODO:create Private zone with additional data
    private = ET.SubElement(lnode, nsURI+'Private', nsmap = nsMap)
    private.set('type', 'mtNppNodeCfg')
        
    #TODO:scan template to instantiate in node DAI values FC=CF, SP, SG, SE
    for data_object in ln_template:
        doi = ET.SubElement(lnode,nsURI+'DOI', nsmap = nsMap)
        doi.set('name', data_object.get('name'))
        do_template = repo.get('DO', data_object.get('type'))
        if not _scan_do_sdo(parent = doi, template = do_template):
            lnode.remove(doi)
            
    #TODO:instantiate LLN0 GrRef
    if lln0 and ref_LLN0 is not None:
        val = lnode.find('./61850:DOI[@name="GrRef"]/61850:DAI[@name="setSrcRef"]/61850:VAL', ns)
        if val is not None: val.text = ref_LLN0

def get_path(item, break_LD = False):
    ''' returns SCL path to item
    item is XML element - any kind of instantiated SCL element
    '''
    path = ''
    while item is not None:
        print(item.tag)
        if item.tag in [nsURI+'DAI', nsURI+'DOI', nsURI+'SDI']:
            path = item.get('name') + '.' + path
        elif item.tag in [nsURI+'LN', nsURI+'LN0']:
            path = (item.get('prefix') if item.get('prefix') else '')\
                   + item.get('lnClass')+item.get('inst') + '.' + path
        elif item.tag == nsURI+'LDevice':
            path = item.get('inst') + '/' + path
            if break_LD: break
        elif item.tag == nsURI+'IED':
            path = item.get('name') + path
            break
        item = item.getparent()
    return path[:-1] if path[-1] in './' else path


def main():
    root = ET.Element(nsURI+'root', nsmap = nsMap)
    add_LN(root,'in4')
    add_LN(root,'out4')
    add_LN(root,'out4')
    add_LN(root,'out4')
    tree = ET.ElementTree(root)
    MU.indentXML(root)
    path = os.path.dirname(os.path.abspath(__file__))
    tree.write(os.path.join(path, 'ln_tst.xml'), encoding="utf-8", xml_declaration=True) 
    
    

if __name__ == "__main__": 
    main()  

