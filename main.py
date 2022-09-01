import requests
from bs4 import BeautifulSoup
import re
import os
from colors_translate import translate
import json

images_count = {}
links_in_dataset = []
parsed_images = 0
fails = 0


def get_color(html):
    lines = html.split('\n')
    for line in lines:
        if re.search(r'payload', line):
            payload = line.strip()[:-1][9:]
            break
    payload_json = json.loads(payload)
    return translate[list(payload_json['product']['colors'].values())[0]]


def get_image(product_soup):
    image_link = product_soup.find('img').get('src')
    image_link = image_link.replace('600x866', '236x341')
    responce = requests.get('http:' + image_link)
    return responce.content


def save_product(category, color, image):
    folder_name = f'{color}_{category}'
    if not os.path.exists(f'dataset/{folder_name}'):
        os.mkdir(f'dataset/{folder_name}')
        images_count[folder_name] = 0
    images_count[folder_name] += 1
    with open(f'dataset/{folder_name}/{images_count[folder_name]}.jpg', 'wb') as file:
        file.write(image)


def parse_from_endpoint(category, url, endpoint, limit):
    global parsed_images
    global fails
    while limit > 0:
        responce = requests.get(url + endpoint)
        soup = BeautifulSoup(responce.text, 'html.parser')
        products = soup.find_all('div', class_='x-product-card__card')
        if not products:
            break
        for product in products:
            link = product.find('a').get('href')
            if link in links_in_dataset:
                print(f'Продукт {url + link} уже загружен')
                continue
            print(f'Парсим продукт: {url + link}')
            product_responce = requests.get(url + link)
            product_soup = BeautifulSoup(product_responce.text, 'html.parser')
            try:
                color = get_color(product_responce.text)
            except KeyError:
                fails += 1
                continue
            image = get_image(product_soup)
            save_product(category, color, image)
            with open('dataset.txt', 'a') as file:
                file.write(f'{link}\n')
            limit -= 1
            parsed_images += 1
            print(f'Картинок загружено: {parsed_images}')
            if limit <= 0:
                break
        if '?page' in endpoint:
            page_number = int(endpoint[-1])
            page_number += 1
            endpoint = endpoint[:-1] + str(page_number)
        else:
            endpoint = endpoint + '?page=2'


def start():
    category = ''
    url = 'https://www.lamoda.ru'
    if not os.path.exists('dataset'):
        os.mkdir('dataset')
    else:
        print('Инициализирую уже загруженные продукты...')
        with open('dataset.txt') as file:
            text = file.read()
            global links_in_dataset
            links_in_dataset = text.split('\n')
        dataset_folders = os.listdir('dataset')
        for folder in dataset_folders:
            files = os.listdir(f'dataset/{folder}')
            images_count[folder] = len(files)
    print('Введите лимит продуктов по каждой из ссылок:')
    limit = int(input())
    with open('endpoints.txt') as file:
        for string in file:
            if string[0] != '/':
                category = string.strip()
            else:
                print(f'Запущен парсинг по: {url+string.strip()}')
                parse_from_endpoint(category, url, string.strip(), limit)
    print(f'Парсинг завершен\nКартинок загружено: {parsed_images}\nФейлы: {fails}')


if __name__ == '__main__':
    start()
