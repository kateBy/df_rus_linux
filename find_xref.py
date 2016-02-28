"""Модуль предназначен для поиска ссылок на уже известные строки
Используется модуль multiprocessig для ускорения процесса, в зависимости
от количества ядер процессора"""

from multiprocessing import Process, Queue, Pipe, Lock, cpu_count
from extract_strings import *
import sys


def find_xrefs(words, procN, all_data, MAX_TO_FIND, msg, pipe, lock):
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
   
    _find = all_data.find    #Так должно быть быстрее
    index = 0
    for test_word in words:
        if index % 100 == 0:

            msg.put(100)    #Сообщаем главному процессу о том, что обработано 100 вариантов

        index += 1
        
        old_index = words[test_word]           #Получаем из списка смещение найденой строки
        bOldindex = old_index.to_bytes(4, byteorder="little") #Преобразуем смещение в байты
        all_poses = []
        pos = 0
        #И ищем совпадение 4-байтного смещения во всем файле, долго, но что поделать :)
        while pos != -1:
            pos = _find(bOldindex, pos+1, MAX_TO_FIND)
            if pos != -1:
                all_poses.append(pos)

        if all_poses != []:
            result[test_word] = all_poses

    lock.acquire()         #В принципе не обязательно ставить lock, но не помешает
    try:
        msg.put(procN)     #Посылаем процессу-родителю сообщение о том, что поиск закончен
        pipe.send(result)  #Отдаём результаты поиска
    finally:
        lock.release()



def find(words, MAX_TO_FIND, all_data, load_from_cache = False):
    """Основная функция поиска используемых смещений на строки.
       words - словарь найденых слов
       all_data - буфер для поиска
       load_from_cache - параметр, благодаря которому можно указать, нужно ли
       обновлять кэш или искать все заново (что даже на 4 ядрах где-то 2 минуты)"""

    SPLIT_SYMBOL = "<*|*>" #Просто символ, который вряд ли встретится среди строк

    #Если получили указание использовать кэш 
    if load_from_cache:
        try:
            cache = open('cache.txt', 'rt').readlines()
            res = {}
            for line in cache:
                word, data = line.split(SPLIT_SYMBOL)
                res[word] = [int(x) for x in data.strip().split("|") if x != ""]

            return res
        except FileNotFoundError:
            print("Отсутствует файл кэша! Необходимо запустить rebuild_cache.py")
            exit()
        except:
            print("Ошибка при парсинге файла-кэша")
            exit()
                
        

    msg = Queue()                                   #Объект для обмена сообщениями между потоками
    child_pipe, parent_pipe = Pipe()                #Объект для передачи результата работы потоков
    lock = Lock()
    #Количество ядер процессора нужно, потому что нет смысла запускать процессов больше, чем ядер
    cpus = cpu_count()                              

    print("Количество ядер процессора:", cpus)

    splitted_words = split_dictionary(words, cpus)  #Делим словарь для потоков


    #Запускаем процессы для поиска, передавая все необходимые данные
    for i in range(cpus):
        Process(target=find_xrefs, args=(splitted_words[i], i, all_data,
                                              MAX_TO_FIND, msg, child_pipe, lock,)).start()
    
    procs = cpus    #Будем отнимать отсюда оп 1 когда процесс сообщит, что закончил
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
            sys.stdout.write("%.2f" % (progress/max_progress*100) + "% ") #Вывод текущего прогресса
            sys.stdout.flush()


        if procs == 0: #Если все процессы сообщили об окончании procs будет равно 0
            break
        

    res = {}
    for d in results:
        res.update(d)


    #Байты, которые должны идти перед указателем на строку, все остальные, кроме mov esp - мусор
    good_bits = [
             0xb8, # mov eax, offset
             0xb9, # mov ecx, offset
             0xba, # mov edx, offset
             0xbb, # mov ebx, offset
             0xbd, # mov ebp, offset
             0xbe, # mov esi, offset
             0xbf, # mov edi, offset
             ]



    bug_addr = []
    for ref in res:
        bug_addr.clear()
        for xaddr in res[ref]:
            bit = all_data[xaddr-1]
            if not (bit in good_bits):              #Первый байт подозрителен
                if all_data[xaddr-4] != 0xc7:       #Проверяем может быть это mov dword ptr esp
                    if all_data[xaddr-3] != 0xc7:   #Проверяем может быть это mov  word ptr esp
                        bug_addr.append(xaddr)      #Скорее всего - ошибочный адрес, исключаем его

                        
        if bug_addr != []:                          #Если в результате поиска были найдены подозрительные адреса
            new_ref = []                            #Создадим новый список, в который включим только валидные адреса
            for i in res[ref]:
                if not (i in bug_addr):
                    new_ref.append(i)
            if new_ref != []:
                print("#BUG", bug_addr, ref)
                res[ref] = new_ref
            else:
                res[ref] = None
                print("!BUG", bug_addr, ref)

      
    
        


    #Записываем результаты на диск, для последующего использования
    sys.stdout.write("\n")
    sys.stdout.flush()
    print("Запись кэша на диск")
    
    cache_file = open('cache.txt', 'wt')
    for w in res:
        if res[w] == None:
            continue
        line = str(w) + SPLIT_SYMBOL + "|".join([str(x) for x in res[w]]) + "\n"
        cache_file.write(line)

    cache_file.close()
        
    return res








