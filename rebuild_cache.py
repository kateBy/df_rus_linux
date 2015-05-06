#!/usr/bin/python3.4


if __name__ != '__main__':
    exit()

from elf import *
from extract_strings import *
import find_xref


print("Ищем строки в исходном файле")
words = extract_strings('Dwarf_Fortress')



test = ELF("Dwarf_Fortress")
hdr = ELF_header(test)
all_data = test.file_object.getvalue()

MAX_TO_FIND = hdr.prog_header[2].filesz


print("Загружаются строки перевода")
trans = load_trans_mo('trans.mo')
print("Поиск строк-близнецов")
gemini = find_gemini(words, trans)
chk = check_founded_gemini(gemini, all_data)

words.update(chk)


print("Поиск перекрестных ссылок")
#Ищем указатели на используемые строки, в несколько потоков
xref = find_xref.find(words, MAX_TO_FIND, all_data, load_from_cache=False)






