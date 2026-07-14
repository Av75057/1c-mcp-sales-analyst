import asyncio, json
try:
    import websockets
    async def test():
        async with websockets.connect("ws://localhost:8000/ws/chat/new") as ws:
            print("Connected!")
            await ws.send(json.dumps({"type": "get_sessions"}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(resp)
            print(f"Response type: {data.get('type')}")
            print(f"Sessions count: {len(data.get('sessions', []))}")
    asyncio.run(test())
except Exception as e:
    print(f"Error: {e}")
