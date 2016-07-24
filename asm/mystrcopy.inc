GPS = 0x1707860
WIDTH = 0x17E74A0 + 0x14

macro strcopy source, size, block_size {
 
    common
    mov rax, rsi           ; сохраняем rsi в rax
    mov r11, rdi           ; сохраняем rdi - в нем будет адрес назначения для movs_
    mov rdi, rsi           ; в rsi - находится адрес того, куда нужно занести перевод , переносим в rdi - для того,чтобы оно стало назначением
    lea rsi, [source]      ; грузим в rsi адрес переведенной строки
    
    if size mod block_size = 0
        count = (size / block_size)      ; количество блоков копирования по block_size байт
    else
        count = (size / block_size) + 1
    end if
     
    mov rcx, qword count

    if block_size = 8
        rep movsq          ; копирование по 8 байт
    else if block_size = 4
        rep movsd          ; копирование по 4 байта
    else if block_size = 2
        rep movsw          ; копирование по 2 байта
    else
        rep movsb          ; копирование по 1 байту
    end if 

    mov rdi, r11           ; восстанавливаем rdi из r11
    mov rsi, rax           ; восстанавливаем rsi из rax

    ;Далее коррекция сдвига для центрирования текста
    mov eax, [qword WIDTH] ;получаем текущую ширину экрана
    add eax, 1
    sar eax, 1             ; теперь в eax - половина ширины экрана
    sub eax, size / 2      ; отнимаем половину ширины текста, чтобы получить центральное положение
    cdqe                   ; расширяем eax -> rax
    mov [qword GPS], rax   ; заносим результат в gps.xoffset 

}


