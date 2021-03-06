from aiohttp import web
from models.thread import Thread
from models.vote import Vote
from .timer import logger


routes = web.RouteTableDef()


@routes.post('/api/thread/{slug_or_id}/vote', expect_handler=web.Request.json)
#@logger
async def handle_posts_create(request):
    data = await request.json()

    pool = request.app['pool']
    thread_slug_or_id = request.match_info['slug_or_id']
    thread_id = thread_slug_or_id

    if not thread_slug_or_id.isdigit():
        async with pool.acquire() as connection:
            res = await connection.fetch(Thread.query_get_thread_id(thread_slug_or_id))
            if len(res) == 0:
                return web.json_response(status=404, data={"message": "Can't find thread with id #{}\n".format(thread_slug_or_id)})
            thread_id = res[0]['id']
    vote = Vote(**data, thread_id=thread_id)

    async with pool.acquire() as connection:
        try:
            await connection.fetch(vote.query_vote_create())
        except Exception:
            return web.json_response(status=404, data={"message": "Can't find thread by id "})
        else:
            res = await connection.fetch(Thread.query_get_thread_by_id(thread_id))
            data = dict(res[0])
            data['created'] = data['created'].astimezone().isoformat()
            return web.json_response(status=200, data=data)
