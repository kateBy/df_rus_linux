"""Модуль содержит функции для извлечения строк из исполняемого файла
а так же поиска т.н. близнецов строк, т.к. GCC для строк, которые содержатся
в других строках использует одни и те же строки, только со смещением,
например:
The finest place,0 и place,0 будут совмещены в одно место, только при запросе
строки 'place' будет дана ссылка на [The finest place]+12 и т.д."""

chars = set(i for i in range(32, 127))
nums = b'1234567890'



"""Проверяем найденую строку на нечитаемые символы"""
def check_forbidden(byte_string):
    if len(byte_string) < 2:
        return None
        
    if byte_string[0] in nums:
        return None
    for char in byte_string:
        if not (char in chars):
            return None

            
    return byte_string.decode()



"""Поиск строк-близнецов постепенно отрезая от исходной строки буквы
а после - сравнение со словарём переводов, если строка имеется в переводах,
заносим ее в список"""
def find_gemini(words, translated):
    result = {}
    for word in words:
        max_i = len(word) - 1
        i = 1

        while i < max_i:
            if word[i:] in translated:
                if not (word[i:] in words):
                    result[words[word] + i] = word[i:]

            i += 1

    return result



"""Проверяем, имеется ли в буфере ссылка с таким адресом"""
def check_founded_gemini(gemini, buf):
    result = {}
    buf_find = buf.find
    max_ind = len(gemini)
    ind = 0
    for g in gemini:
        ind += 1
        link_byte = buf_find(int.to_bytes(g, 4, byteorder="little"))
        if link_byte != -1:
            if gemini[g] in result:
                print(gemini[g], "--->", hex(int.from_bytes(buf[link_byte:link_byte+4], 'little')), hex(g))
                      
            result[gemini[g]] = int.from_bytes(buf[link_byte:link_byte+4], 'little')
        if (ind % 100) == 0:
            print("%.2f" % (ind / max_ind * 100), "%")

    return result

            

"""Извлекает все похожее на строки из секции .rodata"""
def extract_strings(fn):
    import subprocess
    rodata = subprocess.check_output("objdump -x " + fn + " | grep \.rodata | awk '{print $3,$4,$6}'", shell=True).decode().strip()
    rodata_size, rodata_vaddr, rodata_offset = [int(x, 16) for x in rodata.split(" ")]

    _file = open(fn, "rb")
    _file.seek(rodata_offset)
    rodata = _file.read(rodata_size)
    _file.close()
    
    index = 0
    words = {}
    
    while index < rodata_size:
        if rodata[index] in chars:
            next_zero = rodata.find(0, index)
            if next_zero != -1:
                checked = check_forbidden(rodata[index:next_zero])
                if checked is not None:
                    words[checked] = index + rodata_vaddr
                index = next_zero
            
        index += 1
    return words



'''Загрузка перевода из файла .po с помощью библиотеки polib'''
def load_trans_po(fn):
    import polib
    result = {}
    pofile = polib.pofile(fn)
    for i in pofile:
        if i.msgid.endswith(' '):      # Англ. кончается на пробел
            angl_spaces = len(i.msgid) - len(i.msgid.rstrip())
            ru_spaces = len(i.msgstr) - len(i.msgstr.rstrip())
            if angl_spaces != ru_spaces:
                result[i.msgid] = i.msgstr.rstrip() + ' ' * angl_spaces
            else:
                result[i.msgid] = i.msgstr
        else:      
            result[i.msgid] = i.msgstr

    return result



"""Создаёт секцию с новыми строками и возвращает словарь,
содержащий английскую версию строки и индекс ее в новой секции.
Перед строкой стоит 4 байта длины этой строки для использования в функции
Строки разделяются между собой одинарным нулём"""
def make_dat_file(fn, trans, size=0x100000) -> dict:
    from io import BytesIO
    result = {}
    offset = 0
    file = BytesIO()
    file.write(b"\x00" * size)
    file.seek(0)

    trans["'s"] = " "  # Пустая строка притяжательного падежа

    for i in trans:
        result[i] = offset + 4  # Перед строкой идет 4 байта ее длины
        encoded = trans[i].encode('cp1251') + b"\x00"
        ru_len = len(encoded)
        file.write((ru_len-1).to_bytes(4, 'little'))  # Записываем длину строки
        file.write(encoded)
        offset += ru_len + 4

    # Особый патч строки "Готовить"
    result["__COOK__"] = offset + 4
    cook = "Готовить".encode('cp1251') + b"\x00"
    file.write((len(cook)-1).to_bytes(4, 'little'))
    file.write(cook)
    offset += len(cook) + 4
    
    open(fn, 'wb').write(file.getvalue())

    result["CURSOR"] = offset

    return result



"""Разбивает словарь на несколько словарей,
нужно для запуска нескольких потоков замены индексов"""
def split_dictionary(some_dict, out_count):
    result = [{} for _ in range(out_count)]
    cursor = 0

    for i in some_dict:
        result[cursor][i] = some_dict[i]
        cursor += 1
        if cursor == out_count:
            cursor = 0

    return result


