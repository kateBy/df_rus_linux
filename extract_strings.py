"""
Модуль содержит функции для извлечения строк из исполняемого файла
а так же поиска т.н. близнецов строк, т.к. GCC для строк, которые содержатся
в других строках использует одни и те же строки, только со смещением,
например:
The finest place,0 и place,0 будут совмещены в одно место, только при запросе
строки 'place' будет дана ссылка на [The finest place]+12 и т.д.
"""

import subprocess
from typing import List, Optional
from multiprocessing import Process, Queue, Pipe, Lock, cpu_count
import sys

chars = set(i for i in range(32, 127))
nums = b'1234567890'



def check_forbidden(byte_string: bytes) -> Optional[str]:
    """Проверяем найденую строку на нечитаемые символы"""
    if len(byte_string) < 2:
        return
        
    if byte_string[0] in nums:
        return
    for char in byte_string:
        if not (char in chars):
            return

            
    return byte_string.decode()



def find_gemini(words: dict, translated: dict) -> dict:
    """Поиск строк-близнецов постепенно отрезая от исходной строки буквы
    а после - сравнение со словарём переводов, если строка имеется в переводах,
    заносим ее в список"""
    result = {}
    for word in words:
        max_i = len(word) - 1
        i = 1

        while i < max_i:
            if word[i:] in translated:
                if not (word[i:] in words):
                    result[words[word] + i] = word[i:]

            i += 1

    return result


def check_founded_gemini(gemini: dict, buf: bytes) -> dict:
    """Проверяем, имеется ли в буфере ссылка с таким адресом"""

    buf_find = buf.find
    from_bytes = int.from_bytes
    to_bytes = int.to_bytes

    result = {}
    max_ind = len(gemini)
    ind = 0
    for g in gemini:
        ind += 1
        link_byte = buf_find(to_bytes(g, 4, byteorder="little"))
        if link_byte != -1:
            # if gemini[g] in result:
            #     print(gemini[g], "--->", hex(from_bytes(buf[link_byte:link_byte+4], 'little')), hex(g))
                      
            result[gemini[g]] = from_bytes(buf[link_byte:link_byte+4], 'little')
        if (ind % 100) == 0:
            print("%.2f" % (ind / max_ind * 100), "%")

    return result


def one_gemini_proc(gemini: dict, buf: bytes, pid: int, msg: Queue, pipe: Pipe, lock):
    buf_find = buf.find
    from_bytes = int.from_bytes
    to_bytes = int.to_bytes

    result = {}
    index = 0

    for g in gemini:
        index += 1
        link_byte = buf_find(to_bytes(g, 4, byteorder="little"))
        if link_byte != -1:
            result[gemini[g]] = from_bytes(buf[link_byte:link_byte + 4], 'little')
        if (index % 100) == 0:
            msg.put(100)  # Сообщаем главному процессу о том, что обработано 100 вариантов

    lock.acquire()  # В принципе не обязательно ставить lock, но не помешает
    try:
        msg.put(pid)  # Посылаем процессу-родителю сообщение о том, что поиск закончен
        pipe.send(result)  # Отдаём результаты поиска
    finally:
        lock.release()



def check_founded_gemini_multi(gemini: dict, buf: bytes) -> dict:
    msg = Queue()                                   # Объект для обмена сообщениями между потоками
    child_pipe, parent_pipe = Pipe()                # Объект для передачи результата работы потоков
    lock = Lock()
    # Количество ядер процессора нужно, потому что нет смысла запускать процессов больше, чем ядер
    cpus = cpu_count()

    print("Количество ядер процессора:", cpus)

    splitted_words = split_dictionary(gemini, cpus)  # Делим словарь для потоков

    for i in range(cpus):
        Process(target=one_gemini_proc, args=(splitted_words[i], buf, i, msg, child_pipe, lock,)).start()

    procs = cpus  # Будем отнимать отсюда оп 1 когда процесс сообщит, что закончил
    progress = 0
    max_progress = len(gemini)
    results = []
    msgs = [x for x in range(cpus)]
    while True:
        m = msg.get()
        if m in msgs:
            procs -= 1
            results.append(parent_pipe.recv())
        elif m == 100:
            progress += 100
            sys.stdout.write("%.2f" % (progress / max_progress * 100) + "% ")  # Вывод текущего прогресса
            sys.stdout.flush()

        if procs == 0:  # Если все процессы сообщили об окончании procs будет равно 0
            break

    res = {}
    for d in results:
        res.update(d)

    return res

def shell(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


def extract_strings(fn: str) -> dict:
    """Извлекает все похожее на строки из секции .rodata"""
    rodata = shell("objdump -x '%s' | grep \.rodata | awk '{print $3,$4,$6}'" % fn)
    rodata_size, rodata_vaddr, rodata_offset = [int(x, 16) for x in rodata.split(" ")]  # type: int, int, int

    _file = open(fn, "rb")
    _file.seek(rodata_offset)
    rodata = _file.read(rodata_size)
    _file.close()
    
    index = 0
    words = {}
    
    while index < rodata_size:
        if rodata[index] in chars:
            next_zero = rodata.find(0, index)
            if next_zero != -1:
                checked = check_forbidden(rodata[index:next_zero])
                if checked is not None:
                    words[checked] = index + rodata_vaddr
                index = next_zero
            
        index += 1
    return words



def load_trans_po(fn) -> dict:
    """Загрузка перевода из файла .po с помощью библиотеки polib"""
    import polib
    result = {}
    pofile = polib.pofile(fn)
    for i in pofile:
        if i.msgid.endswith(' '):      # Англ. кончается на пробел
            angl_spaces = len(i.msgid) - len(i.msgid.rstrip())
            ru_spaces = len(i.msgstr) - len(i.msgstr.rstrip())
            if angl_spaces != ru_spaces:
                result[i.msgid] = i.msgstr.rstrip() + ' ' * angl_spaces
            else:
                result[i.msgid] = i.msgstr
        else:      
            result[i.msgid] = i.msgstr

    return result



def make_dat_file(fn: str, trans: dict, size=0x100000) -> dict:
    """Создаёт секцию с новыми строками и возвращает словарь,
    содержащий английскую версию строки и индекс ее в новой секции.
    Перед строкой стоит 4 байта длины этой строки для использования в функции
    Строки разделяются между собой одинарным нулём"""

    from io import BytesIO
    result = {}
    offset = 0
    file = BytesIO()
    file.write(b"\x00" * size)
    file.seek(0)

    trans["'s"] = " "  # Пустая строка притяжательного падежа

    for i in trans:
        result[i] = offset + 4  # Перед строкой идет 4 байта ее длины
        encoded = trans[i].encode('cp1251') + b"\x00"
        ru_len = len(encoded)
        file.write((ru_len-1).to_bytes(4, 'little'))  # Записываем длину строки
        file.write(encoded)
        offset += ru_len + 4

    # Особый патч строки "Готовить"
    result["__COOK__"] = offset + 4
    cook = "Готовить".encode('cp1251') + b"\x00"
    file.write((len(cook)-1).to_bytes(4, 'little'))
    file.write(cook)
    offset += len(cook) + 4
    
    open(fn, 'wb').write(file.getvalue())

    result["CURSOR"] = offset

    return result



def split_dictionary(some_dict, out_count) -> List[dict]:
    """Разбивает словарь на несколько словарей, нужно для запуска нескольких потоков замены индексов"""

    result = [{} for _ in range(out_count)]
    cursor = 0

    for i in some_dict:
        result[cursor][i] = some_dict[i]
        cursor += 1
        if cursor == out_count:
            cursor = 0

    return result


