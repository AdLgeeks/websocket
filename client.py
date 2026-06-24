import asyncio
import json
import websockets

async def run_query(uri, query_data, is_json=False):
    try:
        async with websockets.connect(uri) as ws:
            # Prepare payload
            payload = json.dumps(query_data) if is_json else query_data
            
            print(f"\n--- Sending query ({'JSON' if is_json else 'TEXT'}): {query_data} ---")
            await ws.send(payload)

            # Receive the response
            response = await ws.recv()
            print("Received Response:")
            print(response)
    except Exception as e:
        print(f"Error for query '{query_data}': {e}")

async def test_suite():
    uri = "ws://127.0.0.1:8080/query?session_id=TEST_SESSION_123"
    
    # Wait for server to bind
    await asyncio.sleep(0.5)

    # Test case 1: Raw Text Query
    await run_query(uri, "How do I represent a 3D point in the TKMath library?")
    
    # Test case 2: JSON Query (GraphRAG schema)
    await run_query(uri, {"query": "What class describes a shape with orientation in src/TopoDS/?"}, is_json=True)
    
    # Test case 3: Raw Text Multi-concept Query
    await run_query(uri, "Explain standard transient classes and geometry curves in the codebase.")
    
    # Test case 4: JSON Multi-concept Query
    await run_query(uri, {"query": "How is a boolean cut operation implemented on shapes?"}, is_json=True)

if __name__ == "__main__":
    asyncio.run(test_suite())

