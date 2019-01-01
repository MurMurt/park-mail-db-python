from aiohttp import web
from models.forum import Forum
from models.post import Post
from models.thread import Thread
from .timer import logger
import time

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

    pool = request.app['pool']
    thread_id = None
    async with pool.acquire() as connection:
        try:
            result = await connection.fetch(thread.query_create_thread())
            thread_id = result[0]['id']
        except Exception as e:
            async with pool.acquire() as connection2:
                # print("QUERY", Thread.query_get_thread_by_slug(data['slug']))
                res = await connection2.fetch(Thread.query_get_thread_by_slug(data['slug']))
                if len(res) == 0:
                    return web.json_response(status=404, data={})
                thread = dict(res[0])
                thread['created'] = thread['created'].astimezone().isoformat()
                return web.json_response(status=409, data=thread)

        else:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            thread = dict(res[0])

            thread['created'] = thread['created'].astimezone().isoformat()
            # thread['created'] = str(thread['created'])
            if thread['slug'] == 'NULL':
                thread.pop('slug')

            return web.json_response(status=201, data=thread)


@routes.get('/api/forum/{slug}/threads')
@logger
async def handle_get(request):
    ts = time.time()

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
            item['created'] = item['created'].astimezone().isoformat()
    # print('%r  %2.2f ms' % (__name__, time.time() - ts))
    return web.json_response(status=200, data=data)


@routes.get('/api/thread/{slug_or_id}/details')
@logger
async def handle_get_details(request):
    thread_slug_or_id = request.match_info['slug_or_id']
    pool = request.app['pool']

# TODO: rewrite
    ts = time.time()

    if not thread_slug_or_id.isdigit():
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_by_slug(thread_slug_or_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            data = dict(res[0])
            data['created'] = data['created'].astimezone().isoformat()

            # print("QUERY: ", Thread.query_get_thread_by_slug(thread_slug_or_id))
            # print('%r  %2.2f ms' % (__name__, time.time() - ts))

            return web.json_response(status=200, data=data)
    else:
        thread_id = thread_slug_or_id
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            data = dict(res[0])
            data['created'] = data['created'].astimezone().isoformat()

            # print("QUERY: ", Thread.query_get_thread_by_id(thread_id))
            # print('%r  %2.2f ms' % (__name__, time.time() - ts))
            return web.json_response(status=200, data=data)



@routes.get('/api/thread/{slug_or_id}/posts')
@logger
async def handle_get_posts(request):
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

        result = await connection.fetch(Post.query_get_posts(thread_id, since, sort, desc, limit))


        # print(type(result), len(result))
        # if len(result) == 0:
        #     return web.json_response(status=200, data=[])
        data = list(map(dict, list(result)))
        # print('Q:', len(result), len(data), Post.query_get_posts(thread_id, since, sort, desc, limit))
        for item in data:
            item['created'] = item['created'].astimezone().isoformat()
        # print(len(data), len(res))
        tm = (time.time() - ts) * 1000
        # print('%r  %2.2f ms' % (__name__, tm))
        # if sort == 'parent_tree':
        #     print('Q: ', Post.query_get_posts(thread_id, since, sort, desc, limit))
        return web.json_response(status=200, data=data)


@routes.post('/api/thread/{slug_or_id}/details', expect_handler=web.Request.json)
@logger
async def handle_thread_update(request):
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
