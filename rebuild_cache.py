#!/usr/bin/python3.4


if __name__ != '__main__':
    exit()

from extract_strings import *
import find_xref
from time import time


print("Ищем строки в исходном файле")
words = extract_strings('Dwarf_Fortress')

all_data = open("Dwarf_Fortress", 'rb').read()

#Предел поиска строк
MAX_TO_FIND = len(all_data) #FIXME длина не соответствует концу секции


print("Загружаются строки перевода")
trans = load_trans_po('trans.po')


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





