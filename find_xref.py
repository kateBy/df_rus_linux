#!/usr/bin/python3.4

from multiprocessing import Process, Queue, Pipe, Lock, cpu_count
from extract_strings import *
import sys




def find_xrefs(words, procN, all_data, MAX_TO_FIND, msg, pipe, lock):
    index = 0
    max_index = len(words)
    result = {}

    #Так должно быть быстрее
    _find = all_data.find
    
    for test_word in words:
        if index % 100 == 0:

            msg.put(100)

        index += 1
        
        old_index = words[test_word]
        bOldindex = old_index.to_bytes(4, byteorder="little")
        all_poses = []
        pos = 0
        #Ищем все совпадения индекса
        while pos != -1:
            pos = _find(bOldindex, pos+1, MAX_TO_FIND)
            if pos != -1:
                all_poses.append(pos)

        if all_poses != []:
            result[test_word] = all_poses

    lock.acquire()
    try:
        msg.put(procN)
        pipe.send(result)
    finally:
        lock.release()



def find(words, MAX_TO_FIND, all_data, load_from_cache = False):

    SPLIT_SYMBOL = "<*|*>"

    if load_from_cache:
        cache = open('cache.txt', 'rt').readlines()
        res = {}
        for line in cache:
            word, data = line.split(SPLIT_SYMBOL)
            res[word] = [int(x) for x in data.strip().split("|") if x != ""]

        return res
                
        

    msg = Queue()
    child_pipe, parent_pipe = Pipe()
    lock = Lock()
    cpus = cpu_count()
    print("Количество ядер процессора:", cpus)

    splitted_words = split_dictionary(words, cpus)


   
    for i in range(cpus):
        Process(target=find_xrefs, args=(splitted_words[i], i, all_data, MAX_TO_FIND, msg, child_pipe, lock,)).start()

    procs = cpus
    progress = 0
    max_progress = len(words)
    results = []
    msgs = [x for x in range(cpus)]
    while True:
        m = msg.get()
        if m in msgs:
            procs -= 1
            results.append(parent_pipe.recv())
            #print(m, "GET")
        elif m == 100:
            progress += 100
            sys.stdout.write("%.2f" % (progress/max_progress*100) + "% ")
            sys.stdout.flush()


        if procs == 0:
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

                        
        if bug_addr != []:
            new_ref = []
            for i in res[ref]:
                if not (i in bug_addr):
                    new_ref.append(i)
            if new_ref != []:
                print("#BUG", bug_addr, ref)
                res[ref] = new_ref
            else:
                res[ref] = None
                print("!BUG", bug_addr, ref)



    #res[ref] = [1,2,3]
        
    
        


    #Записываем результаты на диск, чтобы не мудохаться много раз
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








