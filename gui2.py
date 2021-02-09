from tkinter import *
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
from verticalscrolledframe import VerticalScrolledFrame as VSFrame
import clientEngine as ce
from textEngine import get_sys_text, get_lib_text, HTMLScrolledText


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(sticky=N+S+E+W)
        self.createWidgets()

    def createWidgets(self):
        top=self.winfo_toplevel()
        top.rowconfigure(0, minsize=400, weight=1)
        top.columnconfigure(0, minsize=400, weight=1)

        self.mainpane = PanedWindow(master = self, bd=2, orient=HORIZONTAL, sashrelief = 'groove')
        self.libpane = PanedWindow(master = self.mainpane, bd=2, orient=VERTICAL, sashrelief = 'groove')

        self.sysframe = Frame(master=self.mainpane, bd = 2, relief='groove')
        self.systree = ttk.Treeview(master=self.sysframe, show='tree headings', selectmode='browse')
        self.systree["columns"]=("ed")
        self.systree.column("#0", width=150, minwidth=150)
        self.systree.column("ed", width=70, minwidth=70, stretch=NO)
        self.systree.heading("#0",text="Модуль",anchor=W)
        self.systree.heading("ed", text="Тип",anchor=W)
        
        self.sys_vsb = Scrollbar(self.sysframe, orient=VERTICAL)
        self.sys_vsb.pack(fill=Y, side=RIGHT)
        self.systree['yscrollcommand'] = self.sys_vsb.set
        self.sys_vsb['command'] = self.systree.yview
        self.sys_hsb = Scrollbar(self.sysframe, orient=HORIZONTAL)
        self.sys_hsb.pack(fill=X, side=BOTTOM)
        self.systree['xscrollcommand'] = self.sys_hsb.set
        self.sys_hsb['command'] = self.systree.xview
        self.systree.pack(fill=BOTH, expand=True)
        self.systree.bind("<<TreeviewSelect>>", self.on_sys_select)

        self.libframe = Frame(master=self.libpane, bd = 2, relief='groove')
        self.libtree = ttk.Treeview(master=self.libframe, show='tree headings', selectmode='browse')
        self.libtree["columns"]=('kind', 'type')
        self.libtree.column("#0", width=150, minwidth=150)
        self.libtree.column("kind", width=100, minwidth=70, stretch=NO)
        self.libtree.column("type", width=70, minwidth=70, stretch=NO)
        self.libtree.heading("#0",text="Модуль",anchor=W)
        self.libtree.heading("kind", text="Вид",anchor=W)
        self.libtree.heading("type", text="Тип",anchor=W)
        
        self.lib_vsb = Scrollbar(self.libframe, orient=VERTICAL)
        self.lib_vsb.pack(fill=Y, side=RIGHT)
        self.libtree['yscrollcommand'] = self.lib_vsb.set
        self.lib_vsb['command'] = self.libtree.yview
        self.lib_hsb = Scrollbar(self.libframe, orient=HORIZONTAL)
        self.lib_hsb.pack(fill=X, side=BOTTOM)
        self.libtree['xscrollcommand'] = self.lib_hsb.set
        self.lib_hsb['command'] = self.libtree.xview
        self.libtree.pack(fill=BOTH, expand=True)
        self.libtree.bind("<<TreeviewSelect>>", self.on_lib_select)
        

        self.infframe = Frame(master=self.mainpane, bd = 2, relief='flat')
        self.htmlmain = HTMLScrolledText(master = self.infframe, padx=10, pady=2, state=DISABLED,
                                         html = get_sys_text(None, None),
                                         relief='flat', bd = 2)
        self.htmlmain.pack(fill=BOTH, expand=True)

        self.libinfframe = Frame(master=self.libpane, bd = 2, relief='flat')
        self.htmllib = HTMLScrolledText(master = self.libinfframe, padx=10, pady=2, state=DISABLED,
                                         html = get_lib_text(None),
                                         relief='flat', bd = 2)
        self.htmllib.pack(fill=BOTH, expand=True)
        
        self.statframe = Frame(master=self, padx=2, pady=2, bd = 2, relief='groove')

        self.mainpane.add(self.sysframe, minsize=200)
        self.mainpane.add(self.infframe, minsize=200, width=400)
        self.mainpane.add(self.libpane, minsize=200, width=200)
        self.libpane.add(self.libframe, minsize=200)
        self.libpane.add(self.libinfframe, minsize=100, height=200)

        self.statframe.grid(column=0, row=0, sticky='nesw')
        self.mainpane.grid(column=0, row=1, sticky='nesw')
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, minsize=30, weight=0)
        self.rowconfigure(1, weight=1)

        self.makeLibTree()
        self.makeTree()
        self.makeStat()

    def on_sys_select(self, * args):
        lib = self.libtree.focus()
        if lib == '': lib = None
        unit = self.systree.focus()
        if unit == '': unit = None
        self.htmlmain.set_html(get_sys_text(unit, lib))
        
    def on_lib_select(self, * args):
        lib = self.libtree.focus()
        if lib == '': lib = None
        unit = self.systree.focus()
        if unit == '': unit = None
        self.htmlmain.set_html(get_sys_text(unit, lib))
        self.htmllib.set_html(get_lib_text(lib))

    def makeLibTree(self):
        for unit in ce.getLibUnits():
            if unit['type']=='ROOT': continue
            self.libtree.insert(parent = '',
                                index = END,
                                iid = unit['id'],
                                text = unit['name'],
                                values = (ce.getTerm(unit['type']),unit['id']))

    def makeStat(self):
        data = ce.getStatus()
        Label(master = self.statframe, justify = LEFT, text='Зависимости:').pack(side = LEFT)
        Label(master = self.statframe, justify = LEFT,
              fg = 'green' if data['Requirements'] else 'red',
              text = '\u2714' if data['Requirements'] else '\u2716').pack(side = LEFT)
        Label(master = self.statframe, justify = LEFT, text='Ресурсы:').pack(side = LEFT)
        Label(master = self.statframe, justify = LEFT,
              fg = 'green' if data['Resources'] else 'red',
              text = '\u2714' if data['Resources'] else '\u2716').pack(side = LEFT)

    def makeTree(self):

        def _addunit(parent, data, prefix=''):
            pos = '' if data['type']=='ROOT' else self.systree.insert(parent = parent,
                                                                      index = END,
                                                                      iid = data['unit'],
                                                                      text=prefix + ce.getTerm(data['type']),
                                                                      values=(data['lib']),
                                                                      open='True')
            for slot in data['slots']:
                slotpos = '' if slot['type']=='Exp' else pos
                if slot['unit'] is not None:
                    _addunit(slotpos, slot['unit'],'' if slot['type']=='ROOT' else slot['addr']+': ')
                else:
                    self.systree.insert(parent = slotpos,
                                        index = END,
                                        iid = data['unit'] + '|' + slot['addr'],
                                        text=('' if slot['type']=='ROOT' else slot['addr'])+': ---',
                                        values=(ce.getTerm(slot['type'])))
            
        data = ce.getPrjUnits()
        _addunit('', data)
            
app = Application()
app.master.title('NPP Configurator Client')
app.master.minsize(400, 400)
app.mainloop()
