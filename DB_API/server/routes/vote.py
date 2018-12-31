from aiohttp import web
from models.thread import Thread
from models.vote import Vote
from .timer import logger
import psycopg2
from psycopg2 import extras, errorcodes


routes = web.RouteTableDef()


@routes.post('/api/thread/{slug_or_id}/vote', expect_handler=web.Request.json)
@logger
async def handle_vote_create(request):
    data = await request.json()
    thread_slug_or_id = request.match_info['slug_or_id']
    thread_id = thread_slug_or_id

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if not thread_slug_or_id.isdigit():
        cursor.execute(Thread.query_get_thread_id(thread_slug_or_id))
        result = cursor.fetchone()
        if not result:
            connection_pool.putconn(connection)
            return web.json_response(status=404,
                                     data={"message": "Can't find thread with id #{}\n".format(thread_slug_or_id)})
        thread_id = result['id']
    vote = Vote(**data, thread_id=thread_id)

    try:
        cursor.execute(vote.query_vote_create())
        connection.commit()
    except psycopg2.Error:
        connection_pool.putconn(connection)
        return web.json_response(status=404, data={"message": "Can't find thread by id "})
    else:
        cursor.execute(Thread.query_get_thread_by_id(thread_id))
        result = cursor.fetchone()
        data = result
        data['created'] = data['created'].astimezone().isoformat()
        connection_pool.putconn(connection)
        return web.json_response(status=200, data=data)
