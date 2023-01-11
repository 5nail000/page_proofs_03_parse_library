import argparse
import logging
import requests
import pathlib
import time
import os

from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError, ConnectionError


def download_file(link, file_name, folder='books', params=None):

    try:
        response = send_request(link, params=params)
    except HTTPError as err:
        logging.error(err)
        time.sleep(1)
    except ConnectionError as err:
        logging.error(err)
        time.sleep(10)
    else:
        os.makedirs(folder, exist_ok=True)
        with open(Path.cwd()/folder/file_name, 'wb') as file:
            file.write(response.content)
            return True


def parse_comments(response_text):
    soup = BeautifulSoup(response_text, 'lxml')
    comments = soup.select('div.texts span.black')
    book_comments = [item.text for item in comments]
    return book_comments


def send_request(url, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response, url)
    return response


def parse_book_page(html_page):

    content = BeautifulSoup(html_page, 'lxml')

    book_url = f"https://tululu.org{content.select_one('div.bookimage a').get('href')}"
    book_id = int(book_url[20:-1])

    book_title = content.find('div', {"id": "content"}).find('h1').next[:-8]
    book_author = content.find('div', {"id": "content"}).find('a').text

    book_image = content.select_one('div.bookimage img').get('src')
    book_image = urljoin(f'https://tululu.org/b{book_id}/', book_image)

    comments = content.select('div.texts span.black')
    book_comments = [item.text for item in comments]

    genres = content.select('span.d_book a')
    book_genres = [genre.text for genre in genres]

    book_filename = f'{sanitize_filename(book_title)}({sanitize_filename(book_author)})'
    book_filename = '{:05d} - {}'.format(book_id, book_filename)

    book_file_url = False
    link_tags = content.select('a')
    for link in link_tags:
        if 'скачать txt' in link:
            book_file_url = urljoin('https://tululu.org', link.get('href'))

    if not book_file_url:
        return

    return {book_id: {'url': book_url,
                      'title': book_title,
                      'author': book_author,
                      'file_name': book_filename,
                      'file_url': book_file_url,
                      'image': book_image,
                      'comments': book_comments,
                      'genre': book_genres
                      }}


def check_for_redirect(response, url):
    if response.history:
        raise HTTPError(f'Redirectrd url: {url}')


def download_many_books(start_id=1, end_id=100000000):

    for book_id in range(start_id, end_id+1):

        try:
            url = f'https://tululu.org/b{book_id}/'
            unparsed_book = send_request(url)
        except HTTPError as err:
            logging.error(err)
            time.sleep(1)
            continue
        except ConnectionError as err:
            logging.error(err)
            time.sleep(10)
            continue

        parsed_book = parse_book_page(unparsed_book.text)

        if not parsed_book:
            continue

        filename = parsed_book[book_id]['file_name']
        txt_link = parsed_book[book_id]['file_url']
        txt_filename = f"{filename}.txt"
        image_link = parsed_book[book_id]['image']
        image_filename = ''.join([filename, pathlib.Path(image_link).suffix])

        download_file(txt_link, file_name=txt_filename, folder='books')
        download_file(image_link, file_name=image_filename, folder='images')


if __name__ == '__main__':

    logging.basicConfig(level=logging.ERROR,
                        filename="tululu_log.log",
                        filemode="w",
                        format="%(asctime)s - %(message)s",
                        datefmt='%Y.%m.%d  %H:%M:%S'
                        )

    parser = argparse.ArgumentParser(
        prog='books downloader',
        description='Download books from tululu'
        )
    parser.add_argument("-start_id", help="start id", type=int, default=1)
    parser.add_argument("-end_id", help="end id", type=int, default=1)
    args = parser.parse_args()

    if args.start_id < 1:
        start_id = 1
    else:
        start_id = args.start_id

    if args.end_id < start_id:
        end_id = start_id
    else:
        end_id = args.end_id

    download_many_books(start_id, end_id)
