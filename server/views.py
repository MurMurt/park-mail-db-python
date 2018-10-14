from aiohttp import web
import json


async def index(request):
    data = {'summer': ['june', 'july', 'august']}
    # return web.Response(text='Hello Aiohttp!')
    return web.json_response(data)


async def post_handler(request):
    data = {'winter': ['june', 'july', 'august']}
    # return web.Response(text='Hello Aiohttp!')
    return web.json_response(data)
