import asyncpg
from aiohttp import web
from models.forum import Forum
from .timer import logger
import time

routes = web.RouteTableDef()


@routes.post('/api/forum/create', expect_handler=web.Request.json)
#@logger
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
        except Exception:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + forum.user})
    async with pool.acquire() as connection:
        result = await connection.fetch(Forum.query_get_forum(forum.slug))
    forum = dict(result[0])
    return web.json_response(status=201, data=forum)


@routes.get('/api/forum/{slug}/details')
#@logger
async def handle_get_details(request):
    slug = request.match_info['slug']
    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch(Forum.query_get_forum(slug))
        if len(result) == 0:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + slug})
        forum = dict(result[0])
        return web.json_response(status=200, data=forum)


@routes.get('/api/forum/{slug}/users')
#@logger
async def handle_get_users(request):
    slug = request.match_info['slug']
    pool = request.app['pool']
    limit = request.rel_url.query.get('limit', False)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', False)
    async with pool.acquire() as connection:
        result = await connection.fetch(Forum.query_get_users(slug, limit=limit, desc=desc, since=since))
        if len(result) == 0:
            result = await connection.fetch("SELECT slug FROM forum WHERE slug = '{}'".format(slug))
            if len(result) == 0:
                return web.json_response(status=404, data={"message": "Can't find forum by slug " + slug})

            return web.json_response(status=200, data=[])
        users = list(map(dict, list(result)))
        return web.json_response(status=200, data=users)


@routes.get('/api/service/status')
#@logger
async def handle_get_status(request):
    pool = request.app['pool']

    async with pool.acquire() as connection:
        result = await connection.fetch('''
			SELECT * FROM 
				(SELECT COUNT(*) AS "forum" FROM forum) AS "f",
				(SELECT COUNT(*) AS "thread" FROM thread) AS "t",
				(SELECT COUNT(*) AS "post" FROM post) AS "p",
				(SELECT COUNT(*) AS "user" FROM users) AS "u"
		''')
        result = dict(result[0])
        return web.json_response(status=200, data={"forum": result['forum'],
                                                   "post": result['post'],
                                                   "thread": result['thread'],
                                                   "user": result['user']})


@routes.post('/api/service/clear')
#@logger
async def handle_get(request):
    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch("TRUNCATE  post, vote, thread, forum_user, forum, users;")
        return web.json_response(status=200)
