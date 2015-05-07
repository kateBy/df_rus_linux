from elf import *


chars = [i for i in range(ord(" "), 127)]
nums = b'1234567890'

"""Проверяем найденую строку на нечитаемые символы"""
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

#Поиск строк-близнецов постепенно отрезая от исходной строки буквы
def find_gemini(words, translated):
    result = {}
    for word in words:
        max_i = len(word)
        i = 1
        
        while i < max_i-2:
            if word[i:] in translated:
                if not (word[i:] in words):
                     result[words[word] + i] = word[i:]
                    

            i += 1

    return result


"""Ищет все включения байтов в буфере"""
def find_bytes(some_bytes, buf_find):
    #last = 0
    result = []
    #while last != -1:
    last = buf_find(some_bytes, last + 1)
    if last != -1:
        result.append(last)

    return last


"""Проверяем, имеется ли в буфере ссылка с таким адресом"""
def check_founded_gemini(gemini, buf):
    result = {}
    buf_find = buf.find
    max_ind = len(gemini)
    ind = 0
    for g in gemini:
        ind += 1
        #founded = find_bytes(int.to_bytes(g, 4, byteorder="little"), buf_find)
        link_byte = buf_find(int.to_bytes(g, 4, byteorder="little"))
        if link_byte != -1:
            if gemini[g] in result:
                print(gemini[g], "--->" ,hex(int.from_bytes(buf[link_byte:link_byte+4], 'little')), hex(g))
                      
            result[gemini[g]] = int.from_bytes(buf[link_byte:link_byte+4], 'little')
        if (ind % 100) == 0:
            print("%.2f" % (ind / max_ind * 100), "%")


    SPLIT_SYMBOL = "<*|*>"


    cache_file = open('gemini_cache.txt', 'wt')
    for w in result:
        line = str(w) + SPLIT_SYMBOL + str(result[w]) + "\n"
        cache_file.write(line)

    cache_file.close()
        

    return result

            


"""Извлекает все похожее на строки из секции .rodata"""
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
                    #check_for_gemini(checked, words, index + rodata_vaddr, translated)
            
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






















