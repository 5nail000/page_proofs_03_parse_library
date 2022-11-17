import argparse
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError


def download_file(link, file_name, folder='books', params=None):
    response = send_request(link, params=params)
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
    check_for_redirect(response)
    return response


def parse_book_page(url):
    try:
        response = send_request(url)
    except HTTPError:
        return {'is_redirected': True}

    soup = BeautifulSoup(response.text, 'lxml')

    book_url = url
    book_id = book_url[20:-1]
    book_title = soup.find('div', {"id": "content"}).find('h1').next[:-8]
    book_author = soup.find('div', {"id": "content"}).find('a').text

    book_image = soup.find('div', {'class': 'bookimage'})
    book_image = book_image.find('img').get('src')
    book_image = f"https://tululu.org{book_image}"

    comments = soup.find_all('div', {'class': 'texts'})
    book_comments = [item.find('span', {'class': 'black'}).text for item in comments]

    parse_genres = soup.find('span', {'class': 'd_book'}).find_all('a')
    book_genre = [genre.text for genre in parse_genres]

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
            'is_txt': is_txt,
            'is_redirected': False
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
        if book['is_redirected']:
            continue
        sanitize_book_title = sanitize_filename(book['title'])
        sanitize_book_author = sanitize_filename(book['author'])
        book_filename = f'{sanitize_book_title}({sanitize_book_author}).txt'

        file_name = '{:04d} - {}'.format(id, book_filename)
        image_file = f'{file_name[:-4]}.jpg'

        if (book['is_txt']):
            params = {'id': id}
            book_file_url = 'https://tululu.org/txt.php'
            download_file(book_file_url, file_name=file_name, params=params)
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
