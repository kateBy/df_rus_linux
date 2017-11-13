#!/usr/bin/python3
# -*- coding: utf-8 -*-

from extract_strings import *
import struct
import os
import find_xref
import opcodes
from os.path import exists
import subprocess


OLD_BASE_ADDR = 0x400000  # Стартовый виртуальный адрес ELF
RUS_SECTION = '/tmp/rus.dat'  # Файл с секцией .rus


"""Функция патча с указаной позиции встраивая jmp или call для перехвата
   управления в новую секцию"""
def makePatch(patchOffset, asm_file: str, jmp_type: str, **fasmvars):

    if jmp_type not in ["JMP", "CALL"]:
        print("Не выбран тип перехода. [JMP, CALL]")
        return

    global CURSOR
    offset = patchOffset

    e_df.seek(offset - OLD_BASE_ADDR)
    s = struct.Struct('<hI')
    _, off = s.unpack(e_df.read(6))

    func_addr = hex(patchOffset + off + 6)

    fasmvars['FUNC_ADDR'] = func_addr  # Задаем адрес функции, куда нужно сделать переход после патча

    args = " ".join(["-d" + k + "=" + v for k, v in fasmvars.items()])  # Аргументы для FASM

    bin_file = '/tmp/df_patch.bin'
    os.system('fasm %s %s %s' % (asm_file, args, bin_file))

    JMP_CALL_SZ = 5

    if exists(bin_file):
        if jmp_type == "CALL":
            jmp = opcodes.make_call(offset + JMP_CALL_SZ, CURSOR + NEW_BASE_ADDR)
        elif jmp_type == "JMP":
            jmp = opcodes.make_near_jmp(offset + JMP_CALL_SZ, CURSOR + NEW_BASE_ADDR)

        e_df.seek(offset - OLD_BASE_ADDR)
        e_df.write(jmp)  # Создаем JMP-перехват управления на новую функцию

        asm_patch = open(bin_file, 'rb').read()
        e_df.seek(CURSOR+NEW_OFFSET)
        e_df.write(asm_patch)  # Записываем результат работы FASM в файл

        CURSOR += len(asm_patch) + JMP_CALL_SZ + 1
        os.remove(bin_file)
    else:
        print("---> !!!Ошибка при сборке asm-модуля!!!")


# Т.к. операция используется много раз
def little4bytes(x: int) -> bytes:
    return x.to_bytes(4, byteorder="little")



if __name__ != '__main__':
    exit()

DF = "Dwarf_Fortress"
NEW_DF = "Edited_DF"

print("Загружаются строки перевода")
trans = load_trans_po('trans.po')

print("Создаётся файл для новой секции с переводом")
rus_words = make_dat_file(RUS_SECTION, trans)

# Получаем сдвиг новой секции в памяти, выравниваем по 4096

