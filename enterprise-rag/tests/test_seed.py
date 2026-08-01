from app.seed import seed_demo_dataset


def test_demo_seed_is_idempotent():
    first = seed_demo_dataset()
    second = seed_demo_dataset()

    assert first["sql_records"] == second["sql_records"] == 4
    assert second["users_created"] == 0
    assert second["pdf_chunks_indexed"] == 0
