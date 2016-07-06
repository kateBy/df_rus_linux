macro strcopyq source,size
 { common
    push rsi
    push rdi
    xor rcx, rcx
    mov cl, size / 8
    mov rdi, rsi
    lea rsi, [source]
    rep movsq
    pop rdi
    pop rsi }

macro strcopyd source,size
 { common
    push rsi
    push rdi
    xor rcx, rcx
    mov cl, size / 4
    mov rdi, rsi
    lea rsi, [source]
    rep movsd
    pop rdi
    pop rsi }

macro strcopyb source,size
 { common
    push rsi
    push rdi
    xor rcx, rcx
    mov cl, size
    mov rdi, rsi
    lea rsi, [source]
    rep movsb
    pop rdi
    pop rsi }
