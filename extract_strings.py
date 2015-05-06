from elf import *


chars = [i for i in range(ord(" "), 127)]
nums = b'1234567890'


def check_forbidden(byte_string):
    if len(byte_string) < 2:
        return None
    #if byte_string[0] == ord("["):
    #    if byte_string.startswith(b"[NAME:") or byte_string.startswith(b"[ATTACK:EDGE") or byte_string.startswith(b"[ATTACK:BLUNT"):
    # #       return byte_string.decode()
    #    else:    
    #        return None
        
    if byte_string[0] in nums:
        return None
    for char in byte_string:
        if not (char in chars):
            return None
    #if byte_string == byte_string.upper():
    #    return None
            
    return byte_string.decode()

#Возможные начала фраз, которые комплятор слепил вместе
possible_gemini = [": ", ", ",
                   " was ", "claimed ",
                   " on a w",            # him
                   " into the area",     # ' around'
                   "was entombed ",      # in
                   "wild ",              # beasts
                   "How are you,",       # ' my '
                   
                   
                   "Very ", "Not ", "Seek ", "Recruit/",
                   "Seek Animal for ", "Orders: ", "Zone, ",
                   "Any ", "Apply ", "Metal ", "Siege ",
                   "Trap ", "Training ", "Other ", "Auto ",
                   "Engrave ", "Toggle ", "Set ", "How ",
                   "Age of ",  "Give ", "Getting ",
                   "Imported ", "Prepared ", " Gather ", "Store ",
                   ": No Auto ", "south", "north", "forgetful "

                   "Below ", "Above ", "Elite ", "Master ", "Enemy ",
                   "Friendly ", "Abduction/" "Death/"

                   

                   "Hotkey: ",
                   "Forge, ", "Fishery, ", "Glass ", "Jeweler, ", "Leather, "]

def check_for_gemini(some_word, words, index):
    for gemini in possible_gemini:
        if some_word == gemini:
            continue
        if some_word.startswith(gemini):
            words[some_word[len(gemini):]] = index + len(gemini)
            check_for_gemini(some_word[len(gemini):], words, index + len(gemini)) #Рекурсивно вызываем еще раз для проверки


def extract_strings(fn):

    test = ELF(fn)
    hdr = ELF_header(test)


    
    for entry in hdr.section_header.entries:                        #Поиск адресов строк и их адресов
            if entry.text_name == ".rodata":
                    break
                
    rodata = test.read(entry.offset, entry.size)
    rodata_vaddr = entry.addr
    
    max_index = len(rodata)
    index = 0
    words = {}
    while index < max_index:
        if rodata[index] in chars:
            next_zero = rodata.find(0, index)
            if next_zero != 0:
                checked = check_forbidden(rodata[index:next_zero])
                if checked != None:
                    words[checked] = index + rodata_vaddr
                    check_for_gemini(checked, words, index + rodata_vaddr)
            
                index = next_zero
            

        index += 1
    return words


def load_trans_txt(fn):
    trans = open(fn, 'rt', encoding="cp1251")
    words = {}
    for line in trans:
        splitted = line.split("|")
        if len(splitted) < 4:
            continue
        else:
            words[splitted[1]] = splitted[2]

    return words

def load_trans_mo(fn):
    import polib
    result = {}
    mofile = polib.mofile(fn)
    for i in mofile:
        result[i.msgid] = i.msgstr

    return result


def compare(words, trans):
    not_found = []
    for i in words:
        try:
            tmp = trans[i]
        except KeyError:
            not_found.append(i)
            
    return not_found

"""Создаёт секцию с новыми строками и возвращает словарь,
содержащий английскую версию строки и индекс ее в новой секции"""
def make_dat_file(fn, trans, add_zeros_to = 0x100000):
    from io import BytesIO
    result = {}
    offset = 0
    file = BytesIO()
    for i in trans:
        result[i] = offset
        encoded = trans[i].encode('cp1251') + b"\x00"
        file.write(encoded)
        offset += len(encoded)

    if offset < add_zeros_to:
        file.write(b"\x00" * (add_zeros_to - offset))

    open(fn, 'wb').write(file.getvalue())

    result[-1] = offset

    return result

"""Разбивает словарь на несколько словарей,
нужно для запуска нескольких потоков замены индексов"""
def split_dictionary(dictionary, count):
    split_by = len(dictionary) // count
    result = []
    tmpdict={}
    counter = 0
    for i in dictionary:
        tmpdict[i] = dictionary[i]
        counter += 1
        if counter == split_by:
            result.append(tmpdict)
            tmpdict = {}
            counter = 0

    return result






















