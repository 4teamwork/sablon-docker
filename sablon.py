#!/usr/bin/env python3
"""
sablon server

A tiny aiohttp based web server that wraps the sablon Ruby script.
It expects a multipart/form-data upload containing a .docx document with the
name template and a JSON part named context containing variable values.
"""
from aiohttp import web
import asyncio
import logging
import os.path
import tempfile

CHUNK_SIZE = 65536

logger = logging.getLogger('sablon')


async def sablon(request):

    form_data = {}
    temp_dir = None

    if not request.content_type == 'multipart/form-data':
        logger.info(
            'Bad request. Received content type %s instead of multipart/form-data.',
            request.content_type,
        )
        return web.Response(status=400, text="Multipart request required.")

    reader = await request.multipart()

    with tempfile.TemporaryDirectory() as temp_dir:
        while True:
            part = await reader.next()

            if part is None:
                break

            if part.name == 'template':
                form_data['template'] = await save_part_to_file(part, temp_dir)
            elif part.name == 'context':
                form_data['context'] = await part.text()

        if 'context' in form_data and 'template' in form_data:
            outfilename = os.path.join(temp_dir, 'output.docx')

            proc, stdout, stderr = await run(
                'sablon', form_data['template'], outfilename,
                input=form_data['context'].encode('utf8'),
                timeout=request.app['config']['sablon_call_timeout'],
            )

            if proc is not None and proc.returncode == 0:
                response = web.StreamResponse(
                    status=200,
                    reason='OK',
                    headers={
                        'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessing',
                        'Content-Disposition': 'attachment; filename="output.docx"',
                    },
                )
                await response.prepare(request)

                with open(outfilename, 'rb') as outfile:
                    while True:
                        data = outfile.read(CHUNK_SIZE)
                        if not data:
                            break
                        await response.write(data)

                await response.write_eof()
                return response
            else:
                if proc is None:
                    logger.error('Document creation failed.')
                    return web.Response(
                        status=500, text="Document creation failed.")
                else:
                    logger.error('Document creation failed. %s', stderr)
                    return web.Response(
                        status=500, text=f"Document creation failed. {stderr}")

        logger.info('Bad request. No template or context provided.')
        return web.Response(status=400, text="No template or context provided.")


async def save_part_to_file(part, directory):
    filename = os.path.join(directory, part.filename)
    with open(os.path.join(directory, filename), 'wb') as file_:
        while True:
            chunk = await part.read_chunk(CHUNK_SIZE)
            if not chunk:
                break
            file_.write(chunk)
    return filename


async def healthcheck(request):
    return web.Response(status=200, text="OK")


async def run(*cmd, input=None, timeout=30, encoding='utf8'):
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=input), timeout=timeout)
    except asyncio.exceptions.TimeoutError:
        logger.error('Calling %s timed out.', cmd)
        return None
    except Exception:
        logger.exception('Calling %s failed', cmd)
        return None

    return proc, stdout.decode(encoding), stderr.decode(encoding)


def get_config():
    config = {}

    try:
        sablon_call_timeout = int(os.environ.get('SABLON_CALL_TIMEOUT', '30'))
    except (ValueError, TypeError):
        sablon_call_timeout = 30
    config['sablon_call_timeout'] = sablon_call_timeout

    return config


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        level=logging.INFO,
    )
    app = web.Application()
    app['config'] = get_config()
    logger.info('Using config=%s', app['config'])
    app.add_routes([web.post('/', sablon)])
    app.add_routes([web.get('/healthcheck', healthcheck)])
    web.run_app(app)
