# import asyncpg
from aiohttp import web
from models.forum import Forum
from .timer import logger, DEBUG
import time
import psycopg2
from psycopg2 import extras
from psycopg2 import errorcodes


routes = web.RouteTableDef()


@routes.post('/api/forum/create', expect_handler=web.Request.json)
@logger
async def handle_forum_create(request):

    data = await request.json()
    forum = Forum(**data)

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute(forum.query_create_forum())
        connection.commit()
    except psycopg2.Error as e:
        connection.rollback()
        error = psycopg2.errorcodes.lookup(e.pgcode)
        if error == 'UNIQUE_VIOLATION':
            cursor.execute(Forum.query_get_forum(forum.slug))
            result = cursor.fetchone()
            connection_pool.putconn(connection)
            return web.json_response(status=409, data=result)

        if error == 'FOREIGN_KEY_VIOLATION':
            connection_pool.putconn(connection)
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + forum.user})
        else:
            connection_pool.putconn(connection)
            return web.json_response(status=404, data={"message": str(e), "code": error})

    else:
        cursor.execute(Forum.query_get_forum(forum.slug))
        result = cursor.fetchone()
        connection_pool.putconn(connection)
        return web.json_response(status=201, data=result)


@routes.get('/api/forum/{slug}/details')
@logger
async def handle_get(request):

    slug = request.match_info['slug']

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(Forum.query_get_forum(slug))

    result = cursor.fetchone()
    connection_pool.putconn(connection)
    if result:
        return web.json_response(status=200, data=result)
    else:
        return web.json_response(status=404, data={"message": "Can't find user by nickname " + slug})



@routes.get('/api/forum/{slug}/users')
@logger
async def handle_get(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    ts = time.time()
    slug = request.match_info['slug']
    pool = request.app['pool']
    limit = request.rel_url.query.get('limit', False)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', False)
    async with pool.acquire() as connection:
        # print(Forum.query_get_users(slug, limit=limit, desc=desc, since=since))
        result = await connection.fetch(Forum.query_get_users(slug, limit=limit, desc=desc, since=since))
        if len(result) == 0:
            result = await connection.fetch("SELECT slug FROM forum WHERE slug = '{}'".format(slug))
            if len(result) == 0:
                return web.json_response(status=404, data={"message": "Can't find forum by slug " + slug})
            te = time.time()
            if DEBUG:
                print('%r  %2.2f ms' % ('/api/forum/{}/users'.format(slug), (te - ts) * 1000))
            return web.json_response(status=200, data=[])
        users = list(map(dict, list(result)))
        te = time.time()
        if DEBUG:
            print('%r  %2.2f ms' % ('/api/forum/{}/users'.format(slug), (te - ts) * 1000))
        return web.json_response(status=200, data=users)


@routes.get('/api/service/status')
@logger
async def handle_get(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    ts = time.time()
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
        te = time.time()
        if DEBUG:
            print('%r  %2.2f ms' % ('/api/service/status', (te - ts) * 1000))

        return web.json_response(status=200, data={"forum": result['forum'],
                                                   "post": result['post'],
                                                   "thread": result['thread'],
                                                   "user": result['user']})


@routes.post('/api/service/clear')
@logger
async def handle_get(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    ts = time.time()
    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch("TRUNCATE  post, vote, thread, forum, users;")
        te = time.time()
        if DEBUG:
            print('%r  %2.2f ms' % ('/api/service/clear', (te - ts) * 1000))

        return web.json_response(status=200)
