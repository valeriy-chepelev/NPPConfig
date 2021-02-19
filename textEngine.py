import sys
import tkinter as tk
from tkinter import scrolledtext
from tkinter import font
import html_parser

import clientEngine as ce

T_H_HWCONF = '<h4>Сборка устройства.</h4>'
T_SEL_TIP = '''<div style="text-align: center">\u261A Выберите модуль или место подключения<br>
в конфигурации вашего устройства<br>
для просмотра полной информации о нём.</div>'''
T_SEL_LIB_TIP = '''<div>\u261D Выберите модуль в библиотке<br>
для просмотра полной информации о нём.</div>'''
T_BADCONF = '''<h6>Устройство не готово.</h6><div style="text-align: center">
Проверьте информацию о <a href="req_info">Зависимостях и Ресурсах</a>,<br>
добавьте или удалите модули и функции.</div>'''
T_GOODCONF = '''<h6>Устройство сконфигурировано.</h6><div style="text-align: center">
Вы можете <a href="get_order">Получить карту заказа</a> или продолжить настройку.</div>'''
T_INS_TIP = '''<div style="text-align: center">Чтобы добавить модуль из библиотеки в устройство,<br>
выберите модуль в библиотеке \u261B <br>
\u261A и выберите место для его установки в устройство.<br>
Совместимые позиции выделяются метками "<span style="color: green">\u25C0 \u25C0</span>".</div>'''
        

def get_sys_text(unit, parent, addr, library):
    s = T_H_HWCONF
    # if no selection - base selection tip
    if parent is None and library is None: s = s + T_SEL_TIP
    # if both selected: commands
    if parent is not None and library is not None:
        s = s + insert_text(unit, parent, addr, library)
    # if only one selected - show tip
    elif parent is not None or library is not None:
        s = s + T_INS_TIP
    # text for unit, if selected
    if parent is not None: s = s + unit_text(unit, parent, addr)
    # finalize - status info       
    stat = ce.getStatus()
    s = s + (T_GOODCONF if stat['Resources'] and stat['Requirements'] else T_BADCONF)
    return s

def get_lib_text(library):
    return T_SEL_LIB_TIP if library is None else lib_text(library)

def unit_text(unit, parent, addr):
    if unit is None:
        # ----- no unit, just a slot -------
        data = ce.getPrjUnits(parent)
        slot = next(item for item in data['slots'] if item["addr"] == addr)
        s = '<h6>Место подключения</h6><div>Может быть установлен любой совместимый (суб-)модуль.</div>'
        s = s + '<ul><li>база: %s</li>' % data['name']
        s = s + '<li>тип соединения: %s</li>' % ce.getTerm(slot['type'])
        s = s + '<li>позиция: %s</li></ul>' % addr
        return s
    data = ce.getPrjUnits(unit)
    s = '<h6>%s</h6>' % data['name']
    # ----- unit commands ---------
    s = s + '<ul><li><a href="del_unit">Удалить</a> из устройства'
    if subunits_count(data):
        s = s + '<span style="color: red"> (подключенные (суб-)модули будут также удалены)</span>'
    s = s + '</li><li><a href="reset_unit">Сбросить настройки</a></li>'
    if ce.get_can_move_up(unit):
        s = s + '<li><a href="move_up_unit">Переместить вверх</a></li>'
    if ce.get_can_move_down(unit):
        s = s + '<li><a href="move_dn_unit">Переместить вниз</a></li>'
    # ----- unit information --------
    s = '</ul>%s<div>%s</div>' % (s, data['desc'])
    s = '%s<ul><li>тип: %s</li>' % (s, ce.getTerm(data['type']))
    s = '%s<li>редакция: %s</li>' % (s, data['edition'])
    s = '%s<li>версия: %s</li>' % (s, data['ver'])
    s = '%s<li>ревизия: %s</li>' % (s, data['rev'])
    prop = ', '.join([ce.getTerm(item) for item in data['prop']])
    s = s + ('</ul>' if prop=='' else '<li>свойства: %s</li></ul>' % prop)
    return s

def lib_text(library):
    data = ce.getLibUnits(library)
    s = '<h6>%s</h6><div>%s</div>' % (data['name'], data['desc'])
    s = '%s<ul><li>тип: %s</li>' % (s, ce.getTerm(data['type']))
    s = '%s<li>редакция: %s</li>' % (s, data['edition'])
    s = '%s<li>версия: %s</li>' % (s, data['ver'])
    s = '%s<li>ревизия: %s</li>' % (s, data['rev'])
    prop = ', '.join([ce.getTerm(item) for item in data['prop']])
    s = s + ('</ul>' if prop=='' else '<li>свойства: %s</li></ul>' % prop)
    return s

