import argparse
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError, Timeout


def download_file(link, file_name, folder='books'):
    response = send_request(link)
    os.makedirs(folder, exist_ok=True)
    with open(Path.cwd()/folder/file_name, 'wb') as file:
        file.write(response.content)
        return True


def parse_comments(response_text):

    soup = BeautifulSoup(response_text, 'lxml')
    results = soup.find_all('div', {'class': 'texts'})

    comments = []
    for item in results:
        comment = item.find('span', {'class': 'black'}).text
        comments.append(comment)

    return comments


def send_request(url):
    read_again = True
    while read_again:
        try:
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)
        except ConnectionError and Timeout:
            time.sleep(2)
        except HTTPError:
            return
        else:
            read_again = False
    return response


def parse_book_page(url):

    response = send_request(url)
    if isinstance(response, type(None)):
        return
    soup = BeautifulSoup(response.text, 'lxml')

    book_url = url
    book_id = book_url[20:-1]
    book_title = soup.find('div', {"id": "content"}).find('h1').next[:-8]
    book_author = soup.find('div', {"id": "content"}).find('a').text

    book_image = soup.find('div', {'class': 'bookimage'})
    book_image = book_image.find('img').get('src')
    book_image = f"https://tululu.org{book_image}"

    book_comments = []
    comments = soup.find_all('div', {'class': 'texts'})
    for item in comments:
        comment = item.find('span', {'class': 'black'}).text
        book_comments.append(comment)

    parse_genres = soup.find('span', {'class': 'd_book'}).find_all('a')
    book_genre = []
    for genre in parse_genres:
        book_genre.append(genre.text)

    try:
        soup.find('a', {'href': f'/txt.php?id={book_id}'}).text
    except AttributeError:
        is_txt = False
    else:
        is_txt = True

    return {'id': book_id,
            'url': book_url,
            'title': book_title,
            'author': book_author,
            'image': book_image,
            'comments': book_comments,
            'genre': book_genre,
            'is_txt': is_txt
            }


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def mass_download_books(start_id=1, end_id=100000000):

    if start_id < 1:
        start_id = 1
    if end_id < start_id:
        end_id = start_id

    for id in range(start_id, end_id+1):

        url = f'https://tululu.org/b{id}/'
        book = parse_book_page(url)
        if isinstance(book, type(None)):
            continue

        book_file_url = f'https://tululu.org/txt.php?id={book["id"]}'

        sanitize_book_title = sanitize_filename(book['title'])
        sanitize_book_author = sanitize_filename(book['author'])
        book_filename = f'{sanitize_book_title}({sanitize_book_author}).txt'

        file_name = '{:04d} - {}'.format(id, book_filename)
        image_file = f'{file_name[:-4]}.jpg'

        if (book['is_txt']):
            print(file_name)
            download_file(book_file_url, file_name=file_name)
            download_file(book['image'], file_name=image_file, folder='images')
    print('Job done')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='books downloader',
        description='Download books from tululu'
        )
    parser.add_argument("-start_id", help="start id", type=int, default=1)
    parser.add_argument("-end_id", help="end id", type=int, default=1)
    args = parser.parse_args()

    mass_download_books(args.start_id, args.end_id)
