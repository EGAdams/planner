import os
import json
import re
import datetime
import pandas as pd
from time import time, sleep
from uuid import uuid4
import openai
import lancedb
import pyarrow as pa

# ----- Helper Functions -----
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)

def save_json(filepath, payload):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)

def timestamp_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")

def gpt3_embedding(content, model='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII', errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=[content], model=model)
    vector = response['data'][0]['embedding']  # access the embedding attribute
    return vector

def ai_completion(prompt, model='gpt-3.5-turbo-16k', temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0, stop=['USER:', 'RAVEN:']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
    while True:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop
            )
            text = response['choices'][0]['message']['content'].strip()
            text = re.sub('[\r\n]+', '\n', text)
            text = re.sub('[\t ]+', ' ', text)
            filename = f'{time()}_gpt3.txt'
            if not os.path.exists('gpt3_logs'):
                os.makedirs('gpt3_logs')
            save_file(f'gpt3_logs/{filename}', prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return f"GPT3 error: {oops}"
            print('Error communicating with OpenAI:', oops)
            sleep(1)

def load_conversation(results_arg):
    """
    Expects results_arg to be a list of dictionaries with an 'id' key.
    Uses each id to load a JSON file from the local file system.
    """
    result = []
    for matching_unique in results_arg:
        filename = f"/home/adamsl/linuxBash/agents/nexus/{matching_unique['id']}.json"
        if not os.path.exists(filename):
            print('file not found:', filename)
            continue
        else:
            print('file found:', filename)
        info = load_json(filename)
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()

# ----- Main Function using LanceDB -----
if __name__ == '__main__':
    USE_RUN_TEXT = False
    convo_length = 30

    # Initialize OpenAI API key
    openai.api_key = open_file('key_openai.txt')

    # Initialize LanceDB and define the schema
    db = lancedb.connect("/tmp/lancedb")
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 1536)),  # Adjust 1536 to your vector dimension
        pa.field("speaker", pa.string()),
        pa.field("time", pa.float64()),
        pa.field("message", pa.string()),
        pa.field("timestring", pa.string())
    ])

    # Create or open the table with the defined schema
    if "youtube-chatbot" in db.table_names():
        tbl = db.open_table("youtube-chatbot")
    else:
        tbl = db.create_table("youtube-chatbot", schema=schema)

    while True:
        data_for_lancedb_upsert = []

        if USE_RUN_TEXT:
            _ = input("using run.txt, ok? <enter> to continue.  ctrl-c to quit")
            user_input = open_file('/home/adamsl/linuxBash/agents/run.txt')
            USE_RUN_TEXT = True
        else:
            user_input = input('\n\nUSER: ')

        timestamp_val = time()
        timestring = timestamp_to_datetime(timestamp_val)
        embedded_user_input = gpt3_embedding(user_input)
        unique_id = str(uuid4())
        metadata = {
            'id': unique_id,
            'vector': embedded_user_input,
            'speaker': 'USER',
            'time': timestamp_val,
            'message': user_input,
            'timestring': timestring
        }
        save_json(f"/home/adamsl/linuxBash/agents/nexus/{unique_id}.json", metadata)
        data_for_lancedb_upsert.append(metadata)

        # Querying LanceDB for relevant conversation history
        results_df = tbl.search(embedded_user_input, vector_column_name='vector').limit(convo_length).to_pandas()

        # Convert the results DataFrame into the format expected by load_conversation().
        if not results_df.empty and "id" in results_df.columns:
            matches = [{"id": uid} for uid in results_df["id"]]
        else:
            matches = []
        conversation = load_conversation(matches)

        # Prepare the prompt using a template file.
        prompt_template = open_file('prompt_response.txt')
        prompt = prompt_template.replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input)

        # Get the AI's completion.
        ai_completion_text = ai_completion(prompt)

        # Save AI response to JSON and prepare for LanceDB upsert
        timestamp_val = time()
        timestring = timestamp_to_datetime(timestamp_val)
        embedded_ai_completion = gpt3_embedding(ai_completion_text)
        unique_id = str(uuid4())
        metadata = {
            'id': unique_id,
            'vector': embedded_ai_completion,
            'speaker': 'RAVEN',
            'time': timestamp_val,
            'message': ai_completion_text,
            'timestring': timestring
        }
        save_json(f"/home/adamsl/linuxBash/agents/nexus/{unique_id}.json", metadata)
        data_for_lancedb_upsert.append(metadata)

        # Upsert data into LanceDB
        df = pd.DataFrame(data_for_lancedb_upsert)
        tbl.add(df)

        print('\n\nRAVEN: %s' % ai_completion_text)

 
