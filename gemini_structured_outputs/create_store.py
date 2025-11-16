#
#
# create_store.py

from google import genai
client = genai.Client(api_key="AIzaSyAf7bkGiAeQnkE2xVnRwxmYAvxAegDLWnk")
store = client.file_search_stores.create(config={'display_name': 'my-first-kb-store'})
print(store.name)
