import requests
from bs4 import BeautifulSoup
import time


#########################
# Припустимо, all_links вже зібрано на Етапі 1.
# Для тесту можна використовувати список з вашим посиланням:
# all_links = ["https://plasticsurgery.org.au/surgeon/associate-professor-thomas-lam/"]
#
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# }
####################


# Базовий URL для збору посилань
base_url = "https://plasticsurgery.org.au/about-asps/find-a-surgeon/?_location=-34.00244273042072%2C150.74296693718674%2C50%2C60+Central+Ave%2C+Oran+Park+NSW+2570%2C+Australia&_sort=geo_distance_asc&map=1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

all_links = []
page = 1

# ================= ЕТАП 1: ЗБІР ПОСИЛАНЬ =================
print("--- ЕТАП 1: Збір посилань на хірургів ---")
while True:
    url = base_url if page == 1 else f"{base_url}&_page={page}"
    print(f"Сканування сторінки пагінації {page}...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Сторінку {page} не знайдено. Зупинка збору посилань.")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('div', class_='wpgb-card-wrapper')

        if not cards:
            print("Контейнери 'wpgb-card-wrapper' більше не знайдені.")
            break

        page_links_count = 0
        for card in cards:
            links = card.find_all('a', class_='wpgb-card-layer-link', href=True)
            for link in links:
                href = link['href']
                if href.startswith('/'):
                    href = f"https://plasticsurgery.org.au{href}"

                if href not in all_links:
                    all_links.append(href)
                page_links_count += 1

        print(f"Знайдено посилань на сторінці {page}: {page_links_count}")

        if page_links_count == 0:
            print("Посилань більше немає. Переходимо до аналізу сторінок.")
            break

        page += 1
        time.sleep(1.5)

    except Exception as e:
        print(f"Помилка на етапі збору: {e}")
        break

print(f"\nВсього знайдено посилань для аналізу: {len(all_links)}\n")

# ================= ЕТАП 2: ПАРСИНГ СТОРІНОК ХІРУРГІВ =================
print("--- ЕТАП 2: Парсинг внутрішніх сторінок ---")
surgeons_data = []

for index, surgeon_url in enumerate(all_links, start=1):
    print(f"[{index}/{len(all_links)}] Обробка: {surgeon_url}")

    try:
        response = requests.get(surgeon_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Не вдалося завантажити сторінку (Status: {response.status_code})")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Ім'я хірурга
        title_tag = soup.find('h1', class_='single-surgeon__title')
        title = title_tag.text.strip() if title_tag else "Не знайдено"

        # Список для зберігання інформації про всі клініки (практики) цього хірурга
        practices_list = []

        # Шукаємо всі блоки локацій на сторінці (їх може бути 1, 2 або більше)
        location_cards = soup.find_all('div', class_='single-surgeon__location-card')
        # print(location_cards)

        for card in location_cards:
            # 1. Шукаємо адресу всередині цієї картки
            address_tag = card.find('div', class_='single-surgeon__meta-text')
            # print(address_tag)
            address = address_tag.get_text(separator=" ", strip=True) if address_tag else "Не знайдено"

            phone = "Не знайдено"
            fax = "Не знайдено"

            # 2. Шукаємо всі елементи з мета-даними (телефон, факс тощо) всередині ЦІЄЇ картки
            meta_items = card.find_all('div', class_='single-surgeon__meta-text')
            for item in meta_items:
                label_tag = item.find('div', class_='single-surgeon__meta-label')
                value_tag = item.find('div', class_='single-surgeon__meta-value')

                if label_tag and value_tag:
                    label_text = label_tag.get_text(strip=True).lower()
                    value_text = value_tag.get_text(strip=True)

                    # Розподіляємо значення в залежності від мітки
                    if 'phone' in label_text or 'tel' in label_text:
                        phone = value_text
                    elif 'fax' in label_text:
                        fax = value_text

            # Додаємо зібрані дані цієї картки до загального списку хірурга
            practices_list.append({
                "address": address,
                "phone": phone,
                "fax": fax
            })
            surgeons_data.append({
                "url": surgeon_url,
                "title": title,
                "practices": practices_list
            })

        time.sleep(1.0)

    except Exception as e:
        print(f"Помилка при парсингу сторінки {surgeon_url}: {e}")
# ================= ВИВЕДЕННЯ РЕЗУЛЬТАТІВ =================
print("\n=== ФІНАЛЬНІ РЕЗУЛЬТАТИ ===")
for data in surgeons_data:
    print(f"\nХірург: {data['title']}")
    print(f"Посилання: {data['url']}")
    print("Адреси та контакти:")

    for i, practice in enumerate(data['practices'], start=1):
        print(f"  Локація №{i}:")
        print(f"    Адреса: {practice['address']}")
        print(f"    Телефон: {practice['phone']}")
        print(f"    Факс: {practice['fax']}")
    print("-" * 60)