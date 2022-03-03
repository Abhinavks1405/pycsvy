import pytest


@pytest.fixture
def data_path():
    from pathlib import Path

    return Path(__file__).parent / "data.csvy"


@pytest.fixture
def data_comment_path():
    from pathlib import Path

    return Path(__file__).parent / "data_comment.csvy"
