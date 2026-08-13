.PHONY: help env bootstrap net-create up down logs build lint format lint-fix mongo-clear-searches

.DEFAULT_GOAL := help

help: ## Показать доступные команды
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

bootstrap: build up ## С нуля после клонирования: сборка, запуск
	@echo ""
	@echo "Проверьте DB_URL в .env, если API не подключается к базе."

net-create: ## Создать Docker-сеть ichub_films_net
	docker network create ichub_films_net || true

up: net-create ## Поднять проект в Docker
	docker compose up -d
	@echo ""
	@echo "Сервисы запущены:"
	@echo "  API:       http://localhost:8000"
	@echo "  Swagger:   http://localhost:8000/docs"
	@echo "  Grafana:   http://localhost:3000"
	@echo "  Alloy:     http://localhost:12345"
	@echo "  MongoDB:   mongodb://localhost:27017"
	@echo ""
	@echo "Grafana по умолчанию: admin / admin"

down: ## Остановить Docker контейнеры
	docker compose down

logs: ## Посмотреть логи приложения
	docker compose logs -f app

build: ## Собрать Docker образ
	docker compose build

lint: ## Проверка кода (ruff)
	uv run ruff check .

format: ## Форматирование кода (ruff)
	uv run ruff format .

lint-fix: ## Ruff с автоисправлением
	uv run ruff check --fix .

mongo-clear-searches: ## Очистить поисковые запросы в MongoDB
	docker compose exec -T app uv run python -m src.scripts.clear_search_history

test:
	uv run pytest
