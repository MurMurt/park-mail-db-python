import asyncpg

from aiohttp import web
from models.forum import Forum

routes = web.RouteTableDef()


@routes.post('/api/forum/create', expect_handler=web.Request.json)
async def handle_forum_create(request):
    data = await request.json()
    forum = Forum(**data)

    pool = request.app['pool']
    async with pool.acquire() as connection:
        try:
            await connection.fetch(forum.query_create_forum())
        except asyncpg.exceptions.UniqueViolationError as e:
            print(Forum.query_get_forum(forum.slug))
            result = await connection.fetch(Forum.query_get_forum(forum.slug))
            forum = dict(result[0])
            forum['user'] = forum.pop('user_nick')
            return web.json_response(status=409, data=forum)
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + forum.user})

    return web.json_response(status=201, data=forum.get_data())



@routes.get('/api/user/{nickname}/profile')
async def handle_get(request):
    nickname = request.match_info['nickname']
    pool = request.app['pool']
    async with pool.acquire() as connection:
        result = await connection.fetch(User.query_get_user(nickname))
        if len(result) == 0:
            return web.json_response(status=404, data={"message": "Can't find user by nickname " + nickname})
        return web.json_response(status=200, data=dict(result[0]))