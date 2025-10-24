```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#8ecae6",
    "secondaryColor": "#ffd166",
    "tertiaryColor": "#cdb4db",
    "primaryTextColor": "#073b4c",
    "actorBorder": "#023047",
    "actorBkg": "#e0fbfc",
    "activationBkgColor": "#ffddd2",
    "activationBorderColor": "#f28482",
    "sequenceNumberColor": "#2a9d8f",
    "lineColor": "#457b9d",
    "signalColor": "#e76f51",
    "signalTextColor": "#1d3557",
    "noteBkgColor": "#f1faee",
    "noteTextColor": "#1d3557"
  }
}}%%
sequenceDiagram
  autonumber
  actor User as "User"
  participant CLI as "CLI / argparse"
  participant Bridge as "LettaMemoryBridge"
  participant Letta as "Letta Client"
  participant Blocks as "client.blocks"
  participant Agents as "client.agents"
  participant DM as "DocumentManager"
  participant Local as "Local RAG / ChromaDB"
  participant Console as "Rich Console"

  User->>CLI: Run script with command
  CLI->>Bridge: new LettaMemoryBridge with base url and api key
  Bridge->>Letta: Initialize client using api key if present
  alt connected
    Letta-->>Bridge: client ready
    Bridge->>Console: Connected to Letta server
  else connection error
    Bridge-->>CLI: exception
    CLI->>Console: Failed to connect
    CLI-->>User: exit 1
  end

  alt command == "sync"
    CLI->>Bridge: sync_from_local_rag for project
    Bridge->>Console: Syncing local memory
    Bridge->>DM: create DocumentManager
    Bridge->>DM: search_artifacts with empty query and n_results 100
    DM->>Local: query artifacts
    Local-->>DM: artifacts list
    DM-->>Bridge: list of artifacts
    alt no artifacts
      Bridge->>Console: No artifacts to sync
    else artifacts found
      Bridge->>Blocks: list
      Blocks-->>Bridge: blocks
      loop up to 50 artifacts
        Bridge->>Bridge: append title, type, first 500 chars
      end
      alt shared block exists
        Bridge->>Blocks: update by id with value
        Blocks-->>Bridge: ok
        Bridge->>Console: Updated shared block
      else no shared block
        Bridge->>Blocks: create with label and value, template false
        Blocks-->>Bridge: created block id
        Bridge->>Console: Created shared block
      end
      Bridge->>Console: Synced N artifacts to Letta
    end
  else command == "list"
    CLI->>Bridge: list_blocks
    Bridge->>Blocks: list
    Blocks-->>Bridge: blocks
    alt any blocks
      Bridge->>Console: Render table with ID, Label, Preview
    else none
      Bridge->>Console: No blocks found
    end
  else command == "create-block"
    CLI->>Bridge: create_block with label, content, template false
    alt missing args
      Bridge->>Console: Usage: create-block [label] [content]
    else ok
      Bridge->>Blocks: create with label, value, template
      alt success
        Blocks-->>Bridge: block id
        Bridge->>Console: Created block
      else error
        Blocks-->>Bridge: error
        Bridge->>Console: Error creating block
      end
    end
  else command == "search"
    CLI->>Bridge: rag_tools recall with query and limit 10
    Bridge->>Console: Found K results from local RAG
  end

  opt create agent with shared memory
    Bridge->>Blocks: list
    Blocks-->>Bridge: blocks
    alt shared block found
      Bridge->>Agents: create with name and memory block id
      Agents-->>Bridge: agent id
      Bridge->>Console: Agent created with shared memory
    else not found
      Bridge->>Console: No shared memory block - run sync first
    end
  end

  opt unexpected exception
    Bridge-->>CLI: exception
    CLI->>Console: Error e - start server or use --api-key
    CLI-->>User: exit 1
  end
  ```
