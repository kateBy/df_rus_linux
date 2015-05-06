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


    #Записываем результаты на диск, чтобы не мудохаться много раз
    sys.stdout.write("\n")
    sys.stdout.flush()
    print("Запись кэша на диск")
    
    cache_file = open('cache.txt', 'wt')
    for w in res:
        line = str(w) + SPLIT_SYMBOL + "|".join([str(x) for x in res[w]]) + "\n"
        cache_file.write(line)

    cache_file.close()
        
    return res