bss = shell("objdump -x '%s' | grep \.bss | awk '{print $3,$4}'" % DF)
bss_len, bss_offset = bss.split(" ")
NEW_BASE_ADDR = ((int(bss_offset, 16) + int(bss_len, 16))//4096 + 1) * 4096

# Созданный файл с новыми строками вставляется как новая секция
print("Создаётся модифицированный исполняемый файл")
os.system("objcopy '%s' '%s' --add-section .rus=%s" % (DF, NEW_DF, RUS_SECTION))
os.system("objcopy '%s' --set-section-flags .rus=A --change-section-vma .rus=0x%X" % (NEW_DF, NEW_BASE_ADDR))
os.remove(RUS_SECTION)

e_df = open(NEW_DF, "r+b")
all_data = e_df.read()


rodata = shell("objdump -x '%s' | grep \.rus | awk '{print $3,$4,$6}'" % NEW_DF)
rus_size, rus_vaddr, rus_offset = [int(x, 16) for x in rodata.split(" ")]

NEW_OFFSET = rus_offset

# Читаем заголовок elf64
elf64header = struct.Struct("16sHHIQQQIHHHHHH").unpack(all_data[:64])
prgHdrOffset = elf64header[5]  # Смещение Program Header
prgEntrySize = elf64header[9]  # Длина одной записи в Program Header
prgEntryCount = elf64header[10]  # Количество записей в Program Header


# Создаётся запись для программного заголовка с указателями на новую секцию
# без этой правки новая секция не будет подгружена в память
template = struct.Struct("IIQQQQQQ")
h0 = template.pack(1,              # Type of segment    | LOAD
                   0b100,          # Segment attributes | r--
                   rus_offset,     # Offset in file     |
                   NEW_BASE_ADDR,  # Vaddr in memory    |
                   0x100000,       # Reserved           |
                   0x100000,       # Size in file       |
                   0x100000,       # Size in memory     |
                   4)              # Alignment          | 2**2


"""
prgHdrOffset-длина заголовка,
prgEntrySize-длина секции
7-номер секции, которую можно переписать
"""
e_df.seek(prgHdrOffset + prgEntrySize * 7)
e_df.write(h0)

print("Поиск перекрестных ссылок")
# Ищем указатели на используемые строки, в несколько потоков
words = extract_strings(DF)
xref = find_xref.find(words, 0, all_data, load_from_cache=True)

print("Перевод...")

for word in xref:
    # Если строки из бинарника нет в переводе просто проигнорируем это
    word_offset = rus_words.get(word)  # Смещение слова в секции .rus

    if word_offset is not None:

        new_index = word_offset + NEW_BASE_ADDR
        all_poses = xref[word]

        # Обрабатываем все найденые индексы
        for pos in all_poses:
            e_df.seek(pos)
            e_df.write(little4bytes(new_index))

print("Патчим множественное число")
# Находим перехватом функции string::assign в меню Статус (кнопка z)
# Т.к. неизвестно какое слово, оканчивающееся на 's' выберет компилятор
S_OFFSET = 0x12b83c7
e_df.seek(S_OFFSET - OLD_BASE_ADDR)
e_df.write(b" \x00")

print("Патчим строку \"Готовить\"")
# Ищем среди нескольких ссылок в cache.json -> "Cook"
COOK_OFFSET = 0x954583
e_df.seek(COOK_OFFSET - OLD_BASE_ADDR)
_cook = rus_words["__COOK__"] + NEW_BASE_ADDR
MOV_ESI = b"\xbe"
e_df.write(MOV_ESI + little4bytes(_cook))

#print("Патчим надписи в главном меню...")
#MAIN_MENU_OFFSETS = [(0x9B9568, 20), (0x9B969a, 26), (0x9B9742, 24)]
#for mainmenu in MAIN_MENU_OFFSETS:
#    off, xpos = mainmenu
#    e_df.seek(off - OLD_BASE_ADDR)
#    e_df.write(b"\x83\xe8" + int.to_bytes(xpos, 1, 'little')) #sub eax, 20

CURSOR = rus_words["CURSOR"]

print("Патчится функция  std::string::assign(char  const*, uint)")
# _ZNSs6assignEPKcm
makePatch(0x405870, 'asm/str_len.asm', 'JMP', RU_OFFSET=hex(rus_vaddr), RU_SIZE=hex(rus_size))

print("Патчится функция  std::string::append(char  const*, uint)")
# _ZNSs6appendEPKcm
makePatch(0x4055e0, 'asm/str_len.asm', 'JMP', RU_OFFSET=hex(rus_vaddr), RU_SIZE=hex(rus_size))

print("Патчится функция  std::string::string(char  const*, ...")
# _ZNSsC1EPKcRKSaIcE
makePatch(0x405cb0, 'asm/str_str_patch.asm', 'JMP')

# print("Патчится функция  вывода мыслей и предпочтений")
# makePatch(0x9c15ef, 'asm/str_resize_patch.asm', 'CALL')

print("Сохраняется результат...")
e_df.close()

print("Успех!")





