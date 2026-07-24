#!/usr/bin/env python3
"""Generate 100k synthetic IT-support chat docs and bulk-load them into Elasticsearch.

Usage:
    python3 scripts/generate_and_load.py [count]

No third-party dependencies (urllib only) so it runs with a stock Python 3 install.
"""
import json
import random
import sys
import uuid
import datetime
import urllib.request
import urllib.error
from pathlib import Path

ES_URL = "http://localhost:9200"
INDEX = "it_support_chats"
ROOT = Path(__file__).resolve().parent.parent
MAPPING_PATH = ROOT / "elasticsearch" / "mapping.json"

CATEGORIES = [
    {"id": 1, "name": "Инцидентный запрос", "description": "Инцидентный запрос - описание инцидентного запроса."},
    {"id": 2, "name": "Запрос на обслуживание", "description": "Плановый запрос на обслуживание оборудования или ПО."},
    {"id": 3, "name": "Консультация", "description": "Консультация пользователя по работе сервисов."},
]

ORGS = [
    {
        "title1": "ООО Технологическая компания",
        "title2": "Департамент технического сопровождения",
        "title3": "Управление автоматизации ИТ-сервисов",
        "title4": "Департамент технического сопровождения",
        "title5": "Управление автоматизации ИТ-сервисов",
    },
    {
        "title1": "ООО Технологическая компания",
        "title2": "Департамент инфраструктуры",
        "title3": "Управление сетевых сервисов",
        "title4": "Департамент инфраструктуры",
        "title5": "Отдел сетевой поддержки",
    },
    {
        "title1": "ООО Технологическая компания",
        "title2": "Департамент разработки",
        "title3": "Управление бэкенд-разработки",
        "title4": "Департамент разработки",
        "title5": "Отдел платформенных сервисов",
    },
    {
        "title1": "ООО Технологическая компания",
        "title2": "Департамент клиентского сервиса",
        "title3": "Управление контакт-центра",
        "title4": "Департамент клиентского сервиса",
        "title5": "Отдел поддержки клиентов",
    },
    {
        "title1": "ООО Технологическая компания",
        "title2": "Департамент безопасности",
        "title3": "Управление информационной безопасности",
        "title4": "Департамент безопасности",
        "title5": "Отдел мониторинга ИБ",
    },
]

