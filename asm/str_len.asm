use64

RU_OFFSET = 0x222b000 ;%_RU_OFFSET_% ;Смещение секции .rus
RU_SIZE   = 0x100000  ;%_RU_SIZE_%   ;Размер секции .rus
RU_END    = RU_OFFSET + RU_SIZE - 1

;esi - сдвиг на строку
;edx - длина строки

cmp     esi, RU_OFFSET ;Проверяем, находится ли строка в секции .rus
jb      NOT_RUS        ;Если сдвиг не в секции, то править длину не нужно
cmp     esi, RU_END    ;Проверяем, находится ли строка в секции .rus
ja      NOT_RUS
    
    mov dword edx, [esi-4]   ;Загружаем длину строки в edx

NOT_RUS:
nop
