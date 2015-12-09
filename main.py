#!/usr/bin/python3.4
# -*- coding: utf-8 -*-


if __name__ != '__main__':
    exit()

from elf import *
from extract_strings import *
import sys
import os
import find_xref
import opcodes


#Функция, использовалась при отладке для поиска
def get_ip(text):
    last = 0
    test_addr = words[text].to_bytes(4, 'little')
    while last != -1:
        last = all_data.find(test_addr, last+1)
        if last != -1:
            return hex(last + OLD_BASE_ADDR)

def get_last(text):
    for x in words:
        if x.endswith(text):
            _addr = get_ip(x)
            if _addr != None:
                print(_addr, '--> "%s"' % x)

def find_word(bytes_word, print_length = 10):
    last = 0
    while last != -1:
        last = all_data.find(bytes_word, last + 1)
        if last != -1:
            print("0x%X -->" % (last + OLD_BASE_ADDR), all_data[last:last+print_length])



print("Загружаются строки перевода")
trans = load_trans_po('trans.po')

print("Ищем строки в исходном файле")
words = extract_strings('Dwarf_Fortress')


print("Создаётся файл для новой секции с переводом")
rus_words   = make_dat_file('rus.dat', trans)

#Получаем сдвиг новой секции в памяти, выравниваем по 4096
try:
    os.system("readelf ./Dwarf_Fortress -e | grep \]\ \.bss | awk '{print $4, $6}' > /tmp/dwarf_base_addr")
    bss_offset, bss_len = open('/tmp/dwarf_base_addr').read().strip().split(" ")
    os.remove('/tmp/dwarf_base_addr')
    NEW_BASE_ADDR = ((int(bss_offset,16) + int(bss_len, 16))//4096 + 1 ) * 4096
except:
    print("Ошибка при получении адреса секции")
    exit()

#NEW_BASE_ADDR = 40694*4096 #0x9ef6000

#Созданный файл с новыми строками вставляется как новая секция
print("Создаётся модифицированный исполняемый файл")
os.system("objcopy ./Dwarf_Fortress ./Edited_DF  --add-section .rus=rus.dat")
os.system("objcopy ./Edited_DF --set-section-flags .rus=A")
os.system("objcopy ./Edited_DF --change-section-vma .rus=%s" % hex(NEW_BASE_ADDR))

test = ELF("Edited_DF")
hdr = ELF_header(test)
all_data = test.file_object.getvalue()

OLD_BASE_ADDR = 0x08048000

try:
    os.system("readelf ./Edited_DF -e | grep \]\ \.rus | awk '{print $5}' > /tmp/dwarf_offset")
    rus_offset = open('/tmp/dwarf_offset').read().strip()
    os.remove('/tmp/dwarf_offset')
    NEW_OFFSET = int(rus_offset, 16)
except:
    print("Ошибка при получении сдвига секции в памяти")
    exit()
              
#NEW_OFFSET = 5029*4096

#Создаётся запись для программного заголовка с указателями на новую секцию
#без этой правки новая секция не будет подгружена в память
template = struct.Struct("IIIIIIII")
h0 = template.pack(1, NEW_OFFSET, NEW_BASE_ADDR,  NEW_BASE_ADDR, 0x100000, 0x100000, 4, 4096)

#52-длина заголовка, 32-длина секции, 7-номер секции, которую можно переписать
test.write(52 + 32 * 7, h0)

MAX_TO_FIND = hdr.prog_header[2].filesz


print("Поиск перекрестных ссылок")
#Ищем указатели на используемые строки, в несколько потоков
xref = find_xref.find(words, MAX_TO_FIND, all_data, load_from_cache=True)

print("Перевод...")


for test_word in xref:
   
    try:
        #Если строки из бинарника нет в переводе просто проигнорируем это
        new_index = rus_words[test_word] + NEW_BASE_ADDR
        all_poses = xref[test_word]
    except KeyError:
        continue

    #Обрабатываем все найденые индексы и корректируем длину строки в коде
    for pos in all_poses:
        test.write(pos, new_index.to_bytes(4, byteorder="little"))

                               #edi   eax   ecx   edx   ebx   ebp   esi
        if all_data[pos-6] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
            if all_data[pos-5] == len(test_word):
                test.write(pos-5, len(trans[test_word]).to_bytes(4, 'little'))
                #print("GOT IT!", test_word, trans[test_word])

        
                               #edi, eax   ecx    edx   ebx   ebp   esi
        if all_data[pos+4] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
            if all_data[pos+5] == len(test_word):
                #Случаи, когда после вызова строки ее размер заносится в edi
                test.write(pos+5, len(trans[test_word]).to_bytes(4, 'little'))
                continue

        if all_data[pos+9] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
            if all_data[pos+10] == len(test_word):
                test.write(pos+10, len(trans[test_word]).to_bytes(4, 'little'))
                continue

        if all_data[pos-16] == 0xb8:
            if all_data[pos-15] == (len(test_word)+1):
                
                """
                Непонятно почему используется значение +1 в меню
                Создать с доп. параметрами
                Арена тестирования объектов
                """
                
                test.write(pos-15, (len(trans[test_word])+1).to_bytes(4, 'little'))
                continue
##
##        if all_data[pos+12] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
##            if all_data[pos+13] == (len(test_word)):
##                print(pos, "FOUND CORRECT SIZE", test_word)
##                test.write(pos+13, (len(trans[test_word])).to_bytes(4, 'little'))
##                continue
##            
##            if all_data[pos+13] == (len(test_word)+1):
##                print(pos, "FOUND SIZE+1", test_word)
##                """Пока что один случай: '  Squad Schedules: '"""
##                test.write(pos+13, (len(trans[test_word])+1).to_bytes(4, 'little'))
##                continue

        

        n = all_data.find(len(test_word).to_bytes(4,'little'),pos - 20, pos)

        if n != -1:
            #Случаи, когда перед вызовом строки в регистр, а после в стёк заносится ее 4-байтная длина
            test.write(n, len(trans[test_word]).to_bytes(4, 'little'))
            
print("Отдельные строки для главного меню")


CURSOR = rus_words[-1]


main_menu = {"Продолжить Игру": b"Cont",
             "Начать Игру":b"Star",
             " Выход ":b"Quit",
             "Создать Новый Мир!":b"Crea",
             "Об Игре":b"Abou",
             }

start_bytes = b"\xc7\x06"
for menuitem in main_menu:
    old_off = all_data.find(start_bytes + main_menu[menuitem])
    if old_off == -1:
        print("NOT FOUND", menuitem)
        continue
    new_off = CURSOR
    CURSOR += opcodes.make_new_string(old_off, new_off, menuitem,
                                     test, OLD_BASE_ADDR, NEW_BASE_ADDR, NEW_OFFSET, all_data)




   

print("Сохраняется результат...")
test.save()

os.remove('./rus.dat')

print("Успех!")





