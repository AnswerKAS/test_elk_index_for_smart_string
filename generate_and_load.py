#!/usr/bin/env python3
"""Generate and bulk-load 1 000 000 documents into Elasticsearch."""

import json
import random
import time
from itertools import cycle

import requests

ES_URL = "http://localhost:9200"
INDEX_NAME = "it_tickets"
BATCH_SIZE = 2000
TOTAL_DOCS = 1_000_000

# ── Reference data ────────────────────────────────────────────────────────────

TASK_TYPES = [
    {
        "type_id": 1,
        "name": "Инцидентный запрос",
        "description": (
            "Инцидентный запрос — это незапланированное прерывание или ухудшение работы "
            "ИТ‑сервиса, требующее максимально быстрого восстановления. Задачи связанные "
            "с проблемами в работе программ, систем или оборудования."
        ),
    },
    {
        "type_id": 2,
        "name": "Запрос на обслуживание",
        "description": (
            "Запрос на обслуживание — стандартная заявка на предоставление доступа, "
            "установку ПО, настройку оборудования или выполнение плановых работ. "
            "Не является нарушением работы сервиса."
        ),
    },
    {
        "type_id": 3,
        "name": "Изменение",
        "description": (
            "Изменение — плановая модификация ИТ-инфраструктуры или сервиса, требующая "
            "согласования. Включает обновления ПО, конфигурационные правки, миграции данных."
        ),
    },
    {
        "type_id": 4,
        "name": "Проблема",
        "description": (
            "Проблема — корневая причина одного или нескольких инцидентов, требующая "
            "глубокого анализа и долгосрочного устранения, а не только симптоматического лечения."
        ),
    },
    {
        "type_id": 5,
        "name": "Консультация",
        "description": (
            "Консультация — запрос на получение информации, разъяснения процессов или "
            "помощи в использовании сервиса без признаков инцидента или необходимости изменений."
        ),
    },
]

SERVICES = [
    {"service_id": 101, "tags": "Active Directory", "synonyms": "AD, LDAP", "name": "Active Directory", "pyrus_id": 201, "category": "Инфраструктура"},
    {"service_id": 102, "tags": "VPN", "synonyms": "Cisco AnyConnect, OpenVPN", "name": "VPN (корпоративный)", "pyrus_id": 202, "category": "Сеть"},
    {"service_id": 103, "tags": "Email", "synonyms": "Outlook, почта, Exchange", "name": "Корпоративная почта (Outlook)", "pyrus_id": 203, "category": "Коммуникации"},
    {"service_id": 104, "tags": "Jira", "synonyms": "трекер задач, issue tracker", "name": "Jira", "pyrus_id": 204, "category": "Управление проектами"},
    {"service_id": 105, "tags": "Confluence", "synonyms": "wiki, база знаний", "name": "Confluence", "pyrus_id": 205, "category": "Управление знаниями"},
    {"service_id": 201, "tags": "SAP HR", "synonyms": "SAP, ПО кадрового учёта", "name": "SAP HR (кадровый учёт)", "pyrus_id": 301, "category": "ERP"},
    {"service_id": 202, "tags": "SAP Finance", "synonyms": "SAP FI, бухгалтерия", "name": "SAP Finance", "pyrus_id": 302, "category": "ERP"},
    {"service_id": 203, "tags": "1C Бухгалтерия", "synonyms": "1С, бухгалтерия", "name": "1C Бухгалтерия", "pyrus_id": 303, "category": "ERP"},
    {"service_id": 204, "tags": "1C ЗУП", "synonyms": "зарплата, кадры", "name": "1C ЗУП (головной офис)", "pyrus_id": 304, "category": "ERP"},
    {"service_id": 332, "tags": "1C ЗУП", "synonyms": None, "name": "1C ЗУП (Совкомбанк Страхование)", "pyrus_id": 139, "category": "ERP"},
    {"service_id": 301, "tags": "Windows", "synonyms": "ОС, операционная система", "name": "Windows (рабочая станция)", "pyrus_id": 401, "category": "ОС"},
    {"service_id": 302, "tags": "Linux", "synonyms": "Ubuntu, CentOS, RHEL", "name": "Linux-сервер", "pyrus_id": 402, "category": "ОС"},
    {"service_id": 303, "tags": "macOS", "synonyms": "Mac, Apple", "name": "macOS (рабочая станция)", "pyrus_id": 403, "category": "ОС"},
    {"service_id": 401, "tags": "PostgreSQL", "synonyms": "Postgres, СУБД", "name": "PostgreSQL", "pyrus_id": 501, "category": "СУБД"},
    {"service_id": 402, "tags": "Oracle DB", "synonyms": "Oracle, СУБД", "name": "Oracle Database", "pyrus_id": 502, "category": "СУБД"},
    {"service_id": 403, "tags": "MS SQL", "synonyms": "MSSQL, SQL Server", "name": "Microsoft SQL Server", "pyrus_id": 503, "category": "СУБД"},
    {"service_id": 501, "tags": "Cisco", "synonyms": "сеть, коммутатор, маршрутизатор", "name": "Cisco (сетевое оборудование)", "pyrus_id": 601, "category": "Сеть"},
    {"service_id": 502, "tags": "Wi-Fi", "synonyms": "беспроводная сеть, точка доступа", "name": "Wi-Fi (корпоративный)", "pyrus_id": 602, "category": "Сеть"},
    {"service_id": 601, "tags": "Антивирус", "synonyms": "Kaspersky, VirusTotal, защита", "name": "Антивирус (Kaspersky)", "pyrus_id": 701, "category": "Безопасность"},
    {"service_id": 602, "tags": "DLP", "synonyms": "утечка данных, контроль", "name": "DLP-система", "pyrus_id": 702, "category": "Безопасность"},
    {"service_id": 701, "tags": "Телефония", "synonyms": "SIP, IP-телефон, звонки", "name": "IP-телефония", "pyrus_id": 801, "category": "Коммуникации"},
    {"service_id": 702, "tags": "VKTeams", "synonyms": "мессенджер, чат, ВКТимс", "name": "VKTeams (корпоративный мессенджер)", "pyrus_id": 802, "category": "Коммуникации"},
    {"service_id": 801, "tags": "Принтер", "synonyms": "МФУ, сканер, печать", "name": "Принтер / МФУ", "pyrus_id": 901, "category": "Оборудование"},
    {"service_id": 802, "tags": "Ноутбук", "synonyms": "лэптоп, компьютер", "name": "Ноутбук / ПК (выдача/ремонт)", "pyrus_id": 902, "category": "Оборудование"},
    {"service_id": 901, "tags": "Pyrus", "synonyms": "пайрус, согласование", "name": "Pyrus (согласование документов)", "pyrus_id": 1001, "category": "Управление проектами"},
    {"service_id": 902, "tags": "СЭД", "synonyms": "документооборот, EDMS", "name": "СЭД (электронный документооборот)", "pyrus_id": 1002, "category": "Управление знаниями"},
    {"service_id": 1001, "tags": "GitLab", "synonyms": "git, репозиторий, CI/CD", "name": "GitLab (репозиторий)", "pyrus_id": 1101, "category": "Разработка"},
    {"service_id": 1002, "tags": "Docker", "synonyms": "контейнер, kubernetes, k8s", "name": "Docker / Kubernetes", "pyrus_id": 1102, "category": "Разработка"},
]

