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
async def handle_get_users(request):
    slug = request.match_info['slug']
    limit = request.rel_url.query.get('limit', False)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', False)

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(Forum.query_get_users(slug, limit=limit, desc=desc, since=since))
    users = cursor.fetchall()

    if not users:
        cursor.execute("SELECT slug FROM forum WHERE slug = '{}'".format(slug))  # TODO: check
        result = cursor.fetchone()
        connection_pool.putconn(connection)
        if not result:
            return web.json_response(status=404, data={"message": "Can't find forum by slug " + slug})
        return web.json_response(status=200, data=[])
    connection_pool.putconn(connection)
    return web.json_response(status=200, data=users)


@routes.get('/api/service/status')
@logger
async def handle_get(request):
    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute('''
			SELECT * FROM 
				(SELECT COUNT(*) AS "forum" FROM forum) AS "f",
				(SELECT COUNT(*) AS "thread" FROM thread) AS "t",
				(SELECT COUNT(*) AS "post" FROM post) AS "p",
				(SELECT COUNT(*) AS "user" FROM users) AS "u"
		''')
    result = cursor.fetchone()
    connection_pool.putconn(connection)
    return web.json_response(status=200, data=result)


@routes.post('/api/service/clear')
@logger
async def handle_get(request):
    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("TRUNCATE  post, vote, thread, forum, users;")
    connection.commit()
    connection_pool.putconn(connection)
    return web.json_response(status=200)