SERVICES = [
    {
        "id": 132,
        "name": "Не работает звук",
        "synonyms": ["наушники", "ганитура", "уши", "headset"],
        "description": "Решение проблем со звуком в наушниках и гарнитуре",
        "tags": ["ухо", "звук"],
        "full_path": "Инцидентный запрос/Оборудование/Гарнитура",
        "subtypes": [
            {
                "id": 231, "name": "Нет звука в МТС Линк", "synonyms": ["динамики", "звук", "мтс"],
                "description": "Решение проблем со звуком в наушниках", "tags": ["звук", "мтс"],
                "phrases": [
                    "Не работает гарнитура", "Меня не слышат при звонках",
                    "Не слышат только в звонках в мтс линке", "Пропал звук в наушниках",
                    "Гарнитура не подключается к компьютеру",
                ],
            },
            {
                "id": 232, "name": "Нет звука в Zoom", "synonyms": ["zoom", "звук"],
                "description": "Проблема со звуком в конференции Zoom", "tags": ["звук", "zoom"],
                "phrases": [
                    "В Zoom не слышно собеседника", "Не работает микрофон в Zoom",
                    "Пропадает звук во время звонка в Zoom", "Коллеги не слышат меня в Zoom",
                ],
            },
        ],
    },
    {
        "id": 140,
        "name": "Не работает камера",
        "synonyms": ["веб-камера", "камера", "видео", "webcam"],
        "description": "Решение проблем с веб-камерой на рабочем месте",
        "tags": ["видео", "камера"],
        "full_path": "Инцидентный запрос/Оборудование/Камера",
        "subtypes": [
            {
                "id": 241, "name": "Камера не определяется системой", "synonyms": ["драйвер", "камера"],
                "description": "Windows не видит подключенную камеру", "tags": ["камера", "драйвер"],
                "phrases": [
                    "Не работает камера на ноутбуке", "Камера не отображается в списке устройств",
                    "После обновления Windows пропала камера",
                ],
            },
            {
                "id": 242, "name": "Черный экран в видеозвонке", "synonyms": ["видео", "звонок"],
                "description": "Камера включена, но собеседники видят черный экран", "tags": ["видео", "звонок"],
                "phrases": [
                    "В Teams у меня черный экран вместо видео", "Камера включена но меня не видно",
                    "Видео не транслируется на созвоне",
                ],
            },
        ],
    },
    {
        "id": 150,
        "name": "Проблемы с VPN",
        "synonyms": ["vpn", "впн", "удаленный доступ"],
        "description": "Решение проблем с подключением к корпоративному VPN",
        "tags": ["сеть", "vpn"],
        "full_path": "Инцидентный запрос/Сеть/VPN",
        "subtypes": [
            {
                "id": 251, "name": "VPN не подключается", "synonyms": ["vpn", "подключение"],
                "description": "Клиент VPN выдает ошибку при подключении", "tags": ["vpn", "ошибка"],
                "phrases": [
                    "Не могу подключиться к VPN", "VPN выдает ошибку сертификата",
                    "После смены пароля перестал работать VPN", "VPN клиент зависает при запуске",
                ],
            },
            {
                "id": 252, "name": "Медленный VPN", "synonyms": ["скорость", "vpn"],
                "description": "Низкая скорость соединения через VPN", "tags": ["vpn", "скорость"],
                "phrases": [
                    "Очень медленно работает интернет через VPN", "VPN постоянно разрывает соединение",
                ],
            },
        ],
    },
    {
        "id": 160,
        "name": "Проблемы с доступом",
        "synonyms": ["пароль", "доступ", "логин", "учетная запись"],
        "description": "Восстановление доступа и сброс пароля учетной записи",
        "tags": ["доступ", "безопасность"],
        "full_path": "Инцидентный запрос/Безопасность/Доступ",
        "subtypes": [
            {
                "id": 261, "name": "Забыл пароль", "synonyms": ["пароль", "сброс"],
                "description": "Пользователь не может вспомнить пароль", "tags": ["пароль"],
                "phrases": [
                    "Забыл пароль от учетной записи", "Не могу войти в систему, пароль не подходит",
                    "Нужно сбросить пароль от почты",
                ],
            },
            {
                "id": 262, "name": "Учетная запись заблокирована", "synonyms": ["блокировка", "доступ"],
                "description": "Аккаунт заблокирован после нескольких неверных попыток входа", "tags": ["блокировка"],
                "phrases": [
                    "Учетная запись заблокирована после неверного ввода пароля",
                    "Пишет что аккаунт заблокирован, нужна разблокировка",
                ],
            },
        ],
    },
    {
        "id": 170,
        "name": "Не работает принтер",
        "synonyms": ["принтер", "печать", "мфу"],
        "description": "Решение проблем с печатью документов",
        "tags": ["принтер", "печать"],
        "full_path": "Инцидентный запрос/Оборудование/Принтер",
        "subtypes": [
            {
                "id": 271, "name": "Принтер не печатает", "synonyms": ["принтер", "печать"],
                "description": "Документ отправлен на печать, но принтер не реагирует", "tags": ["принтер"],
                "phrases": [
                    "Принтер не печатает документы", "Отправил на печать но ничего не происходит",
                    "Принтер показывает офлайн статус",
                ],
            },
            {
                "id": 272, "name": "Замятие бумаги", "synonyms": ["бумага", "замятие"],
                "description": "В принтере замялась бумага", "tags": ["принтер", "бумага"],
                "phrases": [
                    "В принтере зажевало бумагу", "Постоянно замятие бумаги в МФУ",
                ],
            },
        ],
    },
    {
        "id": 180,
        "name": "Проблемы с Wi-Fi",
        "synonyms": ["wifi", "wi-fi", "вайфай", "беспроводная сеть"],
        "description": "Решение проблем с подключением к беспроводной сети офиса",
        "tags": ["сеть", "wifi"],
        "full_path": "Инцидентный запрос/Сеть/Wi-Fi",
        "subtypes": [
            {
                "id": 281, "name": "Не подключается к Wi-Fi", "synonyms": ["wifi", "подключение"],
                "description": "Устройство не видит или не подключается к сети офиса", "tags": ["wifi"],
                "phrases": [
                    "Ноутбук не видит корпоративный Wi-Fi", "Не могу подключиться к сети офиса",
                    "Wi-Fi постоянно отключается",
                ],
            },
            {
                "id": 282, "name": "Медленный Wi-Fi", "synonyms": ["скорость", "wifi"],
                "description": "Низкая скорость беспроводного соединения", "tags": ["wifi", "скорость"],
                "phrases": [
                    "Очень медленный интернет по Wi-Fi", "Wi-Fi еле работает на 3 этаже",
                ],
            },
        ],
    },
    {
        "id": 190,
        "name": "Медленно работает компьютер",
        "synonyms": ["зависает", "тормозит", "лагает"],
        "description": "Диагностика низкой производительности рабочей станции",
        "tags": ["производительность", "пк"],
        "full_path": "Инцидентный запрос/Оборудование/ПК",
        "subtypes": [
            {
                "id": 291, "name": "Компьютер зависает", "synonyms": ["зависание", "пк"],
                "description": "Рабочая станция периодически зависает", "tags": ["пк", "зависание"],
                "phrases": [
                    "Компьютер постоянно зависает", "Ноутбук сильно тормозит при работе",
                    "После обновления система стала очень медленной",
                ],
            },
            {
                "id": 292, "name": "Долгая загрузка системы", "synonyms": ["загрузка", "старт"],
                "description": "Windows долго загружается при включении", "tags": ["пк", "загрузка"],
                "phrases": [
                    "Компьютер очень долго включается", "Загрузка Windows занимает больше 10 минут",
                ],
            },
        ],
    },
]