PATH_CATEGORIES = [
    "Программа\\Веб-ресурс",
    "Инфраструктура\\Серверы",
    "Инфраструктура\\Сеть",
    "Рабочая станция\\Оборудование",
    "Рабочая станция\\ПО",
    "Безопасность\\Доступы",
    "Безопасность\\Инциденты",
    "Коммуникации\\Почта",
    "Коммуникации\\Мессенджеры",
    "СУБД\\Производительность",
    "СУБД\\Доступ",
    "Разработка\\CI-CD",
    "Разработка\\Репозитории",
]

EXAMPLE_TEMPLATES = [
    "{path}; ; {issue}; {detail}",
    "{path}; {title}; {issue}",
    "{path}; ; {detail}",
]

ISSUES = [
    "Не могу войти в систему",
    "Приложение вылетает при запуске",
    "Ошибка при сохранении документа",
    "Нет доступа к ресурсу",
    "Медленная работа сервиса",
    "Не отображаются данные",
    "Ошибка синхронизации",
    "Не приходят уведомления",
    "Проблема с печатью",
    "VPN не подключается",
    "Не отправляется почта",
    "Ошибка авторизации",
    "Зависает при загрузке",
    "Некорректно отображается интерфейс",
    "Нет звука в звонке",
    "Потеря соединения с сервером",
    "Не загружается файл",
    "Ошибка при формировании отчёта",
    "Недоступен личный кабинет",
    "Сбой интеграции с внешней системой",
]

DETAILS = [
    "Прошу срочно разобраться, ситуация критическая.",
    "Проблема возникла после обновления.",
    "Затронуты несколько сотрудников отдела.",
    "Ошибка воспроизводится стабильно.",
    "Проблема возникла сегодня утром.",
    "Обходного пути нет, работа заблокирована.",
    "Прошу проверить и восстановить доступ.",
    "Пробовал перезагрузку — не помогло.",
    "Ошибка возникает только на одном устройстве.",
    "Коллеги также столкнулись с проблемой.",
]

TITLES = [
    "Срочное восстановление доступа",
    "Настройка учётной записи",
    "Обновление прав пользователя",
    "Восстановление выгрузки отчётов",
    "Исправление персональных данных",
    "Подключение к удалённому рабочему месту",
    "Консультация по использованию системы",
    "",
    "",
    "",
]


