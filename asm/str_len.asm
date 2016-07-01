use32

RU_OFFSET = 0x9f7a000 ;%_RU_OFFSET_% ;Смещение секции .rus
RU_SIZE   = 0x100000  ;%_RU_SIZE_%   ;Размер секции .rus
RU_END    = RU_OFFSET + RU_SIZE - 1

push    edi            ;Сохраняем edi

mov	edi, [esp+12]  ;Передаём указатель на первый байт строки

cmp     edi, RU_OFFSET ;Проверяем, находится ли строка в секции .rus
jb      NOT_RUS        ;Если сдвиг не в секции, то править длину не нужно
cmp     edi, RU_END    ;Проверяем, находится ли строка в секции .rus
ja      NOT_RUS
    
    mov edi, [edi-4]   ;Загружаем длину строки в edi
    mov [esp+16], edi  ;Передаем длину в стёк


NOT_RUS:

pop	edi            ;Восстанавливаем edi
