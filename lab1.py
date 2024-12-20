import http.client
import threading
import time
import sys
import os
from urllib.parse import urlparse

def download_file(url, output_file):
    def make_request(parsed_url):
        connection_class = http.client.HTTPSConnection if parsed_url.scheme == "https" else http.client.HTTPConnection
        conn = connection_class(parsed_url.netloc)
        conn.request("GET", parsed_url.path)
        return conn.getresponse()

    parsed_url = urlparse(url)
    response = make_request(parsed_url)

    # Обработка редиректов (301, 302)
    if response.status in (301, 302):
        new_url = response.getheader("Location")
        if new_url:
            print(f"Редирект на {new_url}")
            parsed_url = urlparse(new_url)
            response = make_request(parsed_url)

    if response.status != 200:
        print(f"Ошибка загрузки файла: {response.status} {response.reason}")
        return

    total_downloaded = 0
    lock = threading.Lock()

    def download():
        nonlocal total_downloaded
        with open(output_file, "wb") as file:
            while chunk := response.read(1024):
                with lock:
                    total_downloaded += len(chunk)
                file.write(chunk)

    def show_progress():
        nonlocal total_downloaded
        while not download_complete.is_set():
            time.sleep(1)
            with lock:
                print(f"Загружено: {total_downloaded} байт")

    download_complete = threading.Event()

    download_thread = threading.Thread(target=download)
    progress_thread = threading.Thread(target=show_progress)

    download_thread.start()
    progress_thread.start()

    download_thread.join()
    download_complete.set()
    progress_thread.join()

    print(f"Загрузка завершена. Общий размер: {total_downloaded} байт")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Запуск: python lab1.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    parsed_url = urlparse(url)
    output_file = os.path.basename(parsed_url.path) or "downloaded_file"

    download_file(url, output_file)
