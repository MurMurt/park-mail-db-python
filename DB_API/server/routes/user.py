from aiohttp import web
from models.user import User
from .timer import logger, DEBUG
import time
import psycopg2
from psycopg2 import extras

routes = web.RouteTableDef()


@routes.post('/api/user/{nickname}/create', expect_handler=web.Request.json)
@logger
async def handle_user_create(request):
    data = await request.json()
    user = User(**data, nickname=request.match_info['nickname'])

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute(user.query_create_user())
        connection.commit()
    except psycopg2.Error:
        connection.rollback()
        cursor.execute(user.query_get_same_users())
        result = cursor.fetchall()

        connection_pool.putconn(connection)
        return web.json_response(status=409, data=list(map(dict, result)))

    connection_pool.putconn(connection)
    return web.json_response(status=201, data=user.get_data())


@routes.get('/api/user/{nickname}/profile')
@logger
async def handle_get(request):

    nickname = request.match_info['nickname']
    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(User.query_get_user(nickname))
    result = cursor.fetchall()

    connection_pool.putconn(connection)
    if len(result) == 0:
        return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})
    return web.json_response(status=200, data=dict(result[0]))


@routes.post('/api/user/{nickname}/profile', expect_handler=web.Request.json)
@logger
async def handle_user_update(request):

    data = await request.json()
    nickname = request.match_info['nickname']

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute(User.query_update_user(**data, nickname=nickname))
        connection.commit()
    except psycopg2.Error as e:
        print('USER error:', e)
        connection.rollback()
        connection_pool.putconn(connection)
        return web.json_response(status=409, data={})

    cursor.execute(User.query_get_user(nickname))  #TODO: не лишний ли это запрос в бд?
    result = cursor.fetchall()
    connection_pool.putconn(connection)

    if len(result) != 0:
        return web.json_response(status=200, data=dict(result[0]))
    else:
        return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})

    # async with pool.acquire() as connection:
    #     if len(data) != 0:
    #         try:
    #             await connection.fetch(User.query_update_user(**data, nickname=nickname))
    #         except Exception as e:
    #             # TODO: handle exeptions
    #             # result = await connection.fetch(user.query_update_user())
    #             return web.json_response(status=409, data={})
    #     result = await connection.fetch(User.query_get_user(nickname))
    #     if len(result) != 0:
    #         return web.json_response(status=200, data=dict(result[0]))
    #     else:
    #         return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})
