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

"""Функция патча с указаной позиции встраивая jmp или call для перехвата
   управления в новую секцию"""
def makePatch(patchOffset, asmFile, jmpType, asmCommandLine = ""):
    global CURSOR
    offset = patchOffset
    binFile = '/tmp/df_patch.bin'
    os.system('fasm %s %s %s' % (asmFile, asmCommandLine, binFile))

    if not jmpType in ["JMP", "CALL"]:
        print("Не выбран тип перехода. [JMP, CALL]")
        exit()

    JMP_CALL_SZ= 5

    if exists(binFile):
        if jmpType == "CALL":
            jmp = opcodes.make_call(offset + JMP_CALL_SZ, CURSOR + NEW_BASE_ADDR)
        elif jmpType == "JMP":
            jmp = opcodes.make_near_jmp(offset + JMP_CALL_SZ, CURSOR + NEW_BASE_ADDR)
        else:
            exit()
            
        e_df.seek(offset - OLD_BASE_ADDR)
        e_df.write(jmp) #Создаем JMP-перехват управления на новую функцию

        asm_patch = open(binFile, 'rb').read()
        e_df.seek(CURSOR+NEW_OFFSET)
        e_df.write(asm_patch) #Записываем результат работы FASM в файл
        
        CURSOR += len(asm_patch) + JMP_CALL_SZ + 1
        os.remove(binFile)
    else:
        print("---> !!!Ошибка при сборке asm-модуля!!!")

DF = "Dwarf_Fortress64"
NEW_DF = "Edited_DF64"

print("Загружаются строки перевода")
trans = load_trans_po('trans.po')

print("Ищем строки в исходном файле")
words = extract_strings(DF)

print("Создаётся файл для новой секции с переводом")
rus_words   = make_dat_file('/tmp/rus.dat', trans)

#Получаем сдвиг новой секции в памяти, выравниваем по 4096
try:
    os.system("objdump -x "+ DF +" | grep \.bss | awk '{print $4,$3}' > /tmp/dwarf_base_addr")
    bss_offset, bss_len = open('/tmp/dwarf_base_addr').read().strip().split(" ")
    os.remove('/tmp/dwarf_base_addr')
    NEW_BASE_ADDR = ((int(bss_offset,16) + int(bss_len, 16))//4096 + 1 ) * 4096
except:
    print("Ошибка при получении адреса секции")
    exit()


#Созданный файл с новыми строками вставляется как новая секция
print("Создаётся модифицированный исполняемый файл")
os.system("objcopy "+DF+" "+NEW_DF+"  --add-section .rus=/tmp/rus.dat")
os.system("objcopy "+NEW_DF+" --set-section-flags .rus=A" +
          " --change-section-vma .rus=%s" % hex(NEW_BASE_ADDR))
os.remove('/tmp/rus.dat')

e_df = open(NEW_DF, "r+b")
all_data = e_df.read()

OLD_BASE_ADDR = 0x400000

try:
    os.system("objdump -x "+NEW_DF+" | grep \.rus | awk '{print $6}' > /tmp/dwarf_offset")
    rus_offset = open('/tmp/dwarf_offset').read().strip()
    os.remove('/tmp/dwarf_offset')
    NEW_OFFSET = int(rus_offset, 16)
except:
    print("Ошибка при получении сдвига секции в памяти")
    exit()

#Читаем заголовок elf64
elf64header = struct.Struct("16sHHIQQQIHHHHHH").unpack(all_data[:64])
prgHdrOffset  = elf64header[5] #Смещение Program Header
prgEntrySize  = elf64header[9] #Длина одной записи в Program Header
prgEntryCount = elf64header[10] #Количество записей в Program Header

              
#Создаётся запись для программного заголовка с указателями на новую секцию
#без этой правки новая секция не будет подгружена в память
template = struct.Struct("IIQQQQQQ")
h0 = template.pack(1,             #Type of segment    | LOAD
                   0b100,         #Segment attributes | r--
                   NEW_OFFSET,    #Offset in file     |
                   NEW_BASE_ADDR, #Vaddr in memory    |
                   0x100000,      #Reserved           |
                   0x100000,      #Size in file       |
                   0x100000,      #Size in memory     |
                   4)             #Alignment          | 2**2


"""prgHdrOffset-длина заголовка,
#prgEntrySize-длина секции
#7-номер секции, которую можно переписать"""
e_df.seek(prgHdrOffset + prgEntrySize * 7)
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

    #Обрабатываем все найденые индексы
    for pos in all_poses:
        e_df.seek(pos)
        e_df.write(little4bytes(new_index))

print("Патчим строку \"Готовить\"")
COOK_OFFSET = 0x9527c3
e_df.seek(COOK_OFFSET - OLD_BASE_ADDR)
_cook = rus_words["__COOK__"] + NEW_BASE_ADDR
e_df.write(b"\xbe" + little4bytes(_cook))

print("Патчим множественное число")
S_OFFSET = 0x12B95E7
e_df.seek(S_OFFSET - OLD_BASE_ADDR)
#e_df.write(b" \x00")

print("Патчим надписи в главном меню...")
MAIN_MENU_OFFSETS = [(0x9B9566, 19), (0x9B9698, 13), (0x9B9740, 15)]
for mainmenu in MAIN_MENU_OFFSETS:
    off, xpos = mainmenu
    e_df.seek(off - OLD_BASE_ADDR)
    e_df.write(b"\x48\xc7\xc0" + int.to_bytes(xpos, 4, 'little')) #mov rax, 19

global CURSOR
CURSOR = rus_words["CURSOR"]

print("Патчится функция  std::string::assign(char  const*, uint)")
makePatch(0x405870, 'asm/str_len.asm', 'JMP', '-dFUNC_ADDR=0x1707400')

print("Патчится функция  std::string::append(char  const*, uint)")
makePatch(0x4055e0, 'asm/str_len.asm', 'JMP', '-dFUNC_ADDR=0x17072B8')

print("Патчится функция  std::string::string(char  const*, ...")
makePatch(0x405cb0, 'asm/str_str_patch.asm', 'JMP', '-dFUNC_ADDR=0x1707620')

print("Патчится функция  вывода мыслей и предпочтений")
#makePatch(0x9c15ef, 'asm/str_resize_patch.asm', 'CALL')

print("Сохраняется результат...")
e_df.close()

print("Успех!")





