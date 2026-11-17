import pytest

from src import MovieStorage
import main
import pandas as pd
from pathlib import Path

def test_movies_persist(client, test_storage, uploaded_movies):
    # TODO: create another MovieStorage pointing to test_storage.db_path.
    # Use that object to get the movies and count them.
    # Check 20 rows, all four DataFrame columns, and the original title order.
    # Compare IDs from that object's select_columns() with GET /movies?limit=100.
    # Both should return IDs 1 through 20 in row order.
    storage_obj_test = MovieStorage(test_storage.db_path)
    MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]

    sample_csv_path = Path(__file__).parent.parent / "fixtures" / "sample_movies.csv"
    expected_titles = list(pd.read_csv(sample_csv_path)["title"])


    t_df = storage_obj_test.get()
    t_count = storage_obj_test.count_movies()
    assert len(t_df) == 20
    assert t_count == 20
    assert list(t_df.columns) == MOVIE_COLUMNS
    assert list(t_df["title"]) == expected_titles
    sel_t_df = storage_obj_test.select_columns(['title'], 100)
    t_df_ids = [row['id'] for row in sel_t_df]

  #  offshore = client.get("/movies?limit=100")
  #  assert offshore.status_code == 200
  #  print
  #  offshore_ids = [row["id"] for row in offshore.json()["data"]]
  #  id_range = list(range(1,21))

  #  assert t_df_ids == id_range
  #  assert offshore_ids == id_range
  #  assert t_df_ids == offshore_ids



def test_cache_and_processing(client, uploaded_movies, processing_body):
    # TODO 1: GET /movies with limits 100 and 1.
    # Check 200 and that main.cache.get(limit) equals each response body.
    bodies = {}
    for limit in (100, 1):
        response = client.get(f"/movies?limit={limit}")
        assert response.status_code == 200
        bodies[limit] = response.json()
        assert main.cache.get(limit) == bodies[limit]
    # TODO 2: repeat limit=100 and check the same response.
    repeat = client.get("/movies?limit=100")
    assert repeat.status_code == 200
    assert repeat.json() == bodies[100]
    # TODO 3: POST /movies/process using json=processing_body.
    # Check 200, zero validation removals, and the 20 -> 16 cleaning report.
    # Confirm both old cache entries are None.
    processed = client.post("/movies/process", json=processing_body)
    assert processed.status_code == 200
    report = processed.json()
    
    assert report["validation_rows_removed"] == 0
    assert report['cleaning_report']['rows_before'] == 20
    assert report['cleaning_report']['rows_after'] == 16
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None
    # TODO 4: retrieve again; check total_rows=16 and titles Movie A through Movie P, in order.
    # Check IDs 1 through 16 in the retrieved records.
    # Check that the new response is cached.
    repeat = client.get("/movies?limit=100")
    assert repeat.status_code == 200
    new_report = repeat.json()
    print(new_report)
    assert new_report['total_rows'] == 16
    assert [r["title"] for r in new_report["data"]] == [f"Movie {c}" for c in "ABCDEFGHIJKLMNOP"]
    assert main.cache.get(100) == new_report


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    # TODO 1: GET /movies with limit=100 to populate the cache.
    # Assert 200 and keep the response for comparison.
    initial = client.get("/movies?limit=100")
    assert initial.status_code == 200
    # TODO 2: Use monkeypatch to replace main.storage.select_columns()
    # and main.storage.count_movies() with a function that fails the test
    # if either method is called. 
    def fail(*args, **kwargs):
        pytest.fail("Database was accessed on a cache hit")

    monkeypatch.setattr(main.storage, "select_columns", fail)
    monkeypatch.setattr(main.storage, "count_movies", fail)

    # TODO 3: Repeat the same GET request.
    # Assert 200 and the same response body as the first request.
    second = client.get("/movies?limit=100")
    assert second.status_code == 200
    assert second.json() == initial.json()
