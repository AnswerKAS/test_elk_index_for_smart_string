# ELK — стенд для поиска ИТ-тикетов

Тестовое окружение на базе **Elasticsearch 8.13 + Kibana**, предназначенное для отработки стратегий полнотекстового поиска по русскоязычным ИТ-заявкам.

## Что внутри

| Компонент | Описание |
|---|---|
| `docker-compose.yml` | Elasticsearch + Kibana в Docker |
| `generate_and_load.py` | Генерация и загрузка 1 000 000 синтетических тикетов |
| `start.sh` | Единый скрипт запуска всего стенда |

### Схема индекса `it_tickets`

Каждый документ содержит:

- **`text.type_task`** — тип задачи (Инцидентный запрос, Запрос на обслуживание, Изменение, Проблема, Консультация)
- **`text.service`** — ИТ-сервис (AD, VPN, SAP, 1C, PostgreSQL, GitLab и др., всего 28 сервисов)
- **`text.examples`** — 5–12 примеров обращений в свободной форме
- **`text.full_path`** — иерархический путь (тип / категория / сервис / ID)
- **`priority`** — critical / high / medium / low
- **`status`** — open / in_progress / resolved / closed / pending
- **`created_at`** — дата создания (диапазон ~3 года)

### Анализаторы

| Анализатор | Назначение |
|---|---|
| `split_analyzer` | CamelCase → токены + русский стоп-список + стеммер |
| `concat_analyzer` | Слитное написание: «VKTeams» → «vkteams» |
| `ngram_analyzer` | N-граммы 2–6 для нечёткого поиска по коротким полям |
| `russian_analyzer` | Стандартный анализатор для длинных текстов на русском |

## Требования

- **Docker** (с плагином `compose`)
- **Python 3.12+**

## Быстрый старт

```bash
./start.sh
```

Скрипт последовательно:
1. Поднимает Elasticsearch и Kibana через `docker compose up -d`
2. Устанавливает Python-зависимости (`pip install -r requirements.txt`)
3. Генерирует и загружает 1 000 000 документов батчами по 2 000

После завершения:

| Сервис | URL |
|---|---|
| Elasticsearch | http://localhost:9200 |
| Kibana | http://localhost:5601 |

## Ручной запуск шагов

```bash
# Только инфраструктура
docker compose up -d

# Только загрузка данных (ES должен быть доступен)
python3 generate_and_load.py
```

## Параметры генератора

Константы в начале `generate_and_load.py`:

```python
ES_URL      = "http://localhost:9200"
INDEX_NAME  = "it_tickets"
BATCH_SIZE  = 2000
TOTAL_DOCS  = 1_000_000
```

## Ресурсы Elasticsearch

Контейнер запускается с **2 GB heap** (`ES_JAVA_OPTS=-Xms2g -Xmx2g`), индекс создаётся с 3 шардами и 0 репликами (оптимально для одиночного узла).
