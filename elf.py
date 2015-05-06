#!/usr/bin/python3.4

import struct
from io import BytesIO

class ELF_header():

    class ProgramHeader():
        """Класс-контейнер записей в программном заголовке"""
        class ProgramHeaderEntry():
            """Класс данных одной записи в программном заголовке"""
            
            """
            type   - говорит о том, как нужно интерпретировать информацию этого массива
            offset - сдвиг от начала файла
            vaddr  - адрес первого байта в виртуальной памяти
            paddr  - *не используется в System V*
            filesz - длина данных в файле
            memsz  - длина области памяти, выделяемая объекту
            flags  - флаги, относящиеся к сегменту
            align  - выравнивание данных
            """

            

            def __init__(self,header_entry):
                self.template = struct.Struct("IIIIIIII")                        
                self.type, self.offset, self.vaddr, self.paddr,\
                self.filesz, self.memsz, self.flags, self.align = self.template.unpack(header_entry)

            def __str__(self):
                _type = {0: "NULL", 1:"LOAD", 2: "DYNAMIC", 3:"INTERP", 4:"NOTE",
                         5: "SHLIB", 6:"PHDR", 0x6474e550: "GNU_EH_FRAME", 0x6474E551:"GNU_STACK"}
                                      
                template = '{:<12}'.format(_type[self.type]) + " 0x%(offset)08X 0x%(vaddr)08X "+\
                           "0x%(filesz)08X 0x%(memsz)08X %(flags)2i  %(align)4i"
                
                return template % self.__dict__

            def make_new_entry(self, offset = None, vaddr = None, filesz = None, memsz = None):
                if offset == None:
                    offset = self.offset
                if vaddr == None:
                    vaddr = self.vaddr
                if filesz == None:
                    filesz = self.filesz
                if memsz == None:
                    memsz = self.memsz
                    
                return self.template.pack(self.type, offset, vaddr, vaddr, filesz, memsz, self.flags, self.align)
                
            
            """!!! ---- End class ProgramHeaderEntry --- !!!"""

        def __init__(self, header):
            #Загружаем программный заголовок
            template = struct.Struct(("%is" % header.e_phentsize) * header.e_phnum)
            phdrs = template.unpack(header.file_object.read(header.e_phoff, header.e_phentsize * header.e_phnum))
            self.entries = [self.ProgramHeaderEntry(entry) for entry in phdrs]

        def __getitem__(self, index):
            #Возвращает объект данных о записи
            if index >= len(self.entries):
                raise IndexError
            return self.entries[index]

        def __len__(self):
            return len(self.entries)

        def edit_block_size(self, index, offset_delta = None, filesz_delta = None, memsz_delta = None, vaddr_delta = None):
            new_offset = None
            new_filesz = None
            new_memsz  = None
            new_vaddr  = None
            if offset_delta != None:
                new_offset = self.entries[index].offset + offset_delta
            if filesz_delta != None:
                new_filesz = self.entries[index].filesz + filesz_delta
            if memsz_delta != None:
                new_memsz = self.entries[index].memsz + memsz_delta
            if vaddr_delta != None:
                new_vaddr = self.entries[index].vaddr + vaddr_delta
                
            new_hdr_entry = self.entries[index].make_new_entry(new_offset, new_vaddr, new_filesz, new_memsz)

            for entry in self.entries:
                if entry.offset > self.entries[index].offset + self.entries[index].filesz:
                    print(entry)


            print(self.ProgramHeaderEntry(new_hdr_entry))
            return new_hdr_entry
        """!!! ---- End class ProgramHeader --- !!!"""
            
    class SectionsHeader:

        class SectionHeaderEntry():
            """
            name      - индекс имени в секции с именами
            type      - тип секции
            flags     - флаги атрибутов секции
            addr      - виртуальный адрес
            offset    - смещение от начала файла
            size      - физический размер секции
            link      - содержит индекс в таблице секций
            info      - дополнительная информация о секции
            addralign - выравнивание данных
            entsize   - размер данных для секций с фиксированным размером
            """

            def __init__(self, section_entry):
                template = struct.Struct("I" * 10)

                self.name, self.type, self.flags, self.addr,\
                self.offset, self.size, self.link, self.info, \
                self.addralign, self.entsize = template.unpack(section_entry)

                self.text_name = ""

            def __str__(self):
                _type = {0:"NULL", 1:"PROGBITS", 2: "SYMTAB", 3:"STRTAB",
                         4:"RELA", 5:"HASH", 6:"DYNAMIC", 7:"NOTE",
                         8:"NOBITS", 9:"REL", 10:"SHLIB", 11:"DYNSYM",
                         0x6fffffff:"VERSYM", 0x6ffffffe:"VERNEED"}

                template = '{:<17} '.format(self.text_name) + \
                           '{:<12} '.format(_type[self.type]) + \
                           "0x%(addr)08X 0x%(offset)08X "+\
                           "0x%(size)08X %(flags)3i  %(addralign)4i"

                return template % self.__dict__

            def add_text_name(self, text_name):
                self.text_name = text_name
        """!!! ---- End class SectionHeaderEntry --- !!!"""

        def __init__(self, header):
            #Сохраняем указатель
            self.header = header
            #Загружаем данные из заголовка секций
            template = struct.Struct(("%is" % header.e_shentsize) * header.e_shnum)
            shdrs = template.unpack(header.file_object.read(header.e_shoff, header.e_shentsize * header.e_shnum))
            self.entries = [self.SectionHeaderEntry(entry) for entry in shdrs]

            #TODO: !Костыль! не знаю, как правильно узнать какая секция содержит имена всех остальных
            names = None
            for entry in self.entries:
                if entry.name == 1:
                    names = header.file_object.read(entry.offset, entry.size)
            
            if names != None:
                for entry in self.entries:
                   _name = names[entry.name : names.find(b"\x00", entry.name)]
                   entry.add_text_name(_name.decode())
            

        def __getitem__(self, index):
            #Возвращает объект данных о записи
            if index >= len(self.entries):
                raise IndexError
            return self.entries[index]

        def __len__(self):
            return len(self.entries)

        def get_section_data(self, index):
            return self.header.file_object.read(self.entries[index].offset, self.entries[index].size)

        """!!! ---- End class SectionHeader --- !!!"""

    
    """ 
    ei_mag      - magic ELF-файла, должен быть b"\x7fELF
    ei_class    - класс битности приложения 1 - 32bit, 2-64bit
    ei_data     - говорит о том, какой способ чтения данных используется 1 - littleendian 2 - bigendian
    ei_version  - 'версия' должна быть равна 1 (EV_CURRENT)
    e_type      - тип файла 1-relocable, 2-executable, 3-shared object, 4-core file
    e_machine   - необходимая для запуска архитектура
    e_version   - 'версия' должна быть равна 1 (EV_CURRENT)
    e_entry     - виртуальный адрес точки входа в программу
    e_phoff     - сдвиг в байтах на программный заголовок
    e_shoff     - сдвиг в байтах на заголовок секций
    e_flags     - флаги, специчные в зависимости от процессора
    e_ehsize    - содержит длину заголовка ELF в байтах
    e_phentsize - содержит длину в байтах одной записи в программном заголовке (все имеют одну длину)
    e_phnum     - содержит количество записей в программном заголовке
    e_shentsize - содержит длину одной записи в разделе секций
    e_shnum     - содержит количество секций
    e_shstrndx  - содержит номер секции, содержащую имена всех секций
    """
    
    ELFMAG = b"\x7fELF"

    E_IDENT     = 0x00
    E_TYPE      = 0x10

    
    def __init__(self, ELF_object):
        """Объект для доступа к данным из заголовка ELF"""
        self.file_object = ELF_object
        
        #Структура-идентификатор ELF-файла
        e_ident = struct.Struct("4sBBBB")
        #Загружаем идентификатор файла ELF
        self.ei_mag, self.ei_class, self.ei_data,\
        self.ei_version, self.ei_pad = e_ident.unpack(self.file_object.read(self.E_IDENT, e_ident.size))

        #Структура-заголовок ELF-файла
        Elf32_Ehdr = struct.Struct("HHIIIIIHHHHHH")
        #Загружаем данные заголовка файла ELF
        self.e_type, self.e_machine, self.e_version, self.e_entry,\
        self.e_phoff, self.e_shoff, self.e_flags, self.e_ehsize,\
        self.e_phentsize, self.e_phnum, self.e_shentsize, self.e_shnum,\
        self.e_shstrndx = Elf32_Ehdr.unpack(self.file_object.read(self.E_TYPE, Elf32_Ehdr.size))

        #Загружаем данные из программного заголовка
        self.prog_header = self.ProgramHeader(self)
        #Загружаем данные из заголовка секций
        self.section_header = self.SectionsHeader(self)

        

    def __str__(self):
        """Вывод информации о заголовке и секциях"""
        _ei_class  = {0:"None", 1:"32bit", 2:"64bit"}
        _ei_data   = {0:"None", 1:"little", 2:"big"}
        _e_type    = {1:"relocable", 2:"исполняемый", 3:"библиотека (so)", 4:"файл ядра"}
        _e_machine = {0:"No machine", 1:"AT&T WE 32100", 2:"SPARC", 3:"Intel 80386", 4:"Motorola 68000", 5:"Motorola 88000", 6:"?", 7:"Intel 80860", 8:"MIPS RS3000"}

        info = []
        info.append("Magic: " + str(self.ei_mag))
        info.append("Класс битности: " + _ei_class[self.ei_class])
        info.append("Формат данных: " + _ei_data[self.ei_data])
        info.append("Версия заголовка E_IDENT: " + str(self.ei_version))

        info.append("Тип файла: " + _e_type[self.e_type])
        info.append("Архитектура: " + _e_machine[self.e_machine])
        info.append("Версия заголовка ELF: " + str(self.e_version))
        info.append("Точка входа: 0x%08X" % self.e_entry)
        info.append("Сдвиг на программный заголовок: 0x%X" % self.e_phoff)
        info.append("Сдвиг на заголовок секций: 0x%X" % self.e_shoff)
        info.append("Флаги, зависимые от процессора: " + bin(self.e_flags).split('b')[1])
        
        info.append("Длина заголовка ELF: %i байт" % self.e_ehsize)
        info.append("Длина записи в программном заголовке: %i байт" % self.e_phentsize)
        info.append("Количество записей в программном заголовке %i" % self.e_phnum)
        
        info.append("Данные из программного заголовка:")
        info.append(" "*4 + "[Нм]     Тип       Cмещение  Вирт.адрес   Размер     Память   Флг Выравн")

        counter = 0
        for entry in self.prog_header:
            info.append(" "*4 + "[%02i] " % counter + str(entry))
            counter += 1
        info.append("")
        
        info.append("Длина записи в разделе секций: %i байт" % self.e_shentsize)
        info.append("Количество записей в разделе секций: %i байт" % self.e_shnum)
        info.append("Номер секции, содержащей: %i" % self.e_shstrndx)
        info.append("Данные из заголовка секций:")
        info.append("    [Нм]         Имя       Тип            Адрес     Смещение    Размер    Флг  Выравн")

        counter = 0
        for entry in self.section_header:
            info.append(" "*4 + "[%02i] " % counter + str(entry))
            counter += 1
       
        return "\n".join(info)

    
