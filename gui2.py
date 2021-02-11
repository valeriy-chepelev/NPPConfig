from tkinter import *
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
from verticalscrolledframe import VerticalScrolledFrame as VSFrame
import clientEngine as ce
from textEngine import get_sys_text, get_lib_text, HTMLScrolledText

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
        self.modules_tree.tag_configure('MATCH', background='cyan')
        
        self.lib_tree = ScrolledTree(master=self.lib_pane,
                                     show='tree headings',
                                     selectmode='browse')
        self.lib_tree["columns"]=('kind', 'type')
        self.lib_tree.column("#0", width=150, minwidth=150)
        self.lib_tree.column("kind", width=100, minwidth=70, stretch=NO)
        self.lib_tree.column("type", width=70, minwidth=70, stretch=NO)
        self.lib_tree.heading("#0",text="Модуль",anchor=W)
        self.lib_tree.heading("kind", text="Вид",anchor=W)
        self.lib_tree.heading("type", text="Тип",anchor=W)
        self.lib_tree.bind("<<TreeviewSelect>>", self.on_lib_select)
        self.lib_tree.tag_configure('MATCH', background='cyan')
         
        self.main_html = HTMLScrolledText(master = self.main_pane,
                                          relief='flat', bd = 2,
                                          padx=10, pady=2,
                                          state=DISABLED,
                                          html = get_sys_text(None, None))

        self.lib_html = HTMLScrolledText(master = self.lib_pane,
                                         relief='flat', bd = 2,
                                         padx=10, pady=2,
                                         state=DISABLED,
                                         html = get_lib_text(None))
        
        self.top_frame = Frame(master=self,
                               relief='groove', bd = 2,
                               padx=2, pady=2,)

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
        self.makeStat()

    def on_module_select(self, * args):
        lib = self.lib_tree.focus()
        if lib == '': lib = None
        unit = self.modules_tree.focus()
        if unit == '': unit = None
        self.main_html.set_html(get_sys_text(unit, lib))
        self.update_lib_tree(data = ce.getLibUnits(unit = unit))
        
    def on_lib_select(self, * args):
        lib = self.lib_tree.focus()
        if lib == '': lib = None
        unit = self.modules_tree.focus()
        if unit == '': unit = None
        self.main_html.set_html(get_sys_text(unit, lib))
        self.lib_html.set_html(get_lib_text(lib))
        self.update_modules_tree(data = ce.getPrjUnits(lib = lib, mode = 'short'))

    def fill_lib_tree(self, data):
        for unit in data:
            if unit['type']=='ROOT': continue
            self.lib_tree.insert(parent = '',
                                 index = END,
                                 iid = unit['id'],
                                 text = unit['name'],
                                 values = (ce.getTerm(unit['type']),unit['id']),
                                 tags='MATCH' if unit['match'] else '')

    def update_lib_tree(self, data):
        for unit in data:
            if unit['type']=='ROOT': continue
            self.lib_tree.item(item = unit['id'], tags='MATCH' if unit['match'] else '')

    def makeStat(self):
        data = ce.getStatus()
        state_color = 'green' if data['Requirements'] and data['Resources'] else 'red'
        Label( master = self.top_frame,
               fg = state_color,
               text = '\u2B24').pack(side = RIGHT)

    def fill_modules_tree(self, data, parent='', prefix=''):
        if data['type']=='ROOT': pos = ''
        else: pos = self.modules_tree.insert(parent = parent,
                                             index = END,
                                             iid = data['unit'] + '@' + data['parent'],
                                             text=prefix + data['name'],
                                             values=(data['lib']),
                                             tags='MATCH' if data['match'] else '',
                                             open='True')
        for slot in data['slots']:
            slot_pos = '' if slot['type']=='Exp' else pos
            if slot['unit'] is not None:
                self.fill_modules_tree(parent = slot_pos,
                                       data = slot['unit']|{'match':slot['match'], # indicates slot match for a selected library
                                                            'parent':data['unit'] + '@' + slot['addr']}, #parental unit/slot for future library match for selected unit 
                                                            
                                       prefix = '' if slot['type']=='ROOT' else slot['addr']+': ')
            else:
                self.modules_tree.insert(parent = slot_pos,
                                         index = END,
                                         iid = data['unit'] + '|' + slot['addr'],
                                         text=('' if slot['type']=='ROOT' else slot['addr'] + ': ')+'---',
                                         values=(ce.getTerm(slot['type'])),
                                         tags='MATCH' if slot['match'] else '')

    def update_modules_tree(self, data):
        if data['type']!='ROOT': self.modules_tree.item(item = data['unit'] + '@' + data['parent'],
                                                        tags = 'MATCH' if data['match'] else '')
        for slot in data['slots']:
            if slot['unit'] is not None:
                self.update_modules_tree(data = slot['unit']|{'match':slot['match'], # indicates slot match for a selected library
                                                              'parent':data['unit'] + '@' + slot['addr']}) #parental unit/slot for future library match for selected unit 
            else:
                self.modules_tree.item(item = data['unit'] + '|' + slot['addr'],
                                       tags = 'MATCH' if slot['match'] else '')
            
app = Application()
app.master.title('NPP Configurator Client')
app.master.minsize(600, 400)
app.mainloop()
