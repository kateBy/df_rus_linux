GPS = 0x1707860
WIDTH = 0x17E74A0 + 0x14

macro strcopy source, size, full_size, block_size {
 
    common
    mov rax, rsi          ; сохраняем rsi в rax
    mov r11, rdi          ; сохраняем rdi - в нем будет адрес назначения для movsq
    mov rdi, rsi          ; в rsi - находится адрес того, куда нужно занести перевод , переносим в rdi - для того,чтобы оно стало назначением
    lea rsi, [source]     ; грузим в rsi адрес переведенной строки

    mov rcx, qword full_size / block_size

    if block_size eq 8
        rep movsq 
    end if
    
    if block_size eq 4
        rep movsd 
    end if
    
    if block_size eq 1
        rep movsb
    end if 

    mov rdi, r11           ; восстанавливаем rdi из r11
    mov rsi, rax           ; восстанавливаем rsi из rax

    ;Далее коррекция сдвига для центрирования текста
    mov eax, [dword WIDTH] ;получаем текущую ширину экрана
    sub eax, 1
    sar eax, 1             ;теперь в eax - половина ширины экрана
    sub eax, size / 2      ;отнимаем половину ширины текста, чтобы получить центральное положение
    cdqe                   ;расширяем eax -> rax
    mov [qword GPS], rax   ;заносим результат в gps.xoffset 

}

;Добавляем байты, чтобы длина строки была кратна нужному числу
macro make_align length, block {
    db (length / block + 1)*block - length  dup(0)
}
