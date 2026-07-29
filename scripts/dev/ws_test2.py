import asyncio, json
import websockets

async def test():
    async with websockets.connect("ws://localhost:8000/ws/chat/new") as ws:
        print("Connected!")
        
        # Send a message
        await ws.send(json.dumps({"type": "message", "content": "привет, покажи остатки"}))
        
        # Read responses
        while True:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(resp)
                t = data.get('type')
                
                if t == 'session_created':
                    print(f"Session: {data.get('id')}")
                elif t == 'token':
                    print(data.get('content'), end='', flush=True)
                elif t == 'tool_call':
                    print(f"\n[Tool: {data.get('name')}]")
                elif t == 'chart':
                    print(f"\n[Chart received: {len(data.get('image_base64',''))} bytes]")
                elif t == 'done':
                    print("\n[Done]")
                    break
                elif t == 'error':
                    print(f"\n[Error: {data.get('content')}]")
                    break
                else:
                    print(f"\n[{t}]: {json.dumps(data)[:200]}")
            except asyncio.TimeoutError:
                print("\n[Timeout]")
                break

asyncio.run(test())
