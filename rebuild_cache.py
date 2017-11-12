#!/usr/bin/python3

from extract_strings import *
import find_xref
from time import time

if __name__ != '__main__':
    exit()

DF = 'Dwarf_Fortress'

print("Ищем строки в исходном файле")
words = extract_strings(DF)

data = open(DF, 'rb').read()
find = data.find

# Предел поиска строк
max_offset = len(data)  # FIXME длина не соответствует концу секции


print("Загружаются строки перевода")
trans = load_trans_po('trans.po')


print("Поиск строк-близнецов")
start = time()
gemini = find_gemini(words, trans)
chk = check_founded_gemini(gemini, data)
print("Поиск занял", time() - start, "c")

words.update(chk)

print("Поиск перекрестных ссылок")
# Ищем указатели на используемые строки, в несколько потоков

xref = find_xref.find(words, max_offset, data, load_from_cache=False)

print("Поиск занял", time() - start, "c")





