import psycopg2
from psycopg2 import extras, errorcodes
from aiohttp import web
from models.post import Post
from models.thread import Thread
from .timer import logger, DEBUG
import time


routes = web.RouteTableDef()


@routes.post('/api/thread/{slug}/create', expect_handler=web.Request.json)
@logger
async def handle_posts_create(request):
    data = await request.json()
    thread_slug_or_id = request.match_info['slug']

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(Thread.query_get_thread_forum(thread_slug_or_id))
    result = cursor.fetchone()

    if not result:
        connection_pool.putconn(connection)
        return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})

    thread_id = result['id']
    forum = result['forum']

    if len(data) == 0:
        connection_pool.putconn(connection)
        return web.json_response(status=201, data=[])

    result = None
    try:
        cursor.execute(Post.query_create_post(thread_id, data))
        result = cursor.fetchall()
        connection.commit()
    except psycopg2.Error as e:
        connection.rollback()
        error = psycopg2.errorcodes.lookup(e.pgcode)
        connection_pool.putconn(connection)

        #     TODO: 2 исключения
        return web.json_response(status=409, data={"message": "Can't find user with id #42\n"})
        # return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
    else:
        connection_pool.putconn(connection)
        for i in range(len(result)):
            data[i]['created'] = result[i]['created'].astimezone().isoformat()
            data[i]['id'] = result[i]['id']
            data[i]['forum'] = forum
            data[i]['thread'] = int(thread_id)
        return web.json_response(status=201, data=data)



    # if not thread_slug_or_id.isdigit():
    #     async with pool.acquire() as connection:
    #         res = await connection.fetch(Thread.query_get_thread_id(thread_slug_or_id))
    #         if len(res) == 0:
    #             return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
    #         thread_id = (res[0]['id'])
    #         forum = res[0]['forum']
    # else:
    #     thread_id = thread_slug_or_id
    #     async with pool.acquire() as connection:
    #         res = await connection.fetch(Thread.query_get_thread_forum(thread_id))
    #         if len(res) == 0:
    #             return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
    #         forum = res[0]['forum']
    #
    # async with pool.acquire() as connection:
    #     if len(data) == 0:
    #         return web.json_response(status=201, data=[])
    #     try:
    #         res = await connection.fetch(Post.query_create_post(thread_id, data))
    #     except asyncpg.exceptions.NotNullViolationError:
    #         return web.json_response(status=409, data={"message": "Can't find user with id #42\n"})
    #     except Exception as e:
    #         return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
    #     else:
    #         for i in range(len(res)):
    #             data[i]['created'] = res[i]['created'].astimezone().isoformat()
    #             data[i]['id'] = res[i]['id']
    #             data[i]['forum'] = forum
    #             data[i]['thread'] = int(thread_id)
    #         return web.json_response(status=201, data=data)
    # return web.json_response(status=201, data=[])


@routes.get('/api/post/{id}/details', expect_handler=web.Request.json)
@logger
async def handle_post_details(request):
    ts = time.time()
    id = request.match_info['id']
    pool = request.app['pool']
    related = request.rel_url.query.get('related', False)

    async with pool.acquire() as connection:
        result = await connection.fetch(Post.query_get_post_details(id))
        if len(result) == 0:
            return web.json_response(status=404, data={"message": "Can't find post by slug " + str(id)})

        post = dict(result[0])
        result = None

        result = {
            "author": post['nickname'],
            "created": post['post_created'].astimezone().isoformat(),
            "forum": post['forum'],
            "id": post['post_id'],
            "message": post['post_message'],
            "thread": post['thread_id'],
            "isEdited": post['is_edited'],
            "parent": post['parent'] if post['parent'] != int(id) else 0,
        }
        if not related:
            te = time.time()
            if DEBUG:
                print('%r  %2.2f ms' % ('/api/post/{}/details'.format(id), (te - ts) * 1000))
            return web.json_response(status=200, data={'post': result})
        else:
            user = False
            thread = False
            forum = False
            related = related.split(',')
            if 'user' in related:
                user = {
                    "about": post['about'],
                    "email": post['email'],
                    "fullname": post['fullname'],
                    "nickname": post['nickname'],
                }
            if 'thread' in related:
                thread = {
                    "author": post['t_author'],
                    "created": post['t_created'].astimezone().isoformat(),
                    "id": post['t_id'],
                    "message": post['t_message'],
                    "slug": post['t_slug'],
                    "forum": post['forum'],
                    "title": post['t_title'],
                    "votes": post['votes'],
                }
            if 'forum' in related:
                forum = {
                    "posts": post['posts'],
                    "slug": post['f_slug'],
                    "threads": post['threads'],
                    "title": post['f_title'],
                    "user": post['f_nick'],
                }

            data = {'post': result}
            if user:
                data['author'] = user
            if thread:
                data['thread'] = thread
            if forum:
                data['forum'] = forum

            te = time.time()
            if DEBUG:
                print('%r  %2.2f ms' % ('/api/post/{}/details'.format(id), (te - ts) * 1000))
            return web.json_response(status=200, data=data)


@routes.post('/api/post/{id}/details', expect_handler=web.Request.json)
@logger
async def handle_posts_details_post(request):
    return web.json_response(status=404, data={"message": "Can't find user by nickname "})

    id = request.match_info['id']
    data = await request.json()
    message = data.get('message', False)

    pool = request.app['pool']
    async with pool.acquire() as connection:
        try:
            if message:
                result = await connection.fetch("SELECT message FROM post WHERE id = {id}".format(id=id))
                if len(result) != 0 and dict(result[0])['message'] != message:

                    result = await connection.fetch("UPDATE post SET message = '{message}', is_edited = TRUE "
                                            "WHERE id = {id}".format(message=message, id=id))
        except Exception as e:
            return web.json_response(status=404, data={"message": "Can't find post by slug " + str(id)})
        else:
            async with pool.acquire() as connection:
                result = await connection.fetch(Post.query_get_post_details(id))
                if len(result) == 0:
                    return web.json_response(status=404, data={"message": "Can't find post by slug " + str(id)})

                post = dict(result[0])
                result = None
                result = {
                    "author": post['nickname'],
                    "created": post['post_created'].astimezone().isoformat(),
                    "forum": post['forum'],
                    "id": post['post_id'],
                    "message": post['post_message'],
                    "thread": post['thread_id'],
                }

                return web.json_response(status=200, data={
                    "author": post['nickname'],
                    "created": post['post_created'].astimezone().isoformat(),
                    "forum": post['forum'],
                    "id": post['post_id'],
                    "message": post['post_message'],
                    "thread": post['thread_id'],
                    "isEdited": post['is_edited'],
                })
