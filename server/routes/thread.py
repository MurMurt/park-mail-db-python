import asyncpg

from aiohttp import web

from models.forum import Forum
from models.thread import Thread
from datetime import datetime

routes = web.RouteTableDef()


@routes.post('/api/forum/{slug}/create', expect_handler=web.Request.json)
async def handle_forum_create(request):
    data = await request.json()
    forum = request.match_info['slug']
    thread = Thread(**data)

    pool = request.app['pool']
    async with pool.acquire() as connection:
        try:
            res = await connection.fetch(thread.query_create_thread())
            id = (res[0]['id'])
        except Exception as e:
            print('ERROR', type(e), e)

    data = thread.get_data()
    if data['slug'] == 'NULL':
        data.pop('slug')
    else:
        data['slug'] = data['slug'][1:-1]
    if data['created'] == 'NULL':
        data.pop('created')
    data['id'] = id
    return web.json_response(status=201, data=data)


@routes.get('/api/forum/{slug}/threads')
async def handle_get(request):
    forum_slug = request.match_info['slug']
    limit = request.rel_url.query.get('limit', 0)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', 0)

    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch(Thread.query_get_threads(forum_slug, limit, desc, since))
        if len(result) == 0:
            result = await connection.fetch(Forum.query_get_forum(forum_slug))
            if len(result) == 0:
                return web.json_response(status=404, data={"message": "Can't find forum by slug " + forum_slug})
            return web.json_response(status=200, data=[])

        data = list(map(dict, result))
        for item in data:
            # print(item['created'])
            item['created'] = item['created'].isoformat()

    return web.json_response(status=200, data=data)
