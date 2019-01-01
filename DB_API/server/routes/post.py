import asyncpg
from aiohttp import web
from models.post import Post
from models.thread import Thread
from .timer import logger, timeit
import time


routes = web.RouteTableDef()


@routes.post('/api/thread/{slug}/create', expect_handler=web.Request.json)
@logger
async def handle_posts_create(request):
    data = await request.json()

    # if len(data) == 0:
    #     return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})

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
        if len(data) == 0:
            return web.json_response(status=201, data=[])
        try:
            # print('QUERY ', Post.query_create_post(thread_id, data))
            res = await connection.fetch(Post.query_create_post(thread_id, data))
        except asyncpg.exceptions.NotNullViolationError:
            return web.json_response(status=409, data={"message": "Can't find user with id #42\n"})
        except Exception as e:
            # print('ERROR post', type(e), e)
            return web.json_response(status=404, data={"message": "Can't find user with id #42\n"})
        else:
            await connection.fetch("UPDATE forum SET posts = posts+{count} WHERE slug = '{forum}'".format(forum=forum, count=len(res)))
            # print(res)
            for i in range(len(res)):
                data[i]['created'] = res[i]['created'].astimezone().isoformat()
                data[i]['id'] = res[i]['id']
                data[i]['forum'] = forum
                data[i]['thread'] = int(thread_id)

            return web.json_response(status=201, data=data)
    # return web.json_response(status=201, data=[])


@routes.get('/api/post/{id}/details', expect_handler=web.Request.json)
@logger
# @timeit
async def handle_post_details(request):
    id = request.match_info['id']
    pool = request.app['pool']
    related = request.rel_url.query.get('related', False)

    async with pool.acquire() as connection:
        result = await connection.fetch(Post.query_get_post_details(id))
        if len(result) == 0:
            return web.json_response(status=404, data={"message": "Can't find post by slug " + str(id)})

        post = dict(result[0])

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

            return web.json_response(status=200, data=data)


@routes.post('/api/post/{id}/details', expect_handler=web.Request.json)
@logger
async def handle_posts_create(request):
    id = request.match_info['id']
    data = await request.json()
    message = data.get('message', False)

    pool = request.app['pool']
    async with pool.acquire() as connection:
        try:
            # print(Post.query_get_post_details(id))
            if message:
                result = await connection.fetch("SELECT message FROM post WHERE id = {id}".format(id=id))
                if len(result) != 0 and dict(result[0])['message'] != message:

                    result = await connection.fetch("UPDATE post SET message = '{message}', is_edited = TRUE "
                                            "WHERE id = {id}".format(message=message, id=id))
        except Exception as e:
            # print('ERROR', type(e), e)
            return web.json_response(status=404, data={"message": "Can't find post by slug " + str(id)})
        else:
            async with pool.acquire() as connection:
                # print(Post.query_get_post_details(id))
                # print("GET POST DETAILS", Post.query_get_post_details(id))
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
                # print('RES', post)
                return web.json_response(status=200, data={
                    "author": post['nickname'],
                    "created": post['post_created'].astimezone().isoformat(),
                    "forum": post['forum'],
                    "id": post['post_id'],
                    "message": post['post_message'],
                    "thread": post['thread_id'],
                    "isEdited": post['is_edited'],
                })
