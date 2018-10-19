from aiohttp import web

from models.forum import Forum
from models.post import Post
from models.thread import Thread


routes = web.RouteTableDef()


@routes.post('/api/thread/{slug}/create', expect_handler=web.Request.json)
async def handle_posts_create(request):
    data = await request.json()

    if len(data) == 0:
        return web.json_response(status=201, data=[])

    pool = request.app['pool']
    thread_slug_or_id = request.match_info['slug']

    if not thread_slug_or_id.isdigit():
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_id(thread_slug_or_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            thread_id = (res[0]['id'])
            forum = res[0]['forum']
    else:
        thread_id = thread_slug_or_id
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_forum(thread_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
            forum = res[0]['forum']

    async with pool.acquire() as connection:
        # print('QUERY', Post.query_create_post(thread_id, data))
        try:
            print('QUERY ', Post.query_create_post(thread_id, data))
            res = await connection.fetch(Post.query_create_post(thread_id, data))
        except Exception as e:
            print('ERROR post', type(e), e)
        else:
            # print(res)
            for i in range(len(res)):
                data[i]['created'] = str(res[i]['created'].astimezone().isoformat())
                data[i]['id'] = res[i]['id']
                data[i]['forum'] = forum
                data[i]['thread'] = int(thread_id)

            return web.json_response(status=201, data=data)
    return web.json_response(status=201, data=[])


