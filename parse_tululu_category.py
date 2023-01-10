import os
import json
import time
import logging
import pathlib
import argparse

from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.exceptions import HTTPError, ConnectionError

from tululu_download import (
    send_request,
    parse_book_page,
    download_file
)


def parse_many_genre_pages(genre_id, pages=4, start=1):

    current_page = start
    all_books = {}
    next_page = True
    while next_page:
        url_genre_page = f'/l{genre_id}/{current_page}/'
        url_genre_page = urljoin('https://tululu.org', url_genre_page)

        try:
            html_page = send_request(url_genre_page).text
        except HTTPError as err:
            logging.error(err)
            time.sleep(1)
            continue
        except ConnectionError as err:
            logging.error(err)
            time.sleep(10)
            continue

        all_books = {}
        soup = BeautifulSoup(html_page, 'lxml')
        book_urls = [book_href.get('href') for book_href in (soup.select('div.bookimage a'))]
        for book in book_urls:
            full_book_link = urljoin('https://tululu.org', book)

            try:
                parsed_book = parse_book_page(send_request(full_book_link).text)
            except HTTPError as err:
                logging.error(err)
                time.sleep(1)
                continue
            except ConnectionError as err:
                logging.error(err)
                time.sleep(10)
                continue

            if parsed_book:
                all_books.update(parsed_book)

        last_page = soup.select('a.npage')[-1].text
        if current_page == last_page:
            next_page = False
        if current_page - start + 1 == pages:
            next_page = False

        current_page += 1

    return all_books


def download_books_by_genre(
                            genre_id,
                            json_path=None,
                            skip_imgs=False,
                            skip_txt=False,
                            dest_folder='downloads',
                            pages=4,
                            start=1
                        ):

    books = parse_many_genre_pages(genre_id, pages=pages, start=start)

    os.makedirs(dest_folder, exist_ok=True)
    if json_path:
        os.makedirs(Path.cwd()/dest_folder/json_path, exist_ok=True)

    json_filename = f'{Path.cwd()/dest_folder/json_path/"parsed_books_data.json"}'
    with open(json_filename, 'w', encoding='utf_8') as file:
        json.dump(books, file, indent=4, ensure_ascii=False)

    for book in books.values():
        filename = book['file_name']
        image = book['image']
        image_filename = ''.join([filename, pathlib.Path(image).suffix])
        txt_file = book['file_url']
        if not skip_imgs:
            download_file(image, image_filename, folder=Path.cwd()/dest_folder/'images')
        if not skip_txt:
            download_file(txt_file, ''.join([filename, '.txt']), folder=Path.cwd()/dest_folder/'books')


if __name__ == '__main__':

    genre_id = 55  # Научная фантастика

    parser = argparse.ArgumentParser(
        prog='books downloader',
        description='Download books from tululu'
        )
    parser.add_argument("--start_page", help="start page", type=int, default=1)
    parser.add_argument("--end_page", help="end page", type=int, default=4)
    parser.add_argument("--json_path", help="path for json-file", type=str, default='')
    parser.add_argument("--skip_imgs", help="skip image-files", action='store_true')
    parser.add_argument("--skip_txt", help="skip txt-files", action='store_true')
    parser.add_argument("--dest_folder", help="folder for all downloads", type=str, default='downloads')

    args = parser.parse_args()

    start_page = args.start_page
    end_page = args.end_page
    if end_page < start_page:
        end_page = start_page
    pages = end_page - start_page + 1

    download_books_by_genre(
        genre_id,
        json_path=args.json_path,
        skip_imgs=args.skip_imgs,
        skip_txt=args.skip_txt,
        dest_folder=args.dest_folder,
        pages=pages,
        start=start_page
        )
