use64

;FUNC_ADDR = 0x1707620

include 'mystrcopy.inc'

cmp rsi, r12                      ;Строки главного меню так передаются
jne @NO
	mov rax, [rsi]            ;Чтобы не обращаться много раз к памяти

	cmp rax, qword [dbHISTORY]
	je  @HISTOR
	
	cmp rax, qword [dbCONTINUE]
	je  @CONTINUE

	cmp rax, qword [dbSTART]
	je  @START

	cmp eax, dword [dbQUIT]
	je  @QUIT

	cmp rax, qword [dbCREATE]
	je  @CREATE

	cmp rax, qword [dbABOUT]
	je  @ABOUT

	cmp rax, qword [dbDESIGN]
	je  @DESIGN

	cmp rax, qword [dbOBJECT]
	je  @OBJECT

@NO:
jmp qword [qword FUNC_ADDR]       ;Переход к функции

@CONTINUE:
strcopy sCONTINUE, lCONTINUE, 8
jmp @NO

@START:
strcopy sSTART, lSTART, 8
jmp @NO

@QUIT:
strcopy sQUIT, lQUIT, 8
jmp @NO

@CREATE: 
strcopy sCREATE, lCREATE, 8
jmp @NO

@ABOUT:
strcopy sABOUT, lABOUT, 8
jmp @NO

@DESIGN:
strcopy sDESIGN, lDESIGN, 8
jmp @NO

@OBJECT:
strcopy sOBJECT, lOBJECT, 8
jmp @NO

@HISTOR:
strcopy sHISTOR, lHISTOR, 1
jmp @NO

;Переведенные слова в cp1251
;Продолжить Игру,0
sCONTINUE  db 207, 240, 238, 228, 238, 235, 230, 232, 242, 252, 32, 200, 227, 240, 243,0
lCONTINUE = $-sCONTINUE ; Длина строки без дополнительных нулей

;Начать Игру,0
sSTART     db 205, 224, 247, 224, 242, 252, 32, 200, 227, 240, 243,0
lSTART = $-sSTART

;Выход,0
sQUIT      db 194, 251, 245, 238, 228,0
lQUIT = $-sQUIT

;Создать Новый Мир!,0
sCREATE    db 209,238,231,228,224,242,252,32,205,238,226,251,233,32,204,232,240,33,0
lCREATE = $-sCREATE-1

;Об Игрe,0
sABOUT     db 206,225,32,200,227,240,229,0
lABOUT = $-sABOUT

;Создать Мир с Расширенными Параметрами,0
sDESIGN    db 209,238,231,228,224,242,252,32,204,232,240,32,241,32,208,224,241,248,232,240,229,237,237,251,236,232,32,207,224,240,224,236,229,242,240,224,236,232,0
lDESIGN = $-sDESIGN

;Арена Тестирования Объектов,0
sOBJECT    db 192,240,229,237,224,32,210,229,241,242,232,240,238,226,224,237,232,255,32,206,225,250,229,234,242,238,226,0
lOBJECT = $-sOBJECT

;    Истории о | пробелы в начале, чтобы перебить " of " | ноль на конце не ставится, т.к. оно будет соединяться с другими строками для вывода
sHISTOR    db 32,32,32,32,200, 241, 242, 238, 240, 232, 232, 32, 238
lHISTOR = $-sHISTOR

;Полные слова для поиска соответствия, но только по первым 8-ми байтам
dbCONTINUE db "Continue Playing",0
dbSTART    db "Start Playing",0
dbQUIT     db "Quit",0
dbCREATE   db "Create New World",0
dbABOUT    db "About DF",0
dbDESIGN   db "Design New World with Advanced Parameters",0
dbOBJECT   db "Object Testing Arena",0
dbHISTORY  db "Histories of",0

