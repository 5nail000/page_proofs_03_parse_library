import argparse
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import replace_symbol, sanitize_filename
from requests.exceptions import HTTPError, Timeout


def download_file(link, file_name, folder='books'):
    read_again = True
    while read_again:
        try:
            response = requests.get(link)
            response.raise_for_status()
        except ConnectionError and HTTPError and Timeout:
            time.sleep(2)
        else:
            read_again = False

    try:
        check_for_redirect(response)
    except HTTPError:
        True
    else:
        os.makedirs(folder, exist_ok=True)
        with open(Path.cwd()/folder/file_name, 'wb') as file:
            file.write(response.content)
            return True


def parse_comments(url):

    read_again = True
    while read_again:
        try:
            response = requests.get(url)
            response.raise_for_status()
        except ConnectionError and HTTPError and Timeout:
            time.sleep(2)
        else:
            read_again = False

    soup = BeautifulSoup(response.text, 'lxml')
    results = soup.find_all('div', {'class': 'texts'})

    comments = []
    for item in results:
        comment = item.find('span', {'class': 'black'}).text
        comments.append(comment)

    return comments


def parse_book_page(url):

    read_again = True
    while read_again:
        try:
            response = requests.get(url)
            response.raise_for_status()
        except ConnectionError and HTTPError and Timeout:
            time.sleep(2)
        else:
            read_again = False

    soup = BeautifulSoup(response.text, 'lxml')

    book_url = url
    book_id = book_url[20:-1]
    book_title = replace_symbol(
        soup.find('div', {"id": "content"}).find('h1').next)[:-2]
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

    return {'id': book_id,
            'url': book_url,
            'title': book_title,
            'author': book_author,
            'image': book_image,
            'comments': book_comments,
            'genre': book_genre}


def parse_page(url):

    read_again = True
    while read_again:
        try:
            response = requests.get(url)
            response.raise_for_status()
        except ConnectionError and HTTPError and Timeout:
            time.sleep(2)
        else:
            read_again = False

    soup = BeautifulSoup(response.text, 'lxml')
    results = soup.find('div', {"id": "content"}).find_all('table')
    last_page = soup.find_all('a', {"class": "npage"})[-1].text

    books_all = {'last_page': int(last_page)}
    for item in results:
        book_title = item.find_all('td')[1].text
        book_author = item.find_all('td')[2].find('a').text

        parse_genres = item.find_all('td')[3].find_all('a')
        book_genre = []
        for genre in parse_genres:
            book_genre.append(genre.text)

        book_url = f"https://tululu.org{item.find('a').get('href')}"
        book_id = book_url[20:-1]
        sanitize_book_title = sanitize_filename(book_title)
        sanitize_book_author = sanitize_filename(book_author)
        book_filename = f'{sanitize_book_title}({sanitize_book_author}).txt'

        book_image = item.find('div', {'class': 'bookimage'})
        book_image = book_image.find('img').get('src')
        book_image = f"https://tululu.org{book_image}"

        book_comments = parse_comments(book_url)
        books_all.update({book_id: {'url': book_url,
                                    'title': book_title,
                                    'author': book_author,
                                    'book_filename': book_filename,
                                    'image': book_image,
                                    'comments': book_comments,
                                    'genre': book_genre}})

    return books_all


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def mass_download_books(start_id=1, end_id=100000000):

    if start_id < 1:
        start_id = 1
    if end_id < start_id:
        end_id = start_id

    index = 0
    for page in range(100000000):

        current_page = 1 + page
        url = f'https://tululu.org/l55/{current_page}/'
        books = parse_page(url)
        if index >= end_id:
            break
        if current_page >= books['last_page']:
            break
        books.pop('last_page')

        for book in books:
            index += 1
            if index < start_id:
                continue

            book_file_url = f'https://tululu.org/txt.php?id={book}'

            file_name = '{:04d}_{}'.format(index, books[book]['book_filename'])
            print(file_name)

            download_file(book_file_url, file_name=file_name)
            file_name = f'{file_name[:-4]}.jpg'
            download_file(books[book]['image'],
                          file_name=file_name, folder='images')

            parse_comments(f'https://tululu.org/b{book}/')

            if index >= end_id:
                break

    return True


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='books downloader',
        description='Download books from tululu'
        )
    parser.add_argument("-start_id", help="start id", type=int, default=1)
    parser.add_argument("-end_id", help="end id", type=int, default=1)
    args = parser.parse_args()

    if (mass_download_books(args.start_id, args.end_id)):
        print('Job done')
