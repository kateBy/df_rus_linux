macro strcopy source,size,block_size {
 
   common
    mov rax, rsi          ; сохраняем rsi в rax
    mov r11, rdi          ; сохраняем rdi - в нем будет адрес назначения для movsq
    mov rdi, rsi          ; в rsi - находится адрес того, куда нужно занести перевод , переносим в rdi - для того,чтобы оно стало назначением
    lea rsi, [source]     ; грузим в rsi адрес переведенной строки

    mov rcx, qword size / block_size

    if block_size eq 8
        rep movsq 
    end if
    
    if block_size eq 4
        rep movsd 
    end if
    
    if block_size eq 1
        rep movsb
    end if 

    mov rdi, r11          ; восстанавливаем rdi из r11
    mov rsi, rax           ; восстанавливаем rsi из rax

}
