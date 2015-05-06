


def make_near_jmp(addr_from, addr_to):
    return b"\xe9" + (addr_to - addr_from).to_bytes(4, 'little', signed = True)






#Создаёт последовательность байт, аналогичную загрузке
#строк в главном меню, только выравнивает по 4
def load_str_by_stack(text):
    def dword_mov_esi(x): 
        #mov dword prt [esi + x] 
        if x == 0:
            return bytes([0xc7, 0x6])
        else:
            return bytes([0xc7, 0x46, x])

    
    enc_text = text.encode("cp1251") + b"\x00"
    enc_text += b"\x00" * (4 - len(enc_text) % 4)

    get = lambda x: enc_text[x*4:x*4+4]


    result = b""
    for i in range(len(enc_text) // 4):
        result += dword_mov_esi(i*4) + get(i)



    return result


JMP_LEN = 5
def make_new_string(old_off, new_off, string, file_object, OLD_BASE_ADDR, NEW_BASE_ADDR, NEW_OFFSET, all_data):
    
    new_str = load_str_by_stack(string)
    addr_from = new_off + NEW_BASE_ADDR + len(new_str) + JMP_LEN 
    addr_to = old_off + OLD_BASE_ADDR + JMP_LEN + 1
    jmp = make_near_jmp(addr_from, addr_to)

    first_zero = all_data.find(b"\x00" , old_off)
    if first_zero != 0:
        file_object.write(old_off, b"\x90" * (first_zero - old_off + 1) )

    file_object.write(new_off + NEW_OFFSET, new_str)
    file_object.file_object.write(jmp)

    jmp2 = make_near_jmp(addr_to, new_off + NEW_BASE_ADDR+1)
    file_object.write(old_off, jmp2)

    return len(new_str) + JMP_LEN + 1


def find_all_stack_string(all_data):
    chars = [i for i in range(ord(" "), 127)]
    last = 0
    result = []
    while last != -1:
        last = all_data.find(b"\xc7\x06", last + 1)
        if last != -1:
            if (all_data[last+2] in chars) and (all_data[last+3] in chars) and (all_data[last+4] in chars):
                result.append(last)

    return result
        






    
