import pytest
from pydantic import ValidationError

from films.schemas.films.film_filter import FilmFilter


def test_exact_year_remains_independent_from_range() -> None:
    film_filter = FilmFilter(genres=["Drama"], year=2006)

    assert film_filter.year_from is None
    assert film_filter.year_to is None
    assert film_filter.search_event() == (
        "genre__year",
        {"genre": "Drama", "year": "2006"},
    )


def test_exact_year_does_not_replace_explicit_range() -> None:
    film_filter = FilmFilter(year=2005, year_from=1990, year_to=1995)

    assert film_filter.year == 2005
    assert film_filter.year_from == 1990
    assert film_filter.year_to == 1995
    assert film_filter.search_event() == (
        "year__years_range",
        {"year": "2005", "years_range": "1990-1995"},
    )


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
        "genre__years_range",
        {"genre": "Action", "years_range": "2001-2010"},
    )


def test_equal_range_remains_a_range() -> None:
    film_filter = FilmFilter(year_from=2005, year_to=2005)

    assert film_filter.search_event() == (
        "years_range",
        {"years_range": "2005-2005"},
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
        "keyword__genre__years_range__rating",
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
        "genre__year",
        {"genres": ["Action", "Comedy"], "year": "2006"},
    )


def test_rating_feature_and_length_only_search_is_recorded() -> None:
    film_filter = FilmFilter(
        ratings=[" PG ", "PG"],
        features=[" Trailers "],
        length_from=60,
    )

    assert film_filter.search_event() == (
        "rating__feature__length_from",
        {
            "ratings": ["PG"],
            "features": ["Trailers"],
            "length_from": "60",
        },
    )