# ── Index mapping ─────────────────────────────────────────────────────────────

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 0,
        # ES требует явного разрешения когда max_gram - min_gram > 1
        "max_ngram_diff": 4,
        "analysis": {
            "char_filter": {
                # Вставляет пробел на границах CamelCase:
                #   "VKTeams"          → "VK Teams"
                #   "ActiveDirectory"  → "Active Directory"
                #   "1CБухгалтерия"    → "1C Бухгалтерия"
                "camel_split": {
                    "type": "pattern_replace",
                    "pattern": r"(?<=\p{Lu})(?=\p{Lu}\p{Ll})|(?<=\p{Ll})(?=\p{Lu})|(?<=\p{L})(?=\p{N})|(?<=\p{N})(?=\p{L})",
                    "replacement": " ",
                }
            },
            "analyzer": {
                # split_analyzer: "VKTeams" → ["vk", "teams"]
                "split_analyzer": {
                    "type": "custom",
                    "char_filter": ["camel_split"],
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                },
                # concat_analyzer: "VKTeams" → ["vkteams"]
                "concat_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                },
                # ngram_analyzer: только для индексации коротких полей (name, tags, synonyms)
                # search_analyzer у таких полей = split_analyzer, чтобы не дробить запрос в нграммы
                "ngram_analyzer": {
                    "type": "custom",
                    "char_filter": ["camel_split"],
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ngram_filter"],
                },
                # Для полей с обычным текстом (описания, примеры)
                "russian_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                },
            },
            "filter": {
                "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                "russian_stemmer": {"type": "stemmer", "language": "russian"},
                # min=2 ловит "вк", max=6 покрывает "тимс", "teams", "outlook"
                "ngram_filter": {
                    "type": "ngram",
                    "min_gram": 2,
                    "max_gram": 6,
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "name": {"type": "keyword"},
            "text": {
                "type": "object",
                "properties": {
                    "type_task": {
                        "type": "object",
                        "properties": {
                            "type_id": {"type": "integer"},
                            "name": {
                                "type": "text",
                                "analyzer": "split_analyzer",
                                "fields": {
                                    "concat":   {"type": "text", "analyzer": "concat_analyzer"},
                                    "ngram":    {"type": "text", "analyzer": "ngram_analyzer", "search_analyzer": "split_analyzer"},
                                    "keyword":  {"type": "keyword"},
                                },
                            },
                            "description": {"type": "text", "analyzer": "russian_analyzer"},
                        },
                    },
                    "service": {
                        "type": "object",
                        "properties": {
                            "service_id": {"type": "integer"},
                            "tags": {
                                "type": "text",
                                "analyzer": "split_analyzer",
                                "fields": {
                                    "concat":   {"type": "text", "analyzer": "concat_analyzer"},
                                    "ngram":    {"type": "text", "analyzer": "ngram_analyzer", "search_analyzer": "split_analyzer"},
                                    "keyword":  {"type": "keyword"},
                                },
                            },
                            "synonyms": {
                                "type": "text",
                                "analyzer": "split_analyzer",
                                "fields": {
                                    "ngram": {"type": "text", "analyzer": "ngram_analyzer", "search_analyzer": "split_analyzer"},
                                },
                            },
                            "description": {"type": "text", "analyzer": "russian_analyzer"},
                            "name": {
                                "type": "text",
                                "analyzer": "split_analyzer",
                                "fields": {
                                    "concat":   {"type": "text", "analyzer": "concat_analyzer"},
                                    "ngram":    {"type": "text", "analyzer": "ngram_analyzer", "search_analyzer": "split_analyzer"},
                                    "keyword":  {"type": "keyword"},
                                },
                            },
                            "pyrus_id": {"type": "integer"},
                            "category": {"type": "keyword"},
                        },
                    },
                    "examples": {"type": "text", "analyzer": "russian_analyzer"},
                    "full_path": {
                        "type": "text",
                        "analyzer": "split_analyzer",
                        "fields": {
                            "concat":  {"type": "text", "analyzer": "concat_analyzer"},
                            "ngram":   {"type": "text", "analyzer": "ngram_analyzer", "search_analyzer": "split_analyzer"},
                            "keyword": {"type": "keyword"},
                        },
                    },
                },
            },
            "created_at": {"type": "date"},
            "priority": {"type": "keyword"},
            "status": {"type": "keyword"},
        }
    },
}

