#!/usr/bin/python3.4


if __name__ != '__main__':
    exit()

from elf import *
from extract_strings import *
import find_xref
from time import time


print("Ищем строки в исходном файле")
words = extract_strings('Dwarf_Fortress')

test = ELF("Dwarf_Fortress")
hdr = ELF_header(test)
all_data = test.file_object.getvalue()

#Предел поиска строк
MAX_TO_FIND = hdr.prog_header[2].filesz


print("Загружаются строки перевода")
trans = load_trans_mo('trans.mo')


print("Поиск строк-близнецов")
start = time()
gemini = find_gemini(words, trans)
chk = check_founded_gemini(gemini, all_data)
print("Поиск занял", time() - start, "c")

words.update(chk)

print("Записываем trans.txt")
trans_txt = open('trans.txt', 'wt')
for word in words.keys():
    trans_txt.write("%s|%i\n" % (word, words[word]))
trans_txt.close()

print("Поиск перекрестных ссылок")
#Ищем указатели на используемые строки, в несколько потоков
start = time()
xref = find_xref.find(words, MAX_TO_FIND, all_data, load_from_cache=False)
print("Поиск занял", time() - start, "c")