class ELF:

    uint32_t = struct.Struct("I")
    uint16_t = struct.Struct("H")

    def __init__(self, file_name):
        try:
            self.file_object = BytesIO()
            self.file_object.write(open(file_name, 'rb').read())
            
        except FileNotFoundError:
            print("Файл не найден")
        except:
            print("Ошибка открытия файла")
                                                                                             

    def read(self, pos, count):
        """Читает первые count байт с позиции pos"""
        self.file_object.seek(pos)
        return self.file_object.read(count)

    def write(self, pos, data):
        self.file_object.seek(pos)
        self.file_object.write(data)

    def read_uint32(self, pos):
        return ELF.uint32_t.unpack(self.read(pos,4))[0]

    def write_uint32(self, pos, data):
        self.write(pos, ELF.uint32_t.pack(data))

    def save(self, fn="Edited_DF"):
        self.file_object.seek(0)
        open(fn, 'wb').write(self.file_object.read())

"""
translate_ready = False

if translate_ready:
##    strings = ["аАбБвВгГдДеЕжЖзЗиИкКлЛмМнНоОпПрРсСтТуУфФхХ"]
##    encoded = [s.encode('cp1251') for s in strings]
##    binary = b"\x00".join(encoded)
##
##    section_size = 0x100000
##
##    binary = binary + b"\x00" * (section_size - len(binary))
##    open('empty.dat', 'wb').write(binary)



    
    import os
    #Созданный файл с новыми строками вставляется как новая секция
    os.system("objcopy ./Dwarf_Fortress ./Edited_DF  --add-section .rus=rus.dat")
    os.system("objcopy ./Edited_DF --set-section-flags .rus=A")
    os.system("objcopy ./Edited_DF --change-section-vma .rus=0x9cbd000")

    df = open("./Edited_DF", "r+b")

    #Создаётся запись для программного заголовка с указателями на новую секцию
    template = struct.Struct("IIIIIIII")
    h0 = template.pack(1, 4461*4096, 40125*4096,  40125*4096, 0x100000, 0x100000, 4, 4096)

    df.seek(52 + 32 * 7)
    df.write(h0)
    df.close()

    #if __name__ != "__main__":
    test = ELF("Edited_DF")


    #Ищем указатель на строку Skills remains (в режиме Приключений - создание героя)
    test.file_object.seek(0)
    all_data = test.file_object.read()
    addr = 0x09cbd000.to_bytes(4, byteorder="little")
    #pos = all_data.find(b"\x8c\x8c\x03\x09")
    pos = all_data.find(b'U\x8a\x03\t')
    test.write(pos, addr)

    test.save()
"""
