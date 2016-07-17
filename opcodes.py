"""Модуль содержит функции, обрабатывающие или создающие машинный код в
исполняемом файле Dwarf_Fortress"""

_OP_JMP = b"\xe9"
_OP_CALL = b"\xe8"

'''Создаёт последовательность байт, которые являются джампом с одного адреса на другой'''
def make_near_jmp(addr_from, addr_to):
    return _OP_JMP  + (addr_to - addr_from).to_bytes(4, 'little', signed = True)

def make_call(addr_from, addr_to):
    return _OP_CALL + (addr_to - addr_from).to_bytes(4, 'little', signed = True)


        






    
