use32

libAddstOff = _addst_   ;Число подставляется скриптом
libChtextOff = _chtext_ ;Число подставляется скриптом

ChTextOffset = libChtextOff - libAddstOff
AddstAddr = 946B740h

dec ecx
not ecx 

;В ecx - длина текста
;В edi - указатель на начало текста

push eax
push edx
push ecx

mov eax, [AddstAddr]
add eax, ChTextOffset
push ebp ;Передаем адрес 0-го байта строки
call eax

add esp, 4 ;Восстанавливаем стек

pop ecx
pop edx
pop eax

;Возвращаемся назад
test ecx, ecx
retn
