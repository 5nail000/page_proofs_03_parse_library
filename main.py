from pathlib import Path
import requests
import os

def download_txt_file(link, file_name = "", folder = 'books', index = False):
    response = requests.get(link)
    response.raise_for_status()
    
    os.makedirs(folder, exist_ok= True)
    if len(file_name) < 1:
        file_name = response.headers['Content-Disposition'].split('"')[1]
        if index: 
            file_name = '{:04d}_{}'.format(index, file_name)
        
    with open(Path.cwd()/folder/file_name, 'wb') as file:
        file.write(response.content)
        return True


url = 'https://tululu.org/txt.php?id=32168'

download_txt_file(url,index= 1)