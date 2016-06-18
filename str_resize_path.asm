use32

BACK_ADDR = 8778C8Ch
FUNC_ADDR = 9FF2FD3h
CHANGE_PROC = 0h

org FUNC_ADDR
dec ecx
not ecx 
;В ecx - длина текста
;В edi - указатель на начало текста

nop
nop
nop
nop

;Возвращаемся назад
test ecx, ecx
retn
;jmp near (BACK_ADDR+5)
