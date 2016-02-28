"""Модуль содержит функции, обрабатывающие или создающие машинный код в
исполняемом файле Dwarf_Fortress"""


'''Создаёт последовательность байт, которые являются джампом с одного адреса на другой'''
def make_near_jmp(addr_from, addr_to):
    return b"\xe9" + (addr_to - addr_from).to_bytes(4, 'little', signed = True)




dword_mov_esi = lambda x: bytes([0xc7, 0x46, x])
dword_mov_eax = lambda x: bytes([0xc7, 0x40, x])

stack_opcodes = {"esi" : dword_mov_esi,
                 "eax" : dword_mov_eax}

'''Создаёт последовательность байт, аналогичную загрузке
строк в главном меню, в зависимости от типа регистра и
начального сдвига в стёке, выравнивает по 4'''
def load_str_by_stack(text, opcode_and_offset):
    opcode, start_offset = opcode_and_offset
        
    enc_text = text.encode("cp1251") + b"\x00"
    enc_text += b"\x00" * (4 - len(enc_text) % 4)

    get = lambda x: enc_text[x*4:x*4+4]

    dword_mov = stack_opcodes[opcode]

    result = b""
    for i in range(len(enc_text) // 4):
        result += dword_mov(start_offset + i*4) + get(i)

    return result


JMP_LEN = 5
'''Добавляет строку в новый сегмент данных, а так же код, необходимый для его загрузки'''
def make_new_string(old_off, new_off, string, file_object, OLD_BASE_ADDR, NEW_BASE_ADDR, NEW_OFFSET, all_data, opcode_and_offset):
    
    new_str = load_str_by_stack(string,opcode_and_offset)
    addr_from = new_off + NEW_BASE_ADDR + len(new_str) + JMP_LEN 
    addr_to = old_off + OLD_BASE_ADDR + JMP_LEN + 1
    jmp = make_near_jmp(addr_from, addr_to)

    first_zero = all_data.find(b"\x00" , old_off)
    if first_zero != -1:
        file_object.seek(old_off)
        file_object.write(b"\x90" * (first_zero - old_off + 1) )

    file_object.seek(new_off + NEW_OFFSET)
    file_object.write(new_str)
    #Записываем jmp сразу после загрузки строки в стёк
    file_object.write(jmp)

    jmp2 = make_near_jmp(addr_to, new_off + NEW_BASE_ADDR+1)
    file_object.seek(old_off)
    file_object.write(jmp2)

    return len(new_str) + JMP_LEN + 1

"""Поиск всех строк, которые загружаются через подготовленный стёк"""
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
        






    
