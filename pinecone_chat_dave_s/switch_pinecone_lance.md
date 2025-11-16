# Your Role
- Expert Python Developer
- Expert with creating and using embeddings for effective research

# Your Task
- Given the original chatbot code, rewrite the main Python function by replacing the pinecone vector database( vdb.upsert(), vdb.query() ... ) with methods using the lancedb vector database instead.
- Assume that the lancedb vector database is located in the path "/tmp/lancedb".

## Python Source for the example lancedb vector database usage:
``` python
from datasets import load_dataset

data = load_dataset('jamescalam/youtube-transcriptions', split='train')

from lancedb.context import contextualize
df = (contextualize(data.to_pandas())
      .groupby("title").text_col("text")
      .window(20).stride(4)
      .to_df())
df.head(1)

import openai
import os

# Configuring the environment variable OPENAI_API_KEY
if "OPENAI_API_KEY" not in os.environ:
    # OR set the key here as a variable
    openai.api_key = "<removed>"
    
assert len(openai.Model.list()["data"]) > 0

def embed_func(c):    
    rs = openai.Embedding.create(input=c, engine="text-embedding-ada-002")
    return [record["embedding"] for record in rs["data"]]

import lancedb
from lancedb.embeddings import with_embeddings

# data = with_embeddings(embed_func, df, show_progress=True)
# data.to_pandas().head(1)

db = lancedb.connect("/tmp/lancedb")
# tbl = db.create_table("youtube-chatbot", data)
# get table
tbl = db.open_table("youtube-chatbot")

#print the length of the table
print(len(tbl))

tbl.to_pandas().head(1)

def create_prompt(query, context):
    limit = 3750

    prompt_start = (
        "Answer the question based on the context below.\n\n"+
        "Context:\n"
    )
    prompt_end = (
        f"\n\nQuestion: {query}\nAnswer:"
    )
    # append contexts until hitting limit
    for i in range(1, len(context)):
        if len("\n\n---\n\n".join(context.text[:i])) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(context.text[:i-1]) +
                prompt_end
            )
            break
        elif i == len(context)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(context.text) +
                prompt_end
            )    
    return prompt

def complete(prompt):
    # query text-davinci-003
    res = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        temperature=0,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return res['choices'][0]['text'].strip()

query = ("How do I use the Pandas library to create embeddings?")

# Embed the question
emb = embed_func(query)[0]

# Use LanceDB to get top 3 most relevant context
context = tbl.search(emb).limit(3).to_df()

# Get the answer from completion API
prompt = create_prompt(query, context)
print( "context:", context )
print ( complete( prompt ))
```

