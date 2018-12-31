from aiohttp import web
from models.forum import Forum
from models.post import Post
from models.thread import Thread
from .timer import logger, DEBUG
import time
import psycopg2
from psycopg2 import extras

routes = web.RouteTableDef()


@routes.post('/api/forum/{slug}/create', expect_handler=web.Request.json)
@logger
async def handle_forum_create(request):

    data = await request.json()
    forum = request.match_info['slug']
    forum_slug = data.get('forum', False)
    if not forum_slug:
        thread = Thread(**data, forum=forum)
    else:
        thread = Thread(**data)

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    thread_id = None
    try:
        cursor.execute(thread.query_create_thread())
        thread_id = cursor.fetchone()['id']
        connection.commit()
    except psycopg2.Error as e:
        connection.rollback()
        cursor.execute(Thread.query_get_thread_by_slug(data['slug']))
        result = cursor.fetchone()
        connection_pool.putconn(connection)
        if result:
            result['created'] = result['created'].astimezone().isoformat()
            return web.json_response(status=409, data=result)
        else:
            return web.json_response(status=404, data={})
    else:
        cursor.execute(Thread.query_get_thread_by_id(thread_id))
        result = cursor.fetchone()
        result['created'] = result['created'].astimezone().isoformat()
        if result['slug'] == 'NULL':
            result.pop('slug')

        connection_pool.putconn(connection)
        return web.json_response(status=201, data=result)


@routes.get('/api/forum/{slug}/threads')
@logger
async def handle_get(request):

    forum_slug = request.match_info['slug']
    limit = request.rel_url.query.get('limit', 0)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', 0)

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(Thread.query_get_threads(forum_slug, limit, desc, since))
    result = cursor.fetchall()
    if not result:
        cursor.execute(Forum.query_get_forum(forum_slug))
        result = cursor.fetchall()
        connection_pool.putconn(connection)
        if result:
            return web.json_response(status=200, data=[])
        return web.json_response(status=404, data={"message": "Can't find forum by slug " + forum_slug})

    connection_pool.putconn(connection)
    for item in result:
        item['created'] = item['created'].astimezone().isoformat()

    return web.json_response(status=200, data=result)

    # async with pool.acquire() as connection:
    #     result = await connection.fetch(Thread.query_get_threads(forum_slug, limit, desc, since))
    #     if len(result) == 0:
    #         result = await connection.fetch(Forum.query_get_forum(forum_slug))
    #         if len(result) == 0:
    #             return web.json_response(status=404, data={"message": "Can't find forum by slug " + forum_slug})
    #         return web.json_response(status=200, data=[])
    #
    #     data = list(map(dict, result))
    #     for item in data:
    #         item['created'] = item['created'].astimezone().isoformat()
    #
    # if DEBUG:
    #     print('%r  %2.2f ms' % ('/api/forum/{}/threads'.format(forum_slug), (time.time() - ts) * 1000))
    #
    # return web.json_response(status=200, data=data)


@routes.get('/api/thread/{slug_or_id}/details')
@logger
async def handle_get_details(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    ts = time.time()

    thread_slug_or_id = request.match_info['slug_or_id']
    pool = request.app['pool']

# TODO: rewrite
    if not thread_slug_or_id.isdigit():
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_by_slug(thread_slug_or_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            data = dict(res[0])
            data['created'] = data['created'].astimezone().isoformat()

            if DEBUG:
                print('%r  %2.2f ms' % ('/api/thread/{}/details'.format(thread_slug_or_id), (time.time() - ts) * 1000))
            return web.json_response(status=200, data=data)
    else:
        thread_id = thread_slug_or_id
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            data = dict(res[0])
            data['created'] = data['created'].astimezone().isoformat()

            if DEBUG:
                print('%r  %2.2f ms' % ('/api/thread/{}/details'.format(thread_slug_or_id), (time.time() - ts) * 1000))
            return web.json_response(status=200, data=data)



@routes.get('/api/thread/{slug_or_id}/posts')
@logger
async def handle_get_posts(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    ts = time.time()

    thread_slug_or_id = request.match_info['slug_or_id']
    limit = request.rel_url.query.get('limit', False)
    desc = request.rel_url.query.get('desc', False)
    since = request.rel_url.query.get('since', False)
    sort = request.rel_url.query.get('sort', 'flat')

    pool = request.app['pool']
    thread_id = thread_slug_or_id

    if not thread_slug_or_id.isdigit():
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_id(thread_slug_or_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            data = dict(res[0])
            thread_id = data['id']
    else:
        thread_id = thread_slug_or_id
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
    async with pool.acquire() as connection:
        # print('QUERY ', Post.query_get_posts(thread_id, since, sort, desc, limit))
        res = await connection.fetch(
            Post.query_get_posts(thread_id, since, sort, desc, limit))
        if len(res) == 0:
            return web.json_response(status=200, data=[])
        data = list(map(dict, list(res)))
        for item in data:
            item['created'] = item['created'].astimezone().isoformat()

        if DEBUG:
            print('%r  %2.2f ms' % ('/api/thread/{}/posts'.format(thread_slug_or_id), (time.time() - ts) * 1000))
        return web.json_response(status=200, data=data)


@routes.post('/api/thread/{slug_or_id}/details', expect_handler=web.Request.json)
@logger
async def handle_thread_update(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    data = await request.json()
    thread_slug_or_id = request.match_info['slug_or_id']
    message = data.get('message', False)
    title = data.get('title', False)
    pool = request.app['pool']
    thread_id = thread_slug_or_id

    if not thread_slug_or_id.isdigit():
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_id(thread_slug_or_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #41\n"})
            data = dict(res[0])
            thread_id = data['id']
    else:
        thread_id = thread_slug_or_id

    async with pool.acquire() as connection:
        if not title and not message:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            thread = dict(res[0])

            thread['created'] = thread['created'].astimezone().isoformat()
            # thread['created'] = str(thread['created'])
            if thread['slug'] == 'NULL':
                thread.pop('slug')

            return web.json_response(status=200, data=thread)

        try:
            await connection.fetch(Thread.query_update_thread(thread_id, message, title))

        except Exception as e:
            # print('ERROR', type(e), e)
            return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
        else:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})

            thread = dict(res[0])

            thread['created'] = thread['created'].astimezone().isoformat()
            # thread['created'] = str(thread['created'])
            if thread['slug'] == 'NULL':
                thread.pop('slug')

            return web.json_response(status=200, data=thread)
