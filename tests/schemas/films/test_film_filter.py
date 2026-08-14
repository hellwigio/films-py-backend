import pytest
from pydantic import ValidationError

from films.schemas.films.film_filter import FilmFilter


def test_year_sets_both_range_bounds() -> None:
    film_filter = FilmFilter(genres=["Drama"], year=2006)

    assert film_filter.year_from == 2006
    assert film_filter.year_to == 2006


def test_rejects_invalid_year_range() -> None:
    with pytest.raises(ValidationError, match="year_from должен быть меньше"):
        FilmFilter(genres=["Drama"], year_from=2010, year_to=2000)


def test_rejects_invalid_length_range() -> None:
    with pytest.raises(ValidationError, match="length_from должен быть меньше"):
        FilmFilter(length_from=120, length_to=60)


def test_normalizes_keyword_before_search() -> None:
    film_filter = FilmFilter(keyword="  The   Matrix  ")

    assert film_filter.keyword == "The Matrix"
    assert film_filter.search_event() == (
        "keyword",
        {"keyword": "the matrix"},
    )


def test_builds_genre_years_range_event() -> None:
    film_filter = FilmFilter(genres=["Action"], year_from=2001, year_to=2010)

    assert film_filter.search_event() == (
        "filters",
        {"genre": "Action", "years_range": "2001-2010"},
    )


def test_rejects_incomplete_year_range() -> None:
    with pytest.raises(ValidationError, match="обе границы"):
        FilmFilter(genres=["Action"], year_from=2001)


def test_allows_independent_genre_and_year_filters() -> None:
    assert FilmFilter(genres=["Action"]).genres == ["Action"]
    assert FilmFilter(year_from=2001, year_to=2010).year_from == 2001


def test_combines_keyword_genres_and_years_in_search_event() -> None:
    film_filter = FilmFilter(
        keyword="Matrix",
        genres=["Comedy", "Action"],
        year_from=2001,
        year_to=2010,
        ratings=["PG"],
    )

    assert film_filter.search_event() == (
        "filters",
        {
            "keyword": "matrix",
            "genres": ["Action", "Comedy"],
            "years_range": "2001-2010",
            "ratings": ["PG"],
        },
    )


def test_normalizes_multiple_genres() -> None:
    film_filter = FilmFilter(
        genres=[" Action ", "Comedy", "Action"],
        year=2006,
    )

    assert film_filter.genres == ["Action", "Comedy"]
    assert film_filter.search_event() == (
        "filters",
        {"genres": ["Action", "Comedy"], "years_range": "2006"},
    )


def test_rating_feature_and_length_only_search_is_recorded() -> None:
    film_filter = FilmFilter(
        ratings=[" PG ", "PG"],
        features=[" Trailers "],
        length_from=60,
    )

    assert film_filter.search_event() == (
        "filters",
        {
            "ratings": ["PG"],
            "features": ["Trailers"],
            "length_from": "60",
        },
    )
