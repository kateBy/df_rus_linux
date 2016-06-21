#!/usr/bin/env bash

ASM_FILE='str_resize_path.asm'
LIBGRP=$(dirname $(readlink Dwarf_Fortress))/libgraphics.so
chtext=`nm -C $LIBGRP | grep ChangeAsm | awk '{print $1}'`h #Адрес функции ChangeAsm
addst=`nm -C $LIBGRP | grep addst | awk '{print $1}'`h      #Адрес функции graphics::addst
cp $ASM_FILE /tmp/$ASM_FILE #Копия asm-файла

#Коррекция asm-файла адресами в библиотеке
sed -i -e 's/_addst_/'${addst}'/g;s/_chtext_/'${chtext}'/g' /tmp/$ASM_FILE

fasm /tmp/$ASM_FILE /tmp/$(cut -d '.' -f 1 <<< $ASM_FILE).bin
rm /tmp/$ASM_FILE


