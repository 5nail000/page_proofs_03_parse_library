from pathlib import Path
from pathvalidate import sanitize_filename, replace_symbol
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

import requests
import os


def download_txt_file(link, file_name, folder = 'books'):
    response = requests.get(link)
    response.raise_for_status()
    try:
        check_for_redirect(response)
    except HTTPError: 
        True
    else:
        os.makedirs(folder, exist_ok= True)

        with open(Path.cwd()/folder/file_name, 'wb') as file:
            file.write(response.content)
            print (" "*50, end='\r')
            print (' %s   \r' % file_name, end='\r')
            return True

def parse_comments(url):
    response = requests.get(url)
    response.raise_for_status()    
    soup = BeautifulSoup (response.text, 'lxml')   
    results = soup.find_all('div', {'class': 'texts'})
    comments = []
    for item in results:
        comment = item.find('span', {'class': 'black'}).text
        comments.append(comment)
    return comments


def parse_book_page(url):
    response = requests.get(url)
    response.raise_for_status()    
    soup = BeautifulSoup (response.text, 'lxml')

    book_url = url
    book_id = book_url[20:-1]
    book_title = replace_symbol(soup.find('div', {"id": "content"}).find('h1').next)[:-2]
    book_author = soup.find('div', {"id": "content"}).find('a').text

    book_image = f"https://tululu.org{soup.find('div', {'class': 'bookimage'}).find('img').get('src')}"
    
    book_comments = []
    comments = soup.find_all('div', {'class': 'texts'})
    for item in comments:
        comment = item.find('span', {'class': 'black'}).text
        book_comments.append(comment)
    
    parse_genres = soup.find('span', {'class': 'd_book'}).find_all('a')
    book_genre = []
    for genre in parse_genres:
        book_genre.append(genre.text)

    return {'id': book_id, 'url': book_url, 'title': book_title, 'author': book_author, 'image': book_image, 'comments': book_comments, 'genre': book_genre}
    True


def parse_page(url):
    response = requests.get(url)
    response.raise_for_status()    
    soup = BeautifulSoup (response.text, 'lxml')
    
    #with open('filename.html', "w", encoding='utf_8') as file: file.write(response.text)

    results = soup.find('div', {"id": "content"}).find_all('table')
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
        book_filename = f'{sanitize_filename(book_title)}({sanitize_filename(book_author)}).txt'
        book_image = f"https://tululu.org{item.find('div', {'class': 'bookimage'}).find('img').get('src')}"
        book_comments = parse_comments(book_url)
        books_all.update({book_id : {'url': book_url, 'title': book_title, 'author': book_author, 'book_filename': book_filename, 'image': book_image, 'comments': book_comments, 'genre': book_genre}})

    return books_all


def check_for_redirect(response):
    if response.history: 
        raise HTTPError

def main():
    index = 0
    quantity = 20

    for page in range(700):
        if index >= quantity: break
        url = f'https://tululu.org/l55/{page+ 1}/'
        books = parse_page(url)

        for book in books:
            index += 1
            book_file_url = f'https://tululu.org/txt.php?id={book}'
            file_name = '{:04d}_{}'.format(index, books[book]['book_filename'])
            download_txt_file(book_file_url, file_name= file_name)
            file_name = f'{file_name[:-4]}.jpg'
            download_txt_file(books[book]['image'], file_name= file_name, folder= 'images')
            parse_comments(f'https://tululu.org/b{book}/')
            if index >= quantity: break

    print (" "*50, end='\r')
    print ('Job done')

if __name__ == '__main__':
    
    main()