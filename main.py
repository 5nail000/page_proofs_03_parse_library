import os
from pathlib import Path
from requests.exceptions import HTTPError

import requests

from bs4 import BeautifulSoup


def download_txt_file(link, file_name = "", folder = 'books', index = False):
    response = requests.get(link)
    response.raise_for_status()
    try:
        check_for_redirect(response)
    except HTTPError: 
        True
    else:
        os.makedirs(folder, exist_ok= True)
        if len(file_name) < 1:
            file_name = response.headers['Content-Disposition'].split('"')[1]
            if index: 
                file_name = '{:04d}_{}'.format(index, file_name)
            
        with open(Path.cwd()/folder/file_name, 'wb') as file:
            file.write(response.content)
            print (" "*50, end='\r')
            print (' %s   \r' % file_name, end='\r')
            return True

def parse_page(url):
    response = requests.get(url)
    response.raise_for_status()
    
    with open('filename.html', "w", encoding='utf_8') as file:
        file.write(response.text)
    
    soup = BeautifulSoup (response.text, 'lxml')
    results = soup.find('div', {"id": "content"}).find_all('table')
    books_id = []
    for item in results:
        book_url = item.find('a').get("href")
        book_id = book_url[2:-1]
        #books.update({book_id : book_url})
        books_id.append(book_id)
    return books_id
    True

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
            download_txt_file(book_file_url, index= index)
            if index >= quantity: break

    print (" "*50, end='\r')
    print ('Job done')

if __name__ == '__main__':
    main()