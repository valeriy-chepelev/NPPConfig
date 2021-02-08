from tkinter import *
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
from verticalscrolledframe import VerticalScrolledFrame as VSFrame
import clientEngine as ce


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(sticky=N+S+E+W)
        self.createWidgets()

    def createWidgets(self):
        top=self.winfo_toplevel()
        top.rowconfigure(0, minsize=400, weight=1)
        top.columnconfigure(0, minsize=300, weight=1)

        self.pane = PanedWindow(master = self, bd=2, orient=HORIZONTAL, sashrelief = 'groove')

        self.sysframe = Frame(master=self.pane, bd = 2, relief='groove')
        self.systree = ttk.Treeview(master=self.sysframe, show='tree headings')
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

        self.libframe = Frame(master=self.pane, bd = 2, relief='groove')
        self.libtree = ttk.Treeview(master=self.libframe, show='tree headings')
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

        self.infframe = Frame(master=self.pane, bd = 2, relief='flat')
        
        self.statframe = Frame(master=self, padx=2, pady=2, bd = 2, relief='groove')

        self.pane.add(self.sysframe, minsize=200)
        self.pane.add(self.infframe, minsize=200)
        self.pane.add(self.libframe, minsize=200)

        self.pane.grid(column=0, row=0, sticky='nesw')
        self.statframe.grid(column=0, row=1, sticky='nesw')
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self.makeLibTree()
        self.makeTree()
        self.makeStat()


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
                                        text=('' if slot['type']=='ROOT' else slot['addr'])+': ---',
                                        values=(ce.getTerm(slot['type'])))
            
        data = ce.getPrjUnits()
        _addunit('', data)
            
app = Application()
app.master.title('NPP Configurator Client')
app.master.minsize(400, 300)
app.mainloop()
