# Films API

Итоговый проект по Python и базам данных: REST API для поиска фильмов в MySQL,
сохранения всех поисковых запросов в MongoDB и отображения статистики.

## Стек

- Python 3.13, [uv](https://docs.astral.sh/uv/)
- FastAPI, Uvicorn
- SQLAlchemy 2 async
- MySQL Sakila database
- MongoDB, Motor
- OpenTelemetry, Tempo, Grafana

## Быстрый старт

```bash
cp .env.example .env
# укажите DB_URL, PORT и точное название группы в SEARCH_QUERIES_COLLECTION
make bootstrap
```

Порт API задаётся один раз через `PORT` в `.env` (по умолчанию `8000`). Он
используется и FastAPI, и Docker Compose для публикации порта.

По умолчанию используется коллекция
`final_project_ichub_dmitriy_hellwig`. Если официальное название группы
отличается, измените только `SEARCH_QUERIES_COLLECTION` в локальном `.env`.
Сам файл `.env` игнорируется Git.

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Grafana: http://localhost:3000
- Grafana Alloy: http://localhost:12345

## API

Базовый prefix: `/v1`.

### `GET /v1/films/search-meta`

Данные для формы поиска перед вводом пользователем:

- список всех жанров из `category`
- список всех рейтингов из `film.rating`
- список всех специальных возможностей из `film.special_features`
- минимальный год выпуска фильмов
- максимальный год выпуска фильмов
- минимальная длительность фильма
- максимальная длительность фильма

Ответ:

```json
{
  "genres": ["Action", "Comedy"],
  "ratings": ["G", "PG", "PG-13", "R"],
  "features": ["Behind the Scenes", "Commentaries", "Deleted Scenes", "Trailers"],
  "min_release_year": 2005,
  "max_release_year": 2012,
  "min_length": 46,
  "max_length": 185
}
```

### `GET /v1/films/`

Список фильмов. Размер страницы по умолчанию — 10 фильмов. Пользователь может
выбрать 10, 12, 24, 36 или 48 карточек. Следующие результаты запрашиваются
через `page=2`, `page=3` и так далее.

Фильтры:

| Параметр | Описание |
|----------|----------|
| `keyword` | Поиск по названию фильма |
| `title` | Алиас для поиска по названию |
| `genre` | Один или несколько жанров; параметр можно повторять |
| `ratings` | Один или несколько рейтингов фильма |
| `features` | Одна или несколько специальных возможностей |
| `year` | Конкретный год выпуска |
| `year_from` | Нижняя граница года выпуска |
| `year_to` | Верхняя граница года выпуска |
| `length_from` | Минимальная длительность фильма |
| `length_to` | Максимальная длительность фильма |
| `page` | Номер страницы, по умолчанию `1` |
| `size` | Размер страницы: `10`, `12`, `24`, `36` или `48` |

Сортировка: `order_by` (`title`, `-title`, `release_year`, `-release_year`), по умолчанию `title`.

Примеры:

```text
GET /v1/films/?keyword=academy&page=1&size=10
GET /v1/films/?genre=Comedy&genre=Drama&year_from=2005&year_to=2012&page=2
GET /v1/films/?genre=Drama&year=2006
GET /v1/films/?keyword=academy&genre=Action&year_from=2000&year_to=2020
GET /v1/films/?ratings=PG&ratings=PG-13&features=Trailers&length_from=60
```

Все фильтры независимы и могут сочетаться. Например, ключевое слово с жанрами
и диапазоном лет объединяется в SQL через `AND`. Несколько выбранных жанров
объединяются между собой через `OR` (`category.name IN (...)`).

Ответ:

```json
{
  "items": [
    {
      "id": 1,
      "title": "ACADEMY DINOSAUR",
      "description": "...",
      "release_year": 2006,
      "rental_duration": 6,
      "rental_rate": 0.99,
      "length": 86,
      "replacement_cost": 20.99,
      "rating": "PG",
      "genres": ["Documentary"],
      "features": ["Deleted Scenes", "Behind the Scenes"]
    }
  ],
  "total": 12,
  "page": 1,
  "size": 10,
  "pages": 2
}
```

### `GET /v1/films/{film_id}`

Один фильм по `film.film_id`. При отсутствии возвращает `404`.

### `GET /v1/films/search-statistics`

Пять уникальных поисковых запросов. Режим выбирается пользователем:

- `?order=frequency` — самые частые по убыванию частоты;
- `?order=latest` — последние уникальные от новых к старым.

При нескольких жанрах MongoDB сохраняет `genres` как массив. При одном жанре
сохраняется поле `genre`, как в исходном ТЗ.

Ответ:

```json
{
  "items": [
    {
      "timestamp": "2025-05-01T15:35:00Z",
      "search_type": "filters",
      "params": {
        "genres": ["Action", "Comedy"],
        "years_range": "2001-2010"
      },
      "results_count": 5,
      "frequency": 3
    }
  ]
}
```

В MongoDB каждый первый реальный запрос сохраняется отдельным документом.
Переходы на `page=2` и далее не записываются. `results_count` берётся из
полного SQL `COUNT` без `LIMIT` и `OFFSET`.

Поиск только по рейтингу, специальным возможностям или длительности также
сохраняется. Простое ключевое слово получает тип `keyword`, любые составные
фильтры — тип `filters`.

`GET /v1/films/popular-searches` оставлен как алиас статистики по частоте.

## Надёжность

- ключевые слова и жанры очищаются от пробелов;
- неизвестные жанры и годы вне диапазона базы возвращают HTTP 422;
- неполный и обратный диапазон возвращает HTTP 422;
- при сбое MongoDB поиск в MySQL продолжает работать;
- недоступная статистика возвращает HTTP 503 с понятной подсказкой;
- непредвиденные ошибки возвращаются в JSON, не завершая сервер.

## Локальная разработка без Docker

```bash
uv sync
uv run fastapi dev src/films/main.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

SQLAlchemy и FastAPI инструментированы OpenTelemetry. SQL-запросы можно
посмотреть в трейсе через Grafana и источник данных Tempo.

Логи Docker-контейнеров собираются Grafana Alloy и хранятся в Loki семь дней.
Чтобы посмотреть их, откройте в Grafana раздел **Explore**, выберите источник
**Loki** и выполните, например, один из запросов:

```logql
{container="app"}
{service_name="frontend"}
{compose_project="films_py_project"} |= "ERROR"
```

Tempo остаётся источником трейсов. Экспорт метрик явно отключён через
`OTEL_METRICS_EXPORTER=none`, поскольку metrics pipeline в Collector пока не
настроен.

Сценарий защиты находится в [PRESENTATION.md](PRESENTATION.md).