FIRST_NAMES = ["ivan", "anna", "petr", "olga", "sergey", "elena", "dmitry", "maria", "andrey", "natalia"]
LAST_NAMES = ["ivanov", "petrova", "sidorov", "kuznetsova", "smirnov", "popova", "volkov", "fedorova"]


def random_email(i):
    return f"{random.choice(FIRST_NAMES)}.{random.choice(LAST_NAMES)}{i}@example-corp.ru"


def random_date():
    start = datetime.datetime.now() - datetime.timedelta(days=365)
    delta = datetime.timedelta(seconds=random.randint(0, 365 * 24 * 3600))
    return (start + delta).replace(microsecond=0).isoformat()


def gen_doc(i):
    service = random.choice(SERVICES)
    subtype = random.choice(service["subtypes"])
    org = random.choice(ORGS)
    category = random.choice(CATEGORIES)
    phrases = random.sample(subtype["phrases"], k=min(len(subtype["phrases"]), random.randint(1, 3)))

    return {
        "chat": {
            "chat_id": str(uuid.uuid4()),
            "chat_name": phrases[0],
            "chat_ai_summary": f"Пользователь обратился в техническую поддержку с проблемой: {subtype['name'].lower()}",
            "chat_full_user_text": phrases,
            "chat_create_at": random_date(),
        },
        "category": category,
        "service": {k: v for k, v in service.items() if k != "subtypes"},
        "subtype": {k: v for k, v in subtype.items() if k != "phrases"},
        "user": {
            "email": random_email(i),
            "org": org,
        },
    }


def http_request(method, path, body=None):
    data = body.encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if body is not None and path.endswith("/_bulk"):
        headers["Content-Type"] = "application/x-ndjson"
    req = urllib.request.Request(f"{ES_URL}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def recreate_index():
    status, body = http_request("DELETE", f"/{INDEX}")
    print(f"DELETE /{INDEX} -> {status}")
    mapping = MAPPING_PATH.read_text(encoding="utf-8")
    status, body = http_request("PUT", f"/{INDEX}", mapping)
    print(f"PUT /{INDEX} -> {status}")
    if status >= 300:
        print(body)
        sys.exit(1)


def bulk_load(count, batch_size=2000):
    total = 0
    buf = []
    for i in range(1, count + 1):
        doc = gen_doc(i)
        buf.append(json.dumps({"index": {"_index": INDEX}}))
        buf.append(json.dumps(doc, ensure_ascii=False))
        if len(buf) >= batch_size * 2:
            _send_bulk(buf)
            total += len(buf) // 2
            print(f"Loaded {total}/{count}")
            buf = []
    if buf:
        _send_bulk(buf)
        total += len(buf) // 2
        print(f"Loaded {total}/{count}")


def _send_bulk(buf):
    body = "\n".join(buf) + "\n"
    status, resp_body = http_request("POST", "/_bulk", body)
    if status >= 300:
        print(resp_body)
        sys.exit(1)
    result = json.loads(resp_body)
    if result.get("errors"):
        for item in result["items"]:
            err = item.get("index", {}).get("error")
            if err:
                print("Bulk item error:", err)
                sys.exit(1)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    recreate_index()
    bulk_load(n)
    status, body = http_request("POST", f"/{INDEX}/_refresh")
    status, body = http_request("GET", f"/{INDEX}/_count")
    print(body)