def insert_text(unit, parent, addr, library):
    lib_data = ce.getLibUnits(library, parent, addr)
    s = ''
    # check installing a same item type
    is_same = False
    if unit is not None:
        unit_data = ce.getPrjUnits(unit)
        is_same = unit_data['lib'] == lib_data['id']
    # check lib compatibility to slot
    if (not is_same) and lib_data['match']:
        s = '<div><a href="ins_unit">Установить "%s"</a> ' % lib_data['name']
        s = s + 'на выбранное место.'
        if unit is not None:
            s = s + '<br><span style="color: red">Это действие удалит "%s"!</span>' % unit_data['name']
            if subunits_count(unit_data):
                s = s + '<br>Установленные (суб-)модули будут по возможности переподключены.'
        s = s + '</div>'
    return s

def subunits_count(data):
    # ATTENTION: in list comp link to the slot type !!!
    return len([ slot['addr'] for slot in data['slots']
                 if slot['type'] == 'Bus' and slot['unit'] is not None])
        

#-------------------- the followed is imported from tkhtml----------------

class _ScrolledText(tk.Text):
    #----------------------------------------------------------------------------------------------
    def __init__(self, master=None, **kw):
        self.frame = tk.Frame(master)

        self.vbar = tk.Scrollbar(self.frame)
        kw.update({'yscrollcommand': self.vbar.set})
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar['command'] = self.yview

        tk.Text.__init__(self, self.frame, **kw)
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_meths = vars(tk.Text).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)

class HTMLScrolledText(_ScrolledText):
    #----------------------------------------------------------------------------------------------
    """
    HTML scrolled text widget
    """
    def __init__(self, *args, html=None, **kwargs):
        #------------------------------------------------------------------------------------------
        super().__init__(*args, **kwargs)
        self._w_init(kwargs)
        self.html_parser = html_parser.HTMLTextParser()
        if isinstance(html, str):
            self.set_html(html)


    def _w_init(self, kwargs):
        #------------------------------------------------------------------------------------------
        if not 'wrap' in kwargs.keys():
            self.config(wrap='word')
        if not 'background' in kwargs.keys():
            if sys.platform.startswith('win'):
                self.config(background='SystemWindow')
            else:
                self.config(background='white')


    def fit_height(self):
        #------------------------------------------------------------------------------------------
        """
        Fit widget height to wrapped lines
        """
        for h in range(1, 4):
            self.config(height=h)
            self.master.update()
            if self.yview()[1] >= 1:
                break
        else:
            self.config(height=0.5+3/self.yview()[1])


    def set_html(self, html, strip=True):
        #------------------------------------------------------------------------------------------
        """
        Set HTML widget text. If strip is enabled (default) it ignores spaces and new lines.

        """
        prev_state = self.cget('state')
        self.config(state=tk.NORMAL)
        self.delete('1.0', tk.END)
        for tag in self.tag_names(): self.tag_delete(tag)
        self.html_parser.w_set_html(self, html, strip=strip)
        self.config(state=prev_state)
        self.config(cursor="")


class HTMLText(HTMLScrolledText):
    #----------------------------------------------------------------------------------------------
    """
    HTML text widget
    """
    def _w_init(self, kwargs):
        #------------------------------------------------------------------------------------------
        super()._w_init(kwargs)
        self.vbar.pack_forget()

    def fit_height(self):
        #------------------------------------------------------------------------------------------
        super().fit_height()
        #self.master.update()
        self.vbar.pack_forget()

class HTMLLabel(HTMLText):
    #----------------------------------------------------------------------------------------------
    """
    HTML label widget
    """
    def _w_init(self, kwargs):
        #------------------------------------------------------------------------------------------
        super()._w_init(kwargs)
        if not 'background' in kwargs.keys():
            if sys.platform.startswith('win'):
                self.config(background='SystemButtonFace')
            else:
                self.config(background='#d9d9d9')
                
        if not 'borderwidth' in kwargs.keys():
            self.config(borderwidth=0)

        if not 'padx' in kwargs.keys():
            self.config(padx=3)
        
    def set_html(self, *args, **kwargs):
        #------------------------------------------------------------------------------------------
        super().set_html(*args, **kwargs)
        self.config(state=tk.DISABLED)



def main():
    print (get_text(None, None))

if __name__ == '__main__':
    main()        
