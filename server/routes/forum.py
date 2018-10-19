import asyncpg

from aiohttp import web
from models.forum import Forum

routes = web.RouteTableDef()


@routes.post('/api/forum/create', expect_handler=web.Request.json)
async def handle_forum_create(request):
    data = await request.json()
    forum = Forum(**data)

    pool = request.app['pool']
    async with pool.acquire() as connection:
        try:
            # print('QUERY', forum.query_create_forum())
            await connection.fetch(forum.query_create_forum())
        except asyncpg.exceptions.UniqueViolationError as e:
            result = await connection.fetch(Forum.query_get_forum(forum.slug))
            forum = dict(result[0])
            return web.json_response(status=409, data=forum)
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + forum.user})
    async with pool.acquire() as connection:
        result = await connection.fetch(Forum.query_get_forum(forum.slug))
    forum = dict(result[0])
    return web.json_response(status=201, data=forum)


@routes.get('/api/forum/{slug}/details')
async def handle_get(request):
    slug = request.match_info['slug']
    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch(Forum.query_get_forum(slug))
        if len(result) == 0:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + slug})
        forum = dict(result[0])
        return web.json_response(status=200, data=forum)

@routes.get('/api/forum/{slug}/users')
async def handle_get(request):
    slug = request.match_info['slug']
    pool = request.app['pool']
    limit = request.rel_url.query.get('limit', False)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', False)
    async with pool.acquire() as connection:
        print(Forum.query_get_users(slug, limit=limit, desc=desc, since=since))
        result = await connection.fetch(Forum.query_get_users(slug, limit=limit, desc=desc, since=since))
        if len(result) == 0:
            return web.json_response(status=200, data=[])
        users = list(map(dict, list(result)))
        return web.json_response(status=200, data=users)
