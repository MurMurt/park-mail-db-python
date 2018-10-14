from aiohttp import web

routes = web.RouteTableDef()


@routes.get('/')
async def handle_get(request):
    data = {'summer': ['june', 'july', 'august']}
    # return web.Response(text='Hello Aiohttp!')
    pool = request.app['pool']

    async with pool.acquire() as connection:
        # Open a transaction.
        async with connection.transaction():
            # Run the query passing the request argument.
            query = '''SELECT nickname, fullname, email, about FROM users;'''
            result = await connection.fetch(query)
            print(result[0]['email'])
            return web.Response(
                text="2 ^ {} is {}".format(1, result))

    return web.json_response(data)


@routes.post('/api/user/{nickname}/create', expect_handler=web.Request.json)
async def handle_post(request):
    data = await request.json()
    nickname = request.match_info['nickname']
    # return web.Response(text='Hello Aiohttp!')
    # user = data['user']
    print(data)
    return web.json_response({})