PRIORITIES = ["critical", "high", "medium", "low"]
STATUSES = ["open", "in_progress", "resolved", "closed", "pending"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def wait_for_es(timeout: int = 60):
    print("Waiting for Elasticsearch…", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{ES_URL}/_cluster/health", timeout=3)
            if r.status_code == 200 and r.json().get("status") in ("green", "yellow"):
                print(" ready.")
                return
        except requests.exceptions.ConnectionError:
            pass
        print(".", end="", flush=True)
        time.sleep(2)
    raise TimeoutError("Elasticsearch did not become ready in time.")


def create_index():
    r = requests.head(f"{ES_URL}/{INDEX_NAME}")
    if r.status_code == 200:
        print(f"Index '{INDEX_NAME}' already exists, deleting…")
        requests.delete(f"{ES_URL}/{INDEX_NAME}")

    r = requests.put(
        f"{ES_URL}/{INDEX_NAME}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(INDEX_MAPPING),
    )
    r.raise_for_status()
    print(f"Index '{INDEX_NAME}' created: {r.json()}")


def build_examples(path: str, service_name: str, n: int = 10) -> str:
    lines = []
    for i in range(1, n + 1):
        issue = random.choice(ISSUES)
        detail = random.choice(DETAILS)
        title = random.choice(TITLES)
        tmpl = random.choice(EXAMPLE_TEMPLATES)
        line = tmpl.format(path=f"{path}\\\\{service_name}", title=title, issue=issue, detail=detail)
        lines.append(f"{i}) {line}")
    return "\n\n".join(lines) + "\n\n"


def generate_doc(doc_id: int) -> dict:
    task = random.choice(TASK_TYPES)
    service = random.choice(SERVICES)
    path_cat = random.choice(PATH_CATEGORIES)

    full_path = f"{task['name']}/{path_cat}/{service['name']}/{service['service_id']}"
    doc_name = f"{task['name']};{path_cat};{service['name']};{service['service_id']}.json"

    # Vary the number of examples slightly
    n_examples = random.randint(5, 12)
    examples = build_examples(path_cat, service["name"], n_examples)

    # Fake ISO timestamp spread across ~3 years
    ts_offset = random.randint(0, 3 * 365 * 24 * 3600)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(1_609_459_200 + ts_offset))

    return {
        "name": doc_name,
        "text": {
            "type_task": {
                "type_id": task["type_id"],
                "name": task["name"],
                "description": task["description"],
            },
            "service": {
                "service_id": service["service_id"],
                "tags": service["tags"],
                "synonyms": service.get("synonyms"),
                "description": service.get("description", ""),
                "name": service["name"],
                "pyrus_id": service["pyrus_id"],
                "category": service["category"],
            },
            "examples": examples,
            "full_path": full_path,
        },
        "created_at": ts,
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
    }


def bulk_load():
    total_loaded = 0
    start = time.time()

    print(f"Loading {TOTAL_DOCS:,} documents in batches of {BATCH_SIZE:,}…")

    for batch_start in range(0, TOTAL_DOCS, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, TOTAL_DOCS)
        lines = []
        for doc_id in range(batch_start, batch_end):
            lines.append(json.dumps({"index": {"_index": INDEX_NAME}}))
            lines.append(json.dumps(generate_doc(doc_id), ensure_ascii=False))

        body = "\n".join(lines) + "\n"

        for attempt in range(3):
            try:
                r = requests.post(
                    f"{ES_URL}/_bulk",
                    headers={"Content-Type": "application/x-ndjson"},
                    data=body.encode("utf-8"),
                    timeout=60,
                )
                r.raise_for_status()
                resp = r.json()
                if resp.get("errors"):
                    # Print first error for diagnosis
                    for item in resp["items"]:
                        if "error" in item.get("index", {}):
                            print(f"  Bulk error: {item['index']['error']}")
                            break
                break
            except requests.exceptions.RequestException as exc:
                if attempt == 2:
                    raise
                print(f"  Retrying batch {batch_start}… ({exc})")
                time.sleep(2)

        total_loaded += batch_end - batch_start
        elapsed = time.time() - start
        rate = total_loaded / elapsed if elapsed else 0
        pct = total_loaded / TOTAL_DOCS * 100
        eta = (TOTAL_DOCS - total_loaded) / rate if rate else 0
        print(
            f"  {total_loaded:>9,} / {TOTAL_DOCS:,}  ({pct:5.1f}%)  "
            f"{rate:6.0f} docs/s  ETA {eta:5.0f}s",
            end="\r",
        )

    print(f"\nDone. {total_loaded:,} documents loaded in {time.time() - start:.1f}s.")


def print_stats():
    r = requests.get(f"{ES_URL}/{INDEX_NAME}/_count")
    count = r.json().get("count", "?")
    r2 = requests.get(f"{ES_URL}/_cat/indices/{INDEX_NAME}?v&h=index,docs.count,store.size")
    print(f"\nIndex stats:\n{r2.text}")
    print(f"Total documents: {count:,}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    wait_for_es()
    create_index()
    bulk_load()
    print_stats()
