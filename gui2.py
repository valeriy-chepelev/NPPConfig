from tkinter import *
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
#from PIL import Image
import clientEngine as ce
from textEngine import get_sys_text, get_lib_text, HTMLScrolledText
import resources
from string import punctuation

def fixed_map(option):
    # Fix for setting text colour for Tkinter 8.6.9
    # From: https://core.tcl.tk/tk/info/509cafafae
    #
    # Returns the style map for 'option' with any styles starting with
    # ('!disabled', '!selected', ...) filtered out.

    # style.map() returns an empty list for missing options, so this
    # should be future-safe.
    return [elm for elm in style.map('Treeview', query_opt=option) if
        elm[:2] != ('!disabled', '!selected')]
style = ttk.Style()
style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))
# fix end

class ScrolledTree(ttk.Treeview):
    def __init__(self, master=None, **kw):
        self.frame = Frame(master)

        self.vbar = Scrollbar(self.frame, orient=VERTICAL)
        kw.update({'yscrollcommand': self.vbar.set})
        self.vbar.pack(side=RIGHT, fill=Y)
        self.vbar['command'] = self.yview        

        self.hbar = Scrollbar(self.frame, orient=HORIZONTAL)
        kw.update({'xscrollcommand': self.hbar.set})
        self.hbar.pack(side=BOTTOM, fill=X)
        self.hbar['command'] = self.xview
        
        ttk.Treeview.__init__(self, self.frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=True)
        
        tree_meths = vars(ttk.Treeview).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(tree_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(sticky=N+S+E+W)
        self.create_widgets()

    def create_widgets(self):
        top=self.winfo_toplevel()
        top.rowconfigure(0, minsize=400, weight=1)
        top.columnconfigure(0, minsize=600, weight=1)

        self.ico_lib = PhotoImage(data=resources.ICO_LIB)
        self.ico_lib_ins = PhotoImage(data=resources.ICO_LIB_INS)
        self.ico_mod = PhotoImage(data=resources.ICO_MOD)
        self.ico_mod_ins = PhotoImage(data=resources.ICO_MOD_INS)
        self.ico_mod_no = PhotoImage(data=resources.ICO_MOD_NO)
        self.ico_mod_no_ins = PhotoImage(data=resources.ICO_MOD_NO_INS)
        self.ico_red_bulb = PhotoImage(data=resources.ICO_RED)
        self.ico_green_bulb = PhotoImage(data=resources.ICO_GREEN)
        

        self.main_pane = PanedWindow(master = self,
                                     bd=2,
                                     orient=HORIZONTAL,
                                     sashrelief = 'groove')
        
        self.lib_pane = PanedWindow(master = self.main_pane,
                                    bd=2,
                                    orient=VERTICAL,
                                    sashrelief = 'groove')

        self.modules_tree = ScrolledTree(master=self.main_pane,
                                         show='tree headings',
                                         selectmode='browse')
        self.modules_tree["columns"]=("ed")
        self.modules_tree.column("#0", width=150, minwidth=150)
        self.modules_tree.column("ed", width=70, minwidth=70, stretch=NO)
        self.modules_tree.heading("#0",text="Модуль",anchor=W)
        self.modules_tree.heading("ed", text="Тип",anchor=W)
        self.modules_tree.bind("<<TreeviewSelect>>", self.on_module_select)
        self.modules_tree.tag_configure('DEF', image=self.ico_mod)
        self.modules_tree.tag_configure('EMPTY', image=self.ico_mod_no)
        self.modules_tree.tag_configure('DMATCH', image=self.ico_mod_ins)
        self.modules_tree.tag_configure('EMATCH', image=self.ico_mod_no_ins)
        
        self.lib_tree = ScrolledTree(master=self.lib_pane,
                                     show='tree headings',
                                     selectmode='browse')
        self.lib_tree["columns"]=('type')
        self.lib_tree.column("#0", width=100, minwidth=100)
        self.lib_tree.column("type", width=70, minwidth=70, stretch=NO)
        self.lib_tree.heading("#0",text="Модуль",anchor=W)
        self.lib_tree.heading("type", text="Тип",anchor=W)
        self.lib_tree.bind("<<TreeviewSelect>>", self.on_lib_select)
        self.lib_tree.tag_configure('DEF', image=self.ico_lib)
        self.lib_tree.tag_configure('MATCH', image=self.ico_lib_ins)
         
        self.main_html = HTMLScrolledText(master = self.main_pane,
                                          relief='flat', bd = 2,
                                          padx=10, pady=2,
                                          state=DISABLED,
                                          html = get_sys_text(None, None, None, None))
        self.main_html.bind('<<get_order>>', self.on_get_order)
        self.main_html.bind('<<req_info>>', self.on_req_info)
        self.main_html.bind('<<del_unit>>', self.on_del_unit)
        self.main_html.bind('<<reset_unit>>', self.on_reset_unit)
        self.main_html.bind('<<move_up_unit>>', self.on_move_up_unit)
        self.main_html.bind('<<move_dn_unit>>', self.on_move_dn_unit)
        self.main_html.bind('<<ins_unit>>', self.on_ins_unit)
        self.main_html.bind('<<alias>>', self.on_alias)

        self.lib_html = HTMLScrolledText(master = self.lib_pane,
                                         relief='flat', bd = 2,
                                         padx=10, pady=2,
                                         state=DISABLED,
                                         html = get_lib_text(None))
        
        self.top_frame = Frame(master=self,
                               relief='groove', bd = 2,
                               padx=2, pady=2)
        self.stat_label = Button(master = self.top_frame,
                                 image = self.ico_red_bulb,
                                 relief = 'flat',
                                 takefocus = 0,
                                 command = self.on_req_info)
        self.stat_label.pack(side = LEFT)
                                 

        self.main_pane.add(self.modules_tree, minsize=200, width=200)
        self.main_pane.add(self.main_html, minsize=200)
        self.main_pane.add(self.lib_pane, minsize=200, width=200)
        self.lib_pane.add(self.lib_tree, minsize=200)
        self.lib_pane.add(self.lib_html, minsize=100, height=200)

        self.top_frame.grid(column=0, row=0, sticky='nesw')
        self.main_pane.grid(column=0, row=1, sticky='nesw')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, minsize=30, weight=0)
        self.rowconfigure(1, weight=1)

        self.fill_lib_tree(data = ce.getLibUnits())
        self.fill_modules_tree(data = ce.getPrjUnits())
        self.update_stat()
        
        
    def on_get_order(self, * args):
        print('This is order')

    def on_req_info(self, * args):
        print('This is stats info')

    def on_del_unit(self, * args):
        iid = self.modules_tree.focus()
        assert iid != ''
        (parent, addr) = (next( tag for tag in self.modules_tree.item(iid, 'tags')
                                if '@' in tag)).split('@')
        ce.del_unit(self.modules_tree.focus())
        self.update_modules(new_focus = parent + '|' + addr)

    def on_reset_unit(self, * args):
        ce.set_unit_alias(self.modules_tree.focus(), '')
        self.update_modules()

    def on_alias(self, * args):
        iid = self.modules_tree.focus()
        assert iid != ''
        name = self.modules_tree.item(iid,'text')
        if ': ' in name:
            name = name.split(': ')[-1]
        value = self.main_html.entry_text
        new_alias = (''.join(e for e in value if not e in punctuation)).strip()
        if new_alias != name:
            ce.set_unit_alias(iid, new_alias)
            self.update_modules()
            

    def on_move_up_unit(self, * args):
        ce.move_up_unit(self.modules_tree.focus())
        self.update_modules()

    def on_move_dn_unit(self, * args):
        ce.move_dn_unit(self.modules_tree.focus())
        self.update_modules()

    def on_ins_unit(self, * args):
        iid = self.modules_tree.focus()
        lib = self.lib_tree.focus()
        assert iid != ''
        (parent, addr) = (next( tag for tag in self.modules_tree.item(iid, 'tags')
                                if '@' in tag)).split('@')
        self.update_modules(new_focus = ce.ins_new_unit(parent, addr, lib)['unit'])

    def on_module_select(self, * args):
        lib = self.lib_tree.focus()
        if lib == '': lib = None
        iid = self.modules_tree.focus()
        assert iid != ''
        unit = None if ('|' in iid) else iid
        (parent, addr) = (next( tag for tag in self.modules_tree.item(iid, 'tags')
                                if '@' in tag)).split('@')
        self.main_html.set_html(get_sys_text(unit, parent, addr, lib))
        self.update_lib_tree(data = ce.getLibUnits(parent = parent, addr = addr))
        
    def on_lib_select(self, * args):
        lib = self.lib_tree.focus()
        if lib == '': lib = None
        iid = self.modules_tree.focus()
        if iid == '':
            unit = None
            parent = None
            addr = None
        else:
            unit = None if ('|' in iid) else iid
            (parent, addr) = (next( tag for tag in self.modules_tree.item(iid, 'tags')
                                    if '@' in tag)).split('@')

        self.lib_html.set_html(get_lib_text(lib))
        self.update_modules_tree(data = ce.getPrjUnits(lib = lib, mode = 'short'))
        self.main_html.set_html(get_sys_text(unit, parent, addr, lib))
        
    def fill_lib_tree(self, data):
        for unit in data:
            if unit['type']=='ROOT': continue
            self.lib_tree.insert(parent = '',
                                 index = END,
                                 iid = unit['id'],
                                 text = unit['name'],
                                 values = (unit['id']),
                                 tags = 'MATCH' if unit['match'] else 'DEF')

    def update_lib_tree(self, data):
        for unit in data:
            if unit['type']=='ROOT': continue
            self.lib_tree.item(item = unit['id'], tags='MATCH' if unit['match'] else 'DEF')

    def update_stat(self):
        data = ce.getStatus()
        if data['Requirements'] and data['Resources']:
            self.stat_label.configure(image = self.ico_green_bulb, command = self.on_get_order)
        else:
            self.stat_label.configure(image = self.ico_red_bulb, command = self.on_req_info)

    def fill_modules_tree(self, data, parent='', prefix=''):
        if data['type']=='ROOT': pos = ''
        else: pos = self.modules_tree.insert(parent = parent,
                                             index = END,
                                             iid = data['unit'],
                                             text=prefix + (data['alias'] if data['alias'] != '' else data['name']),
                                             values=(data['lib']),
                                             tags = ('DMATCH', data['parent']) if data['match'] else ('DEF', data['parent']),
                                             open=True)
        for slot in data['slots']:
            slot_pos = '' if slot['type']=='Exp' else pos
            if slot['unit'] is not None:
                self.fill_modules_tree(parent = slot_pos,
                                       data = slot['unit']|{'match':slot['match'],
                                                            'parent':data['unit'] + '@' + slot['addr']}, #parental unit/slot for future library match for selected unit 
                                                            
                                       prefix = '' if slot['type']=='ROOT' else slot['addr']+': ')
            else:
                self.modules_tree.insert(parent = slot_pos,
                                         index = END,
                                         iid = data['unit'] + '|' + slot['addr'],
                                         text=('' if slot['type']=='ROOT' else slot['addr'] + ': ')+'---',
                                         values=(ce.getTerm(slot['type'])),
                                         tags = ('EMATCH', data['unit'] + '@' +
                                                 slot['addr']) if slot['match'] else ('EMPTY', data['unit'] + '@' + slot['addr']))

    def update_modules_tree(self, data):
        if data['type']!='ROOT':
            self.modules_tree.item(item = data['unit'],
                                   tags = ('DMATCH', data['parent']) if data['match'] else ('DEF',data['parent']))
        for slot in data['slots']:
            if slot['unit'] is not None:
                self.update_modules_tree(data = slot['unit']|{'match':slot['match'], # indicates slot match for a selected library
                                                              'parent':data['unit'] + '@' + slot['addr']}) #parental unit/slot for future library match for selected unit 
            else:
                self.modules_tree.item(item = data['unit'] + '|' + slot['addr'],
                                       tags = ('EMATCH', data['unit'] + '@' + slot['addr']) if slot['match'] else ('EMPTY', data['unit'] + '@' + slot['addr']))

    def update_modules(self, new_focus = None):
        focused  = self.modules_tree.focus()
        closed_stat = [iid for iid in self.modules_tree.get_children()
                       if not self.modules_tree.item(iid,'open')]
        
        self.modules_tree.delete(*self.modules_tree.get_children())
        self.fill_modules_tree(data = ce.getPrjUnits())
        
        for iid in closed_stat:
            if self.modules_tree.exists(iid):
                self.modules_tree.item(item=iid, open=False)
        if new_focus is not None:
            if self.modules_tree.exists(new_focus):
                focused = new_focus
            elif self.modules_tree.exists(new_focus.split('|')[0]):
                focused = new_focus.split('|')[0]
        if self.modules_tree.exists(focused):
            self.modules_tree.see(focused)
            self.modules_tree.focus(focused)
            self.modules_tree.selection_set(focused)
        self.on_lib_select()
        self.update_stat()
        
            
app = Application()
app.master.title('NPP Configurator Client')
app.master.minsize(600, 400)
app.mainloop()
