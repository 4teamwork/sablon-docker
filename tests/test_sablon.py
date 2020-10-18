import os.path
import pytest
import requests
import shlex
import socket
import subprocess
import time


def test_create_document(sablon, template, context):
    with open(template, 'rb') as template_file, open(context, 'rb') as context_file:
        resp = requests.post(
            sablon, files={'template': template_file, 'context': context_file})

    assert resp.status_code == 200
    assert (
        resp.headers['Content-Type']
        == 'application/vnd.openxmlformats-officedocument.wordprocessing'
    )


def test_convert_without_multipart_request(sablon):
    resp = requests.post(sablon)

    assert resp.status_code == 400
    assert resp.text == 'Multipart request required.'


def test_convert_without_template(sablon):
    resp = requests.post(sablon, files={'context': '{}'})

    assert resp.status_code == 400
    assert resp.text == 'No template or context provided.'


def test_convert_without_context(sablon, template):
    with open(template, 'rb') as template_file:
        resp = requests.post(sablon, files={'template': template_file})

    assert resp.status_code == 400
    assert resp.text == 'No template or context provided.'


def test_convert_with_invalid_msg(sablon):
    resp = requests.post(sablon, files={'template': 'bar', 'context': 'bar'})

    assert resp.status_code == 500
    assert resp.text.startswith('Document creation failed.')


@pytest.fixture(scope="module")
def sablon():
    """Builds the docker image, starts the container and returns its URL.
    """
    context = os.path.dirname(os.path.dirname(__file__))
    run(f'docker build -t sablon:latest {context}')
    port = find_free_port()
    run(f'docker run -d -p {port}:8080 --name sablon sablon:latest')
    wait_until_ready(f'http://localhost:{port}/healthcheck')
    yield f'http://localhost:{port}'
    run('docker stop sablon')
    run('docker rm sablon')


@pytest.fixture(scope="module")
def template():
    return os.path.join(os.path.dirname(__file__), 'template.docx')


@pytest.fixture(scope="module")
def context():
    return os.path.join(os.path.dirname(__file__), 'context.json')


def wait_until_ready(url, timeout=10):
    start = now = time.time()
    while now - start < timeout:
        try:
            requests.get(url)
        except requests.ConnectionError:
            pass
        else:
            return True
        time.sleep(0.1)
        now = time.time()
    return False


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run(cmd):
    args = shlex.split(cmd)
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.fail(proc.stderr, pytrace=False)
