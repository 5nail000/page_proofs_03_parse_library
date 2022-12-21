import os
import json
import pathlib
import argparse

from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathvalidate import sanitize_filename

from tululu_download import (
    send_request,
    parse_comments,
    download_file
)


def get_genre_page(genre_id, page):
    host = 'https://tululu.org'
    url_genre_page = f'/l{genre_id}/{page}/'
    url_genre_page = urljoin(host, url_genre_page)

    return send_request(url_genre_page)


def parse_book_file_url(html_page):
    soup = BeautifulSoup(html_page, 'lxml')
    results = soup.select('a')
    for res in results:
        if 'скачать txt' in res:
            file_url = res.get('href')
            return file_url

    return


def parse_genre_page(html_page):

    soup = BeautifulSoup(html_page, 'lxml')
    results = soup.select('#content table')
    last_page = soup.select('a.npage')[-1].text
    books_all = {}
    for item in results:
        book_title = item.find_all('td')[1].text
        book_author = item.find_all('td')[2].find('a').text
        parse_genres = item.find_all('td')[3].find_all('a')
        book_genre = []
        for genre in parse_genres:
            book_genre.append(genre.text)
        book_url = f"https://tululu.org{item.find('a').get('href')}"
        book_id = book_url[20:-1]
        book_filename = f'{book_id}_{sanitize_filename(book_title)}({sanitize_filename(book_author)})'
        book_image = f"https://tululu.org{item.find('div', {'class': 'bookimage'}).find('img').get('src')}"
        book_html_page = send_request(book_url).text
        book_comments = parse_comments(book_html_page)

        book_file_url = parse_book_file_url(book_html_page)
        if not book_file_url:
            continue
        book_file_url = urljoin('https://tululu.org', book_file_url)

        books_all.update({book_id: {'url': book_url,
                                    'title': book_title,
                                    'author': book_author,
                                    'file_name': book_filename,
                                    'file_url': book_file_url,
                                    'image': book_image,
                                    'comments': book_comments,
                                    'genre': book_genre}})
    return books_all, last_page


def parse_many_genre_pages(genre_id, pages=4, start=1):

    current_page = start
    if start < 1:
        start = 1
        current_page = 1

    all_books = {}
    next_page = True
    while next_page:
        url_genre_page = f'/l{genre_id}/{current_page}/'
        url_genre_page = urljoin('https://tululu.org', url_genre_page)
        html_page = send_request(url_genre_page).text
        books, last_page = parse_genre_page(html_page)
        all_books.update(books)

        if current_page - start + 1 == pages:
            next_page = False
        if current_page == last_page:
            next_page = False

        current_page += 1

    return all_books


def download_books_by_genre(
                            genre_id,
                            json_path='',
                            skip_imgs=False,
                            skip_txt=False,
                            dest_folder='downloads',
                            pages=4,
                            start=1
                        ):

    books = parse_many_genre_pages(genre_id, pages=pages, start=start)

    if dest_folder != "":
        os.makedirs(dest_folder, exist_ok=True)
    if json_path != "":
        os.makedirs(Path.cwd()/dest_folder/json_path, exist_ok=True)

    json_file = f'{Path.cwd()/dest_folder/json_path/"parsed_books_data.json"}'
    with open(json_file, 'w', encoding='utf_8') as file:
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
