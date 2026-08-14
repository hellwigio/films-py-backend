from films.query_builders.film_query_builder import FilmQueryBuilder
from films.schemas.films.film_filter import FilmFilter


def test_query_builder_combines_filters_and_uses_stable_sort() -> None:
    query = FilmQueryBuilder(
        FilmFilter(
            keyword="academy",
            genres=["Action", "Comedy"],
            ratings=["PG"],
            features=["Trailers"],
            year_from=2000,
            year_to=2010,
            length_from=60,
            length_to=120,
            order_by="-release_year",
        )
    ).build()

    sql = str(query)

    assert "JOIN film_category" in sql
    assert "JOIN category" in sql
    assert "lower(film.title) LIKE lower(" in sql
    assert "category.name IN" in sql
    assert "film.rating IN" in sql
    assert "film.special_features LIKE" in sql
    assert "film.release_year >=" in sql
    assert "film.release_year <=" in sql
    assert "film.length >=" in sql
    assert "film.length <=" in sql
    assert "ORDER BY film.release_year DESC, film.film_id ASC" in sql
    assert sql.startswith("SELECT DISTINCT")


def test_query_builder_defaults_to_title_then_id_sort() -> None:
    sql = str(FilmQueryBuilder(FilmFilter()).build())

    assert "ORDER BY film.title ASC, film.film_id ASC" in sql