## Python Source for the Original Chatbot
``` python
import os
import openai
import json
import numpy as np
from numpy.linalg import norm
import re
from time import time,sleep
from uuid import uuid4
import datetime
import pinecone

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8' ) as infile:
        return infile.read()

def save_file(filepath, content ):
    with open(filepath, 'w', encoding='utf-8' ) as outfile:
        outfile.write(content )

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8' ) as infile:
        return json.load( infile )

def save_json(filepath, payload):
    with open(filepath, 'w', encoding='utf-8' ) as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)

def timestamp_to_datetime( unix_time ):
    return datetime.datetime.fromtimestamp( unix_time ).strftime("%A, %B %d, %Y at %I:%M%p %Z")

def gpt3_embedding(content, engine='text-embedding-ada-002' ):
    content = content.encode(encoding='ASCII',errors='ignore' ).decode()  # fix any UNICODE errors
    response = openai.Embedding.create( input=content,engine=engine )
    vector = response[ 'data' ][ 0 ][ 'embedding' ]  # this is a normal list
    return vector

def ai_completion(prompt, engine='gpt-3.5-turbo-16k', temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0, stop=[ 'USER:', 'RAVEN:' ]):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore' ).decode()
    while True:
        try:
            response = openai.Completion.createChatCompletion(
                model=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response[ 'choices' ][0][ 'text' ].strip()
            text = re.sub( '[\r\n]+', '\n', text )
            text = re.sub( '[\t ]+', ' ', text )
            filename = '%s_gpt3.txt' % time()
            if not os.path.exists( 'gpt3_logs' ):
                os.makedirs( 'gpt3_logs' )
            save_file( 'gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text )
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print( 'Error communicating with OpenAI:', oops )
            sleep(1)


def load_conversation( results_arg ):  # comes from:  vdb.query( vector = embedded_user_input, top_k = convo_length )
    result = list()
    for matching_unique_id in results_arg[ 'matches' ]:
        filename = '/home/adamsl/linuxBash/agents/nexus/%s.json' % matching_unique_id[ 'id' ]
        # if filename exists, load it and append it to the result list, otherwise skip it
        if not os.path.exists( filename ):
            print ( 'file not found:', filename )
            continue
        else:
            print ( 'file found:', filename )
        info = load_json( '/home/adamsl/linuxBash/agents/nexus/%s.json' % matching_unique_id[ 'id' ])
        result.append( info )
    ordered = sorted( result, key=lambda d: d[ 'time' ], reverse=False )  # sort them all chronologically
    messages = [ i[ 'message' ] for i in ordered ]
    return '\n'.join( messages ).strip()

if __name__ == '__main__':
    USE_RUN_TEXT = True
    convo_length = 30
    openai.api_key = open_file( 'key_openai.txt' )
    pinecone.init( api_key=open_file( 'key_pinecone.txt' ), environment='northamerica-northeast1-gcp' )
    vdb = pinecone.Index( "debug-memory" )
    while True:
        ###
        data_for_pinecone_upsert = list()  # initialize the list that will ultimately be upserted to the vector database
        if ( USE_RUN_TEXT == True ):
            temp = input( "using run.txt, ok? <enter> to continue.  ctrl-c to quit" )
            user_input = open_file( '/home/adamsl/linuxBash/agents/run.txt' )
            USE_RUN_TEXT = False
        else:
            user_input = input( '\n\nUSER: ' )
        timestamp = time()
        timestring = timestamp_to_datetime( timestamp )
        embedded_user_input = gpt3_embedding( user_input )
        unique_id = str( uuid4())
        metadata = { 'speaker': 'USER', 'time': timestamp, 'message': user_input, 'timestring': timestring, 'uuid': unique_id }
        save_json( '/home/adamsl/linuxBash/agents/nexus/%s.json' % unique_id, metadata ) # <<--- save user input to a .json file on our file system ---<<<
        data_for_pinecone_upsert.append(( unique_id, embedded_user_input ))  # <<--- this data is going to pinecone ---<<<
        ###
        ###  Now we have the user input not only saved to our local file, but it is also placed in the built-in mutable
        ###  sequence that we will ultimately be inserted into the vector database under the same unique_id.
        ###
        results = vdb.query( vector=embedded_user_input, top_k=convo_length )# search for relevant message unique ids in vsd
        conversation = load_conversation( results )  # with these unique ids, which where very cheap to aquire, we load the
                                                     # relevant conversation data from our local file system
        prompt = open_file( 'prompt_response.txt' ).replace( '<<CONVERSATION>>', conversation ).replace( '<<MESSAGE>>', user_input )
        ###
        ai_completion_text = ai_completion( prompt )  # <<-- send the prompt created from the template to the model ---<<<
        timestamp = time()
        timestring = timestamp_to_datetime( timestamp )
        embedded_ai_completion = gpt3_embedding( ai_completion_text )
        unique_id = str( uuid4())
        metadata = { 'speaker': 'RAVEN', 'time': timestamp, 'message': ai_completion_text,
                     'timestring': timestring, 'uuid': unique_id }
        ###
        save_json( '/home/adamsl/linuxBash/agents/nexus/%s.json' % unique_id, metadata ) # <<--- save ai answer to a .json file ---<<<
        ###
        data_for_pinecone_upsert.append(( unique_id, embedded_ai_completion )) # <<--- add ai answer to data to be upserted ---<<<
        vdb.upsert( data_for_pinecone_upsert ) # <<--- upsert the data to pinecone ---<<<
        print( '\n\nRAVEN: %s' % ai_completion_text )  
        
        # just noticed that the unique_id is being used in the upsert and
        # the save_json, so it's being saved twice. How are we referencing both?
        # we "tag" the data here on our file system.  the vector database
        # returns the unique_ids that have relevance.  we use those ids to get the relevant data from
        # our file system.  the unique_id is the "tag" that links the two.
```

https://chat.openai.com/share/73615abc-1e14-481a-96d9-4c630bcb9d96
