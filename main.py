#!/usr/bin/python3.4
# -*- coding: utf-8 -*-


if __name__ != '__main__':
    exit()

from extract_strings import *
import struct
import sys
import os
import find_xref
import opcodes
from os.path import exists

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
rus_words   = make_dat_file('/tmp/rus.dat', trans)

#Получаем сдвиг новой секции в памяти, выравниваем по 4096
try:
    os.system("objdump -x ./Dwarf_Fortress | grep \.bss | awk '{print $4,$3}' > /tmp/dwarf_base_addr")
    bss_offset, bss_len = open('/tmp/dwarf_base_addr').read().strip().split(" ")
    os.remove('/tmp/dwarf_base_addr')
    NEW_BASE_ADDR = ((int(bss_offset,16) + int(bss_len, 16))//4096 + 1 ) * 4096
except:
    print("Ошибка при получении адреса секции")
    exit()


#Созданный файл с новыми строками вставляется как новая секция
print("Создаётся модифицированный исполняемый файл")
os.system("objcopy ./Dwarf_Fortress ./Edited_DF  --add-section .rus=/tmp/rus.dat")
os.system("objcopy ./Edited_DF --set-section-flags .rus=A")
os.system("objcopy ./Edited_DF --change-section-vma .rus=%s" % hex(NEW_BASE_ADDR))
os.remove('/tmp/rus.dat')

e_df = open("./Edited_DF", "r+b")
all_data = e_df.read()

OLD_BASE_ADDR = 0x08048000

try:
    os.system("objdump -x ./Edited_DF | grep \.rus | awk '{print $6}' > /tmp/dwarf_offset")
    rus_offset = open('/tmp/dwarf_offset').read().strip()
    os.remove('/tmp/dwarf_offset')
    NEW_OFFSET = int(rus_offset, 16)
except:
    print("Ошибка при получении сдвига секции в памяти")
    exit()
              
#Создаётся запись для программного заголовка с указателями на новую секцию
#без этой правки новая секция не будет подгружена в память
template = struct.Struct("IIIIIIII")
h0 = template.pack(1, NEW_OFFSET, NEW_BASE_ADDR,  NEW_BASE_ADDR, 0x100000, 0x100000, 4, 4096)

#52-длина заголовка, 32-длина секции, 7-номер секции, которую можно переписать
e_df.seek(52 + 32 * 7)
e_df.write(h0)

print("Поиск перекрестных ссылок")
#Ищем указатели на используемые строки, в несколько потоков
xref = find_xref.find(words, 0, all_data, load_from_cache=True)

print("Перевод...")

#Т.к. операция используется много раз
little4bytes = lambda x: x.to_bytes(4, byteorder="little")


for test_word in xref:
   
    try:
        #Если строки из бинарника нет в переводе просто проигнорируем это
        new_index = rus_words[test_word] + NEW_BASE_ADDR
        all_poses = xref[test_word]
    except KeyError:
        continue

    #Обрабатываем все найденые индексы и корректируем длину строки в коде
    for pos in all_poses:
        e_df.seek(pos)
        e_df.write(little4bytes(new_index))

                               #edi   eax   ecx   edx   ebx   ebp   esi
        if all_data[pos-6] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
            if all_data[pos-5] == len(test_word):
                e_df.seek(pos-5)
                e_df.write(little4bytes(len(trans[test_word])))
                continue

        
                               #edi, eax   ecx    edx   ebx   ebp   esi
        if all_data[pos+4] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
            if all_data[pos+5] == len(test_word):
                #Случаи, когда после вызова строки ее размер заносится в edi
                e_df.seek(pos+5)
                e_df.write(little4bytes(len(trans[test_word])))
                continue

        if all_data[pos+9] in [0xbf, 0xb8, 0xb9, 0xba, 0xbb, 0xbd, 0xbe]:
            if all_data[pos+10] == len(test_word):
                e_df.seek(pos+10)
                e_df.write(little4bytes(len(trans[test_word])))
                continue

        if all_data[pos-16] == 0xb8:
            if all_data[pos-15] == (len(test_word)+1):
                
                """
                Непонятно почему используется значение +1 в меню
                Создать с доп. параметрами
                Арена тестирования объектов
                """
                e_df.seek(pos-15)
                e_df.write(little4bytes(len(trans[test_word])+1))
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

        

        n = all_data.find(little4bytes(len(test_word)),pos - 20, pos)

        if n != -1:
            #Случаи, когда перед вызовом строки в регистр, а после в стёк заносится ее 4-байтная длина
            e_df.seek(n)
            e_df.write(little4bytes(len(trans[test_word])))
    
print("Отдельные строки для главного меню")


CURSOR = rus_words[-1]


main_menu = {"Продолжить Игру": b"Cont",
             "Начать Игру":b"Star",
             " Выход ":b"Quit",
             "Создать Новый Мир!":b"Crea",
             "Об Игре":b"Abou",

             #Меняющийся заголовок
             "Истории о ":b"Hist",
             #Слова в заголовке у них загрузка в стёк через eax
             "Жадности" : b"Gree",
             "Алчности" : b"Avar",
             "Настойчивости":b"Pers",
             "Зависти":b"Jeal",
             "Решительности":b"Dete",
             "Обжорстве":b"Glut",
             "Храбрости":b"Mett",
             "Ненасытности":b"Cupi",
             "Динамичности":b"Dyna",
             "Упорстве":b"Tena",
             "Старании":b"Exer",
             "Предприимчивости":b"Ente",
             "Усердии":b"Dili",
             "Усердном труде":b"Toil",
             "Трудолюбии":b"Indu",
             "Находчивости":b"Reso",
             " и ":b" and"
             }

#Варианты опкодов и сдвига в памяти в зависимости от вида
_start_bytes = {b"\xc7\x06":["esi",0],
                b"\xc7\x43\x0e":["esi",0], #Истории о
                b"\xc7\x42\x0e":["eax",0], #Для меняющихся слов в заголовке
                b"\xc7\x40\x0e":["eax",0xe]}

for menuitem in main_menu:
    for start_bytes in _start_bytes:
        old_off = all_data.find(start_bytes + main_menu[menuitem])
        if old_off != -1:
            opcode_and_offset = _start_bytes[start_bytes]     
            CURSOR += opcodes.make_new_string(old_off, CURSOR, menuitem,
                                     e_df, OLD_BASE_ADDR, NEW_BASE_ADDR, NEW_OFFSET, all_data, opcode_and_offset)


print("Патчится функция выравнивания строк")
offset = 0x8778C8C #FIXME найти способ нахождения функции автоматически
binFile = '/tmp/str_resize_path.bin'
os.system('bash ./asm/get_lib_addr.sh ' + binFile)

CALL_SIZE = 5
call = opcodes.make_call(offset + CALL_SIZE, CURSOR + NEW_BASE_ADDR)
e_df.seek(offset - OLD_BASE_ADDR)
e_df.write(call) #Создаем CALL-перехват управления на новую функцию
e_df.seek(CURSOR+NEW_OFFSET)
if exists(binFile):
    asm_patch = open(binFile, 'rb').read()
    e_df.write(asm_patch) #Записываем результат работы FASM в файл
    CURSOR += len(asm_patch) + 1
    os.remove(binFile)
else:
    print("---> !!!Ошибка при сборке asm-модуля!!!")




print("Сохраняется результат...")
e_df.close()

print("Успех!")





