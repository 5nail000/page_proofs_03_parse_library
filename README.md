# Скрипт для выгрузки библиотеки tululu.org

Скрипт скачивает в папку **books** книги раздела жанра **Научной фантастики** электронной библиотеки **[tululu.org](https://tululu.org/)**, а так-же изображения их обложек в папку **images**.

Формат книг: txt-файлы

## Установка

Для запуска скриптов у вас уже должен быть установлен Python 3.

- Скачайте код
- Установите зависимости командой:
```
pip install -r requirements.txt
```

## Выгрузка книг по ID (файл tululu_download)

- Запустите скрипт командой: 
```
py tululu_download.py
```

# Опции

- **start_id** (условный порядковый номер, с которого необходимо начать выгрузку; по умолчанию 1)
- **end_id** (условный порядковый номер, по который необходимо продолжать выгрузку; по умолчанию 1)

пример запуска с определёными опциями(сохранятся книги со 2-й по 10-ую):
```
py tululu_download.py -start_id 2 -end_id 10
```


## Выгрузка всех книг в категории (файл parse_tululu_category)

- Запустите скрипт командой: 
```
py parse_tululu_category.py
```

# Опции

- **start_page** (номер страницы перечня, с которого необходимо начать выгрузку; по умолчанию 1)
- **end_page** (номер страницы перечня, по который необходимо продолжать выгрузку; по умолчанию 4)
- **dest_folder** (опция настройки папки в которой будет организованно сохранение всех загружаемых данных; по умолчанию 'downloads')
- **json_path** (опция настройки отдельной папки для json файла; по умолчанию - отсутствует)
- **skip_imgs** (опция для игнорирования изображений/обложек, отменяющая их загрузку)
- **skip_txt** (опция для игнорирования txt-файлов книг, отменяющая их загрузку)

Пример запуска с определёными опциями. Сохранятся все книги перечня со страниц 700-701, без обложек, json-файл будет сохранён в папке 'json':
```
python parse_tululu_category.py --start_page 700 --end_page 701 --json_path json --skip_imgs
```

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
