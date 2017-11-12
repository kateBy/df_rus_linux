use64

;Здесь перед вызовом функции

;RU_OFFSET = 0x222b000 ;Смещение секции .rus
;FUNC_ADDR - адрес функции к которой нужно сделать переход
;RU_SIZE   = 0x100000  ;Размер секции .rus
RU_END    = RU_OFFSET + RU_SIZE - 1

;esi - сдвиг на строку
;edx - длина строки

cmp     esi, RU_OFFSET ;Проверяем, находится ли строка в секции .rus
jb      NOT_RUS        ;Если сдвиг не в секции, то править длину не нужно
cmp     esi, RU_END    ;Проверяем, находится ли строка в секции .rus
ja      NOT_RUS

    xor rdx, rdx             ;Сбрасываем регистр с уже прописанной длиной
    mov dword edx, [esi-4]   ;Загружаем длину строки в edx

NOT_RUS:
jmp qword [qword FUNC_ADDR]       ;Переход к функции
