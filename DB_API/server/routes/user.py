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
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(User.query_get_user(nickname))
    result = cursor.fetchone()

    connection_pool.putconn(connection)
    if not result:
        return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})
    return web.json_response(status=200, data=result)


@routes.post('/api/user/{nickname}/profile', expect_handler=web.Request.json)
@logger
async def handle_user_update(request):

    data = await request.json()
    nickname = request.match_info['nickname']

    connection_pool = request.app['pool']
    connection = connection_pool.getconn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute(User.query_update_user(**data, nickname=nickname))
        connection.commit()
    except psycopg2.Error as e:
        print('USER POST profile:', e.pgcode)
        connection.rollback()
        connection_pool.putconn(connection)
        return web.json_response(status=409, data={})

    cursor.execute(User.query_get_user(nickname))  #TODO: не лишний ли это запрос в бд?
    result = cursor.fetchone()
    connection_pool.putconn(connection)

    if result:
        return web.json_response(status=200, data=result)
    else:
        return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})

