import os
import threading
from multiprocessing import Process, Queue
from queue import Queue as ThreadQueue
import time

# Функція для пошуку ключових слів у файлі
def search_keywords_in_file(file_path, keywords):
    results = {keyword: [] for keyword in keywords}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            for keyword in keywords:
                if keyword in content:
                    results[keyword].append(file_path)
    except Exception as e:
        print(f"Помилка при обробці файлу {file_path}: {e}")
    return results

# Об'єднання результатів пошуку
def merge_results(global_results, local_results):
    for keyword, files in local_results.items():
        global_results[keyword].extend(files)

# Версія з threading
def threaded_keyword_search(file_list, keywords):
    results = {keyword: [] for keyword in keywords}
    lock = threading.Lock()
    threads = []

    def worker(files_chunk):
        local_results = {keyword: [] for keyword in keywords}
        for file in files_chunk:
            file_results = search_keywords_in_file(file, keywords)
            merge_results(local_results, file_results)
        with lock:
            merge_results(results, local_results)

    # Розділення файлів на частини для кожного потоку
    num_threads = min(4, len(file_list))
    chunk_size = len(file_list) // num_threads
    for i in range(num_threads):
        start = i * chunk_size
        end = start + chunk_size if i != num_threads - 1 else len(file_list)
        thread = threading.Thread(target=worker, args=(file_list[start:end],))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results

# Версія з multiprocessing
def process_worker(file_list, keywords, result_queue):
    local_results = {keyword: [] for keyword in keywords}
    for file in file_list:
        file_results = search_keywords_in_file(file, keywords)
        merge_results(local_results, file_results)
    result_queue.put(local_results)

def multiprocessing_keyword_search(file_list, keywords):
    results = {keyword: [] for keyword in keywords}
    processes = []
    result_queue = Queue()

    # Розділення файлів на частини для кожного процесу
    num_processes = min(4, len(file_list))
    chunk_size = len(file_list) // num_processes
    for i in range(num_processes):
        start = i * chunk_size
        end = start + chunk_size if i != num_processes - 1 else len(file_list)
        process = Process(target=process_worker, args=(file_list[start:end], keywords, result_queue))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    # Збір результатів з черги
    while not result_queue.empty():
        local_results = result_queue.get()
        merge_results(results, local_results)

    return results

# Вимірювання часу виконання
def measure_execution_time(function, *args):
    start_time = time.time()
    result = function(*args)
    end_time = time.time()
    print(f"Час виконання {function.__name__}: {end_time - start_time:.2f} секунд")
    return result

# Тестування
if __name__ == "__main__":
    # Список файлів і ключових слів для пошуку
    file_list = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
    keywords = ["security", "error", "cyber", "cucumber"]

    # Перевірка наявності файлів
    for file in file_list:
        if not os.path.exists(file):
            print(f"Файл {file} не знайдено. Створіть тестові файли перед запуском програми.")
            exit(1)

    print("Багатопотоковий підхід:")
    threading_results = measure_execution_time(threaded_keyword_search, file_list, keywords)
    print("Результати:", threading_results)

    print("\nБагатопроцесорний підхід:")
    multiprocessing_results = measure_execution_time(multiprocessing_keyword_search, file_list, keywords)
    print("Результати:", multiprocessing_results)
