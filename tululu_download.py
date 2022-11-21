import argparse
import logging
import time
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
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
    comments = soup.find_all('div', {'class': 'texts'})
    book_comments = [item.find('span', {'class': 'black'}).text for item in comments]
    return book_comments


def send_request(url, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response, url)
    return response


def parse_book_page(book_id, content):

    book_title = content.find('div', {"id": "content"}).find('h1').next[:-8]
    book_author = content.find('div', {"id": "content"}).find('a').text

    book_image = content.find('div', {'class': 'bookimage'})
    book_image = book_image.find('img').get('src')
    book_image = urljoin(f'http://tululu.org/b{book_id}/', book_image)

    comments = content.find_all('div', {'class': 'texts'})
    book_comments = [item.find('span', {'class': 'black'}).text for item in comments]

    genres = content.find('span', {'class': 'd_book'}).find_all('a')
    book_genres = [genre.text for genre in genres]

    is_txt = True
    if isinstance(content.find('a', text='скачать txt'), type(None)):
        is_txt = False

    return {'id': book_id,
            'title': book_title,
            'author': book_author,
            'image': book_image,
            'comments': book_comments,
            'genre': book_genres,
            'is_txt': is_txt
            }


def check_for_redirect(response, url):
    if response.history:
        if response.history[0].status_code == 301:
            True
        if response.history[0].status_code == 302:
            raise HTTPError(f'Redirectrd url: {url}')
    True


def download_many_books(start_id=1, end_id=100000000):

    for book_id in range(start_id, end_id+1):

        try:
            url = f'https://tululu.org/b{book_id}/'
            response = send_request(url)
        except HTTPError as err:
            logging.error(err)
            time.sleep(1)
            continue
        except ConnectionError as err:
            logging.error(err)
            time.sleep(10)
            continue

        book = parse_book_page(book_id, BeautifulSoup(response.text, 'lxml'))

        if not book['is_txt']:
            continue

        book_title = sanitize_filename(book['title'])
        book_author = sanitize_filename(book['author'])
        book_filename = f'{book_title}({book_author}).txt'

        file_name = '{:04d} - {}'.format(book_id, book_filename)
        image_file = f'{file_name[:-4]}.jpg'

        params = {'id': book_id}
        book_file_url = 'https://tululu.org/txt.php'
        download_file(book_file_url, file_name=file_name, params=params)
        download_file(book['image'], file_name=image_file, folder='images')


if __name__ == '__main__':

    logging.basicConfig(level=logging.ERROR, filename="tululu_log.log", filemode="w", format="%(asctime)s %(message)s")

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
