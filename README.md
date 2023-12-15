# sablon

A dockerized webservice for creating Microsoft Word documents from templates.

## Description

sablon uses the Ruby Gem [sablon](https://github.com/senny/sablon) for document creation.
It exposes an endpoint for uploading a .docx template and a JSON context.
The webservice is written in Python using the aiohttp web server.

## Usage

To start the webservice just run
```
docker-compose up
```

The .docx template and the JSON context must be uploaded as multipart/form-data
with a parts named `template` and `context`.

Example:

```
curl -F "template=@tests/template.docx" -F "context=@tests/context.json" http://localhost:3000/
```

## Testing

To execute the tests, Python 3.10 with pytest and requests is required.

```
python3.10 -m venv venv
. venv/bin/activate
pip install pytest requests
```

Tests are run by executing pytest:

```
pytest
```
