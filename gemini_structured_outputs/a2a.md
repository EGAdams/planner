 ```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Agent1
    participant Agent2

    User->>Orchestrator: Request service
    Orchestrator->>Agent1: Delegate task
    Agent1->>Agent2: Communicate via WebSocket
    Agent2-->>Agent1: Response
    Agent1-->>Orchestrator: Result
    Orchestrator-->>User: Final output
```