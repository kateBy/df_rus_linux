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


cache = open('gemini_cache.txt', 'rt').readlines()

gemini = {}
for i in cache:
    word, vaddr = i.split(SPLIT_SYMBOL)
    gemini[word] = int(vaddr.strip())


failed = []
for i in gemini:
    in_bin = show_string(gemini[i])
    if i != in_bin.decode():
        print("\'%s\'" % i, "--->",in_bin)

##for i in b:
##    if len(i) == 10:
##        print(i)



            

