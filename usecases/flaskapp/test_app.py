import pytest  # noqa: F401

from usecases.flaskapp.app import create_app


@pytest.fixture()
def app():
    app = create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_hello_world(client):
    response = client.get("/")
    assert response.status_code == 405

    response = client.post("/")
    assert response.data == b"<p>Hello, World!</p>"
