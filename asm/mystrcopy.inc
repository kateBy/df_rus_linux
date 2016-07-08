macro strcopyq source,size
 { common
    mov rax, rsi          ; сохраняем rsi в rax
    push rdi              ; сохраняем rdi - в нем будет адрес назначения для movsq
    xor rcx, rcx          ; сбрасываем rcx - в cl - будет количество блоков по 8 байт
    mov cl, size / 8      ; заносим в cl количество 8-байтных блоков
    mov rdi, rsi          ; в rsi - находится адрес того, куда нужно занести перевод , переносим в rdi - для того,чтобы оно стало назначением
    lea rsi, [source]     ; грузим в rsi адрес переведенной строки
    rep movsq             ; копируем cl раз по 8 байт из [rsi] в [rdi]
    pop rdi               ; восстанавливаем rdi
    mov rsi,rax }         ; восстанавливаем rsi из rax

macro strcopyd source,size
 { common
    mov rax, rsi
    push rdi
    xor rcx, rcx
    mov cl, size / 4
    mov rdi, rsi
    lea rsi, [source]
    rep movsd
    pop rdi
    mov rsi,rax }

macro strcopyb source,size
 { common
    mov rax, rsi
    push rdi
    xor rcx, rcx
    mov cl, size
    mov rdi, rsi
    lea rsi, [source]
    rep movsb
    pop rdi
    mov rsi,rax }
