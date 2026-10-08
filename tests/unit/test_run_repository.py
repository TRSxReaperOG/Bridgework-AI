import sqlite3

import pytest

from bridgework.repositories import RunNotFoundError, RunRepository


@pytest.fixture
def repo(tmp_path):
    return RunRepository(tmp_path / "runs.db")


def test_runs_table_has_the_planned_columns(tmp_path):
    db_path = tmp_path / "runs.db"
    RunRepository(db_path)
    with sqlite3.connect(db_path) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(runs)")]
    assert columns == ["run_id", "stage", "state_json", "created_at", "updated_at"]


def test_create_then_get_returns_the_same_run(repo):
    run_id = repo.create_run("research", {"feature_idea": "alert suppression"})
    run = repo.get_run(run_id)
    assert run.run_id == run_id
    assert run.stage == "research"
    assert run.state == {"feature_idea": "alert suppression"}
    assert run.created_at == run.updated_at


def test_create_without_state_starts_empty(repo):
    assert repo.get_run(repo.create_run("research")).state == {}


def test_each_run_gets_a_unique_id(repo):
    assert repo.create_run("research") != repo.create_run("research")


def test_get_unknown_run_returns_none(repo):
    assert repo.get_run("does-not-exist") is None


def test_update_stage_keeps_state_and_moves_updated_at(repo):
    run_id = repo.create_run("research", {"a": 1})
    repo.update_run(run_id, stage="codebase")
    run = repo.get_run(run_id)
    assert run.stage == "codebase"
    assert run.state == {"a": 1}
    assert run.updated_at >= run.created_at


def test_update_state_keeps_stage(repo):
    run_id = repo.create_run("research", {"a": 1})
    repo.update_run(run_id, state={"a": 2, "nested": {"sources": ["https://example.com"]}})
    run = repo.get_run(run_id)
    assert run.stage == "research"
    assert run.state == {"a": 2, "nested": {"sources": ["https://example.com"]}}


def test_update_does_not_touch_other_runs(repo):
    first = repo.create_run("research", {"n": 1})
    second = repo.create_run("research", {"n": 2})
    repo.update_run(first, stage="synthesis", state={"n": 10})
    assert repo.get_run(second).stage == "research"
    assert repo.get_run(second).state == {"n": 2}


def test_update_unknown_run_raises(repo):
    with pytest.raises(RunNotFoundError):
        repo.update_run("does-not-exist", stage="codebase")


def test_update_with_nothing_to_change_raises(repo):
    run_id = repo.create_run("research")
    with pytest.raises(ValueError):
        repo.update_run(run_id)


def test_runs_survive_reopening_the_database(tmp_path):
    db_path = tmp_path / "runs.db"
    run_id = RunRepository(db_path).create_run("research", {"saved": True})
    assert RunRepository(db_path).get_run(run_id).state == {"saved": True}


def test_database_folder_is_created_if_missing(tmp_path):
    db_path = tmp_path / "nested" / "folder" / "runs.db"
    RunRepository(db_path)
    assert db_path.exists()


def test_values_are_stored_safely_not_as_sql(repo):
    run_id = repo.create_run("research'; DROP TABLE runs; --", {"q": "x'); DELETE FROM runs; --"})
    assert repo.get_run(run_id).stage == "research'; DROP TABLE runs; --"
