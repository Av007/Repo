from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "mock_response, expected_response", [
        ({"total_count": 0}, {'ok': 'success'}),
        ({"total_count": 1, "items": [{'tags_url': ''}]}, {'ok': 'success'}),
        ({"total_count": 101, "items": [{'tags_url': ''} for _ in range(101)]}, {'ok': 'success'})
    ]
)
@patch("app.requester.get_request")
def test_repo_fetch(fake_httpx, mock_response, expected_response):
    fake_httpx.return_value = mock_response

    response = client.post("/repositories/fetch", params={"count": 1})

    assert response.status_code == 200
    assert response.json() == expected_response

def test_repo_read_empty():
    response = client.get("/repositories")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_read_name_empty():
    response = client.get("/repositories/build")
    assert response.status_code == 200
    assert response.json() == {
        'name': 'build-your-own-x',
        'stars': 328317,
        'tags': [],
        'url': 'https://github.com/codecrafters-io/build-your-own-x'
    }
