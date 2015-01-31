from multiprocessing.pool import ThreadPool

def mt_map(func, iterable):
    thread_pool = ThreadPool()
    result      = thread_pool.map(func, iterable)
    thread_pool.close()
    thread_pool.join()
    return result
