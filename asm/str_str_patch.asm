use64

;FUNC_ADDR = 0x1707620

CONTINUE = "Continue" ;Continue Playing
START    = "Start Pl" ;Start Playing
QUIT     = "Quit"     ;Quit
CREATE   = "Create N" ;Create New World
ABOUT    = "About DF" ;About DF
DESIGN   = "Design N" ;Design New World with Advanced Parameters
OBJECT   = "Object T" ;Object Testing Arena
HISTOR   = "Historie" ;Histories of 

cmp rsi, r12                  ;Строки главного меню так передаются
jne NO
	mov rax, [rsi]            ;Чтобы не обращаться много раз к памяти

	mov r13, HISTOR
	cmp r13, rax
	je _HISTOR
	
	mov r13, CONTINUE
	cmp r13, rax
	je  _CONTINUE

	mov r13, START
	cmp r13, rax
	je  _START

	mov r13d, QUIT
	cmp r13d, eax
	je  _QUIT

	mov r13, CREATE
	cmp r13, rax
	je  _CREATE

	mov r13, ABOUT
	cmp r13, rax
	je  _ABOUT

	mov r13, DESIGN
	cmp r13, rax
	je  _DESIGN

	mov r13, OBJECT
	cmp r13, rax
	je  _OBJECT

NO:
jmp qword [qword FUNC_ADDR]       ;Переход к функции

_CONTINUE:
CONTINUE_F0 = 0xe8e6ebeee4eef0cf ; Продолжи
CONTINUE_F1 = 0xf3f0e3c820fcf2   ; ть Игру
mov rax, CONTINUE_F0
mov qword [rsi], rax
mov rax, CONTINUE_F1
mov qword [rsi+8], rax
jmp NO

_START:
START_F0 = 0xc820fcf2e0f7e0cd ; Начать И
START_F1 = 0xf3f0e3           ; гру
mov rax, START_F0
mov qword [rsi], rax
mov rax, START_F1
mov qword [rsi+8], rax
jmp NO

_QUIT:
QUIT_F  =  0xe4eef5fbc2    ;Выход,0
mov rax, QUIT_F
mov qword [rsi], rax
jmp NO

_CREATE:
CREATE_F0 = 0x20fcf2e0e4e7eed1 ; Создать 
CREATE_F1 = 0xe8cc20e9fbe2eecd ; Новый Ми
CREATE_F2 = 0x21f0             ; р!
mov rax, CREATE_F0
mov qword [rsi], rax
mov rax, CREATE_F1
mov qword [rsi+8], rax
mov rax, CREATE_F2
mov qword [rsi+16], rax
jmp NO

_ABOUT:
ABOUT_F0 = 0xe5f0e3c820e1ce ; Об Игре
mov rax, ABOUT_F0
mov qword [rsi], rax
jmp NO

_DESIGN:
DESIGN_F0 = 0x20fcf2e0e4e7eed1; Создать 
DESIGN_F1 = 0xf1c820f120f0e8cc; Мир с Ис
DESIGN_F2 = 0xe0e2eee7fcebeeef; пользова
DESIGN_F3 = 0xf1e0d020ece5e8ed; нием Рас
DESIGN_F4 = 0xf5fbedede5f0e8f8; ширенных
DESIGN_F5 = 0xf2e5ece0f0e0cf20;  Парамет
DESIGN_F6 = 0xe2eef0          ; ров
mov rax, DESIGN_F0
mov qword [rsi], rax
mov rax, DESIGN_F1
mov qword [rsi+8], rax
mov rax, DESIGN_F2
mov qword [rsi+16], rax
mov rax, DESIGN_F3
mov qword [rsi+24], rax
mov rax, DESIGN_F4
mov qword [rsi+32], rax
mov rax, DESIGN_F5
mov qword [rsi+40], rax
mov rax, DESIGN_F6
mov qword [rsi+48], rax
jmp NO

_OBJECT:
OBJECT_F0 = 0xe5d220e0ede5f0c0; Арена Те
OBJECT_F1 = 0xede0e2eef0e8f2f1; стирован
OBJECT_F2 = 0xeae5fae1ce20ffe8; ия Объек
OBJECT_F3 = 0xe2eef2          ; тов
mov rax, OBJECT_F0
mov qword [rsi], rax
mov rax, OBJECT_F1
mov qword [rsi+8], rax
mov rax, OBJECT_F2
mov qword [rsi+16], rax
mov rax, OBJECT_F3
mov qword [rsi+24], rax
jmp NO

_HISTOR:
HISTOR_F0 = 0xf0eef2f1c8202020 ;    Истор
HISTOR_F1 = 0xee20e8e8 ; ии о
mov rax, HISTOR_F0
mov qword [rsi], rax
mov eax, HISTOR_F1
mov dword [rsi+8], eax
jmp NO

