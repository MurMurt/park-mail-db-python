from aiohttp import web
from models.user import User
from .timer import logger

routes = web.RouteTableDef()


@routes.post('/api/user/{nickname}/create', expect_handler=web.Request.json)
@logger
async def handle_user_create(request):
    data = await request.json()
    user = User(**data, nickname=request.match_info['nickname'])

    pool = request.app['pool']
    async with pool.acquire() as connection:
        # Open a transaction.
        # async with connection.transaction():
        try:
            await connection.fetch(user.query_create_user())

        except Exception:
            result = await connection.fetch(user.query_get_same_users())
            return web.json_response(status=409, data=list(map(dict, result)))

        return web.json_response(status=201, data=user.get_data())


@routes.get('/api/user/{nickname}/profile')
@logger
async def handle_get(request):
    nickname = request.match_info['nickname']
    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch(User.query_get_user(nickname))
        if len(result) == 0:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})
        return web.json_response(status=200, data=dict(result[0]))


@routes.post('/api/user/{nickname}/profile', expect_handler=web.Request.json)
@logger
async def handle_user_update(request):
    data = await request.json()
    nickname = request.match_info['nickname']
    # user = User(**data, nickname=request.match_info['nickname'])

    pool = request.app['pool']

    async with pool.acquire() as connection:
        if len(data) != 0:
            try:
                # print(User.query_update_user(**data, nickname=nickname))
                await connection.fetch(User.query_update_user(**data, nickname=nickname))
            except Exception as e:
                # TODO: handle exeptions
                # print('ERROR', e)
                # result = await connection.fetch(user.query_update_user())
                return web.json_response(status=409, data={})
        result = await connection.fetch(User.query_get_user(nickname))
        if len(result) != 0:
            return web.json_response(status=200, data=dict(result[0]))
        else:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})
