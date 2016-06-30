#!/usr/bin/env bash

FASM=$(which fasm)

if [ $FASM == "" ]; then
   echo "Не найден Fasm!"
   exit
fi

if [ "$1" == "" ]; then
  echo "Необходимо указать исходящий файл"
  exit
fi

TMP_ASM='/tmp/str_resize_patch.asm'
LIBGRP=$(dirname $(readlink Dwarf_Fortress))/libgraphics.so
chtext=`nm -C "$LIBGRP" | grep ChangeAsm | awk '{print $1}'` #Адрес функции ChangeAsm
addst=`nm -C "$LIBGRP" | grep addst | awk '{print $1}'`      #Адрес функции graphics::addst

echo -e "use32

ChTextOffset = ${chtext}h - ${addst}h
AddstAddr = 946B740h

dec ecx
not ecx 

;В ecx - длина текста
;В ebp - указатель на начало текста

push eax
push edx
push ecx

mov eax, [AddstAddr]
add eax, ChTextOffset
push ebp ;Передаем адрес 0-го байта строки
call eax

add esp, 4 ;Восстанавливаем стек

pop ecx
pop edx
pop eax

;Возвращаемся назад
test ecx, ecx
retn" > $TMP_ASM

$FASM $TMP_ASM $1
rm $TMP_ASM


