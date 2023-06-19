import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from queue import Queue
import threading
from tqdm import tqdm

# Set the maximum number of threads
MAX_THREADS = 10

# Set the maximum number of retries for failed requests
MAX_RETRIES = 3

# Set the starting URL and maximum recursion depth
start_url = "https://exitcode0.net"
MAX_DEPTH = 2

# Create a queue for storing URLs to be crawled
url_queue = Queue()

# Create a set to keep track of visited URLs
visited_urls = set()

# Create a lock for thread safety
lock = threading.Lock()

# Create a counter for successful and failed requests
success_count = 0
failure_count = 0

# Create a flag for indicating whether to pause or quit
pause_flag = threading.Event()

# Create a file for storing 404 links
file = open("404_links.txt", "w")
file.close()

def crawl_worker():
    while True:
        item = url_queue.get()
        if item is None:
            break

        url, depth, link_path = item

        try:
            response = requests.get(url, timeout=5)
            status_code = response.status_code
        except requests.exceptions.RequestException:
            status_code = None

        if status_code == 404:
            with lock:
                print(f"404 Not Found: {url}")
                with open("404_links.txt", "a") as file:
                    file.write(f"{url}\n")
                global failure_count
                failure_count += 1
        elif status_code is not None:
            with lock:
                global success_count
                success_count += 1
            if depth < MAX_DEPTH:
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        abs_url = urljoin(url, href)
                        parsed_abs_url = urlparse(abs_url)
                        parsed_start_url = urlparse(start_url)
                        if parsed_abs_url.netloc == parsed_start_url.netloc:  # Check if link is within the same domain
                            enqueue_url(abs_url, depth + 1, f"{link_path} - {link.text}")
        else:
            enqueue_url(url, depth, link_path)

        url_queue.task_done()

def enqueue_url(url, depth, link_path):
    with lock:
        if url not in visited_urls:
            visited_urls.add(url)
    url_queue.put((url, depth, link_path))

def input_thread_func():
    global pause_flag
    while True:
        command = input("Enter 'p' to pause or 'r' to resume: ")
        if command == 'p':
            pause_flag.set()
            print("Crawling paused.")
        elif command == 'r':
            pause_flag.clear()
            print("Crawling resumed.")
        else:
            print("Invalid command. Please try again.")

# Parse the start URL
start_url_parsed = urlparse(start_url)

# Start crawling from the starting URL with depth 0
enqueue_url(start_url, 0, "root link")
# Create and start the crawl worker threads
threads = []
for _ in range(MAX_THREADS):
    thread = threading.Thread(target=crawl_worker)
    thread.start()
    threads.append(thread)

# Create a progress bar
with tqdm(total=url_queue.qsize(), unit='URL') as pbar:
    # Start the input thread for pausing and resuming
    input_thread = threading.Thread(target=input_thread_func)
    input_thread.start()

    while not url_queue.empty():
        if not pause_flag.is_set():
            pbar.update(url_queue.qsize() - pbar.n)
            pbar.set_postfix({'Success': success_count, 'Failure': failure_count})
        threading.Event().wait(0.1)

# Wait for all URLs to be processed
url_queue.join()

# Stop the worker threads
for _ in range(MAX_THREADS):
    url_queue.put(None)
for thread in threads:
    thread.join()

# Stop the input thread
input_thread.join()

# Print the summary
print("\nCrawling completed!")
print(f"Successful requests: {success_count}")
print(f"Failed requests: {failure_count}")
