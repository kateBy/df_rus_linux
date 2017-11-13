"""Модуль предназначен для поиска ссылок на уже известные строки
Используется модуль multiprocessig для ускорения процесса, в зависимости
от количества ядер процессора"""

from multiprocessing import Process, Queue, Pipe, Lock, cpu_count
from extract_strings import *
import sys
import json

ESI = b'\xbe'
CACHE_FILE = 'cache.json'

def find_xrefs(words: dict, pid: int, all_data: bytes, _max_offset: int, msg: Queue, pipe: Pipe, lock):
    """Один из потоков поиска использования смещений на строки
    words - список найденых строк в файле
    procN - номер процесса
    all_data - массив байт в котором будем искать совпадения
    MAX_TO_FIND - это крайнее смещение, за которым искать уже не имеет смысла
    msg - объект Queue для общения между потоками и их родителем
    pipe - объект Pipe, через него будут переданы результаты поиска
    lock - объект для блокировки стандатного вывода
    """

    result = {}
   
    _find = all_data.find    # Так должно быть быстрее
    to_bytes = int.to_bytes
    index = 0
    for test_word in words:
        if index % 100 == 0:
            msg.put(100)    # Сообщаем главному процессу о том, что обработано 100 вариантов

        index += 1
        
        old_index = words[test_word]           # Получаем из списка смещение найденой строки
        boldindex = ESI + to_bytes(old_index, 4, byteorder="little")  # type: bytes  # Преобразуем смещение в байты
        all_poses = []
        pos = 0
        # И ищем совпадение 4-байтного смещения во всем файле, долго, но что поделать :)
        while pos != -1:
            pos = _find(boldindex, pos + 1, _max_offset)
            if pos != -1:
                all_poses.append(pos+1)

        if len(all_poses) > 0:
            result[test_word] = all_poses

    lock.acquire()         # В принципе не обязательно ставить lock, но не помешает
    try:
        msg.put(pid)     # Посылаем процессу-родителю сообщение о том, что поиск закончен
        pipe.send(result)  # Отдаём результаты поиска
    finally:
        lock.release()



def find(words: dict, max_offset: int, all_data: bytes, load_from_cache=False) -> dict:
    """Основная функция поиска используемых смещений на строки.
       words - словарь найденых слов
       all_data - буфер для поиска
       load_from_cache - параметр, благодаря которому можно указать, нужно ли
       обновлять кэш или искать все заново (что даже на 4 ядрах где-то 2 минуты)"""

    # Если получили указание использовать кэш
    if load_from_cache:
        try:
            cache = open(CACHE_FILE, 'rt').read()
            return json.loads(cache)
        except FileNotFoundError:
            print("Отсутствует файл кэша! Необходимо запустить rebuild_cache.py")
            exit()
        except json.JSONDecodeError:
            print("Ошибка при парсинге файла-кэша")
            exit()
                
        

    msg = Queue()                                   # Объект для обмена сообщениями между потоками
    child_pipe, parent_pipe = Pipe()                # Объект для передачи результата работы потоков
    lock = Lock()
    # Количество ядер процессора нужно, потому что нет смысла запускать процессов больше, чем ядер
    cpus = cpu_count()                              

    print("Количество ядер процессора:", cpus)

    splitted_words = split_dictionary(words, cpus)  # Делим словарь для потоков


    # Запускаем процессы для поиска, передавая все необходимые данные
    for i in range(cpus):
        Process(target=find_xrefs, args=(splitted_words[i], i, all_data,
                                         max_offset, msg, child_pipe, lock,)).start()
    
    procs = cpus    # Будем отнимать отсюда оп 1 когда процесс сообщит, что закончил
    progress = 0
    max_progress = len(words)
    results = []
    msgs = [x for x in range(cpus)]
    while True:
        m = msg.get()
        if m in msgs:
            procs -= 1
            results.append(parent_pipe.recv())
        elif m == 100:
            progress += 100
            sys.stdout.write("%.2f" % (progress/max_progress*100) + "% ")  # Вывод текущего прогресса
            sys.stdout.flush()


        if procs == 0:  # Если все процессы сообщили об окончании procs будет равно 0
            break
        

    res = {}
    for d in results:
        res.update(d)


    # Записываем результаты на диск, для последующего использования
    sys.stdout.write("\n")
    sys.stdout.flush()
    print("Запись кэша на диск")
    
    with open(CACHE_FILE, 'wt') as json_file:
        json_file.write(json.dumps(res, ensure_ascii=False, indent=4))
        json_file.close()
        
    return res
