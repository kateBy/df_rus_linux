from extract_strings import *

SPLIT_SYMBOL = "<*|*>"
OLD_BASE_ADDR = 0x08048000

trans = load_trans_mo('trans.mo')

all_data = open('Dwarf_Fortress', 'rb').read()

b = []

def show_string(vaddr):
    off = vaddr - OLD_BASE_ADDR

    zero = all_data.find(b"\x00", off)

    if zero != -1:
        if zero - off < 100:
           b.append(all_data[off:zero])
        else:
            print("Слишком далеко нулевой байт", zero - off)

    return all_data[off:zero]


cache5 = open('gemini_cache-5.txt', 'rt').readlines()
cache6 = open('gemini_cache-6.txt', 'rt').readlines()

gemini5 = {}
for i in cache5:
    word, vaddr = i.split(SPLIT_SYMBOL)
    gemini5[word] = int(vaddr.strip())

gemini6 = {}
for i in cache6:
    word, vaddr = i.split(SPLIT_SYMBOL)
    gemini6[word] = int(vaddr.strip())

g5_g6 = []
for g5 in gemini5:
    if not (g5 in gemini6):
        g5_g6.append(g5)



##failed = []
##for i in gemini:
##    in_bin = show_string(gemini[i])
##    if i != in_bin.decode():
##        print("\'%s\'" % i, "--->",in_bin)

##for i in b:
##    if len(i) == 10:
##        print(i)



            

