import clientEngine as ce

T_NO_UNIT = '''<p>Выберите справа \u261B модуль в библиотке
для просмотра полной информации о нём.</p>'''
T_NO_LIB = '''<p>Выберите \u261A слева модуль или место подключения
в конфигурации вашего устройста
для просмотра полной информации о нём.</p>'''
T_BADCONF = '''<hr><p>Ваше устройство ещё не готово.\n
Проверьте внизу \u261F информацию о Зависимостях и Ресурсах,\n
добавьте или удалите модули и функции'''
T_GOODCONF = '''<hr><p>Ваше устройство сконфигурировано.\n
Вы можете Получить карту заказа или продолжить настройку'''
T_INS_TIP = '''<p>Чтобы добавить модуль из библиотеки в устройство,\n
выберите элемент библиотеки справа \u261B \n
и выберите \u261A слева место для его установки в устройство.\n
Совместимые элементы <span style="background-color: green">
выделяются зеленым </span> цветом.</p>'''
        

def get_text(unit, library):
    s = T_NO_UNIT if unit is None else unit_text(unit)
    s = s + '<hr>' + T_NO_LIB if library is None else lib_text(library)
    # if both selected - show possible add commands
    if unit is not None and library is not None:
        s = s + '<hr>' + insert_text(unit, library)
    # if only one selected - show tip
    elif unit is not None or library is not None:
        s = s + '<hr>' + T_INS_TIP
        
    stat = ce.getStatus()
    s = s + (T_GOODCONF if stat['Resources'] and stat['Requirements'] else T_BADCONF)
    return s

def unit_text(unit):
    pass

def lib_text(library):
    pass

def insert_text(unit, library):
    pass

def main():
    print (get_text(None, None))

if __name__ == '__main__':
    main()        
