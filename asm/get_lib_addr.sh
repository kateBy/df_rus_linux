#!/usr/bin/env bash

FASM=$(which fasm)

if [ "$FASM" != "" ]; then
   CMD=$FASM
else
   echo "Не найден Fasm!"
   exit
fi

if [ "$1" == "" ]; then
  echo "Необходимо указать исходящий файл"
  exit
fi

ASM_FILE='str_resize_path.asm'
LIBGRP=$(dirname $(readlink Dwarf_Fortress))/libgraphics.so
chtext=`nm -C "$LIBGRP" | grep ChangeAsm | awk '{print $1}'` #Адрес функции ChangeAsm
addst=`nm -C "$LIBGRP" | grep addst | awk '{print $1}'`      #Адрес функции graphics::addst

cp asm/$ASM_FILE /tmp/$ASM_FILE #Копия asm-файла

#Коррекция asm-файла адресами в библиотеке
sed -i -e 's/_addst_/'${addst}'h/g;s/_chtext_/'${chtext}'h/g' /tmp/$ASM_FILE

$CMD /tmp/$ASM_FILE "$1"
rm /tmp/$ASM_FILE


