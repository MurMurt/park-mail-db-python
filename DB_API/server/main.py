try:
    import psycopg2
except ImportError:
    # Fall back to psycopg2cffi
    from psycopg2cffi import compat

    compat.register()

import psycopg2
from psycopg2 import pool

from aiohttp import web

from routes.user import routes as user_routes
from routes.forum import routes as forum_routes
from routes.thread import routes as thread_routes
from routes.post import routes as post_routes
from routes.vote import routes as vote_routes




from collections import OrderedDict
import asyncio
# import asyncpg


async def init_app():
    """Initialize the application server."""
    app = web.Application()
    # Create a database connection pool
    app['pool'] = psycopg2.pool.SimpleConnectionPool(1, 2,
                                                     user="docker",
                                                     password="docker",
                                                     host="127.0.0.1",
                                                     port="5432",
                                                     database="docker")

    app.router.add_routes(user_routes)
    app.router.add_routes(forum_routes)
    app.router.add_routes(thread_routes)
    app.router.add_routes(post_routes)

    app.router.add_routes(vote_routes)
    return app


def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, port=5000)


# app = web.Application()
# # Create a database connection pool
# app['pool'] = asyncpg.create_pool(user='docker', password='docker', database='docker', host='127.0.0.1')
# app.router.add_routes(user_routes)
# app.router.add_routes(forum_routes)
# app.router.add_routes(thread_routes)
# app.router.add_routes(post_routes)
# app.router.add_routes(vote_routes)

# loop = asyncio.get_event_loop()
# app = loop.run_until_complete(init_app())


# web.run_app(app, port=5000)
#

if __name__ == '__main__':
    main()
