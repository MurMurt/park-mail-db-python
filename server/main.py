from aiohttp import web
# from server.routes import setup_routes
from settings import config
from routes import routes
from collections import OrderedDict
import asyncio
import asyncpg


async def handle(request):
    """Handle incoming requests."""
    pool = request.app['pool']
    power = int(request.match_info.get('power', 10))

    # Take a connection from the pool.
    async with pool.acquire() as connection:
        # Open a transaction.
        async with connection.transaction():
            # Run the query passing the request argument.
            result = await connection.fetchval('select 2 ^ $1', power)
            return web.Response(
                text="2 ^ {} is {}".format(power, result))


async def init_app():
    """Initialize the application server."""
    app = web.Application()
    # Create a database connection pool
    app['pool'] = await asyncpg.create_pool(user='docker', password='docker',
                                 database='forum', host='127.0.0.1')
    # Configure service routes
    # app.router.add_route('GET', '/{power:\d+}', handle)
    # app.router.add_route('GET', '/', handle)
    app.router.add_routes(routes)
    return app



def main():
    # app = web.Application()
    # app.router.add_routes(routes)
    # app['config'] = config
    # app['db'] = run()
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, port=5000)


if __name__ == '__main__':
    main()
