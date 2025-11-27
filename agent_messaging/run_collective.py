import asyncio
from pathlib import Path
from rich.console import Console
from a2a_collective import A2ACollectiveHub
from memory_backend import MemoryBackend

class MockMemoryBackend(MemoryBackend):
    def __init__(self):
        self.namespace = "mock_namespace"
    
    async def connect(self): pass
    async def disconnect(self): pass
    async def remember(self, *args, **kwargs): return "mock_id"
    async def recall(self, *args, **kwargs): return []
    async def get_recent(self, *args, **kwargs): return []
    async def forget(self, *args, **kwargs): return True
    async def get_stats(self): return {}
    def is_connected(self): return True

class MockMemoryFactory:
    async def create_memory_async(self, agent_id: str, **kwargs):
        return "mock_backend", MockMemoryBackend()

console = Console()

async def main():
    # Initialize Hub with Mock Factory
    workspace_root = Path(__file__).parent
    hub = A2ACollectiveHub(workspace_root=workspace_root, memory_factory=MockMemoryFactory())
    
    console.print(f"[bold blue]Scanning for agents in: {workspace_root}[/bold blue]")
    
    # Discover Agents
    registry = await hub.discover_agents()
    
    console.print(f"[bold green]Discovered {len(registry)} agents[/bold green]")
    
    orchestrator_found = False
    letta_found = False
    
    for name, spoke in registry.items():
        console.print(f"- [bold]{name}[/bold] (v{spoke.card.version})")
        console.print(f"  Capabilities: {[c['name'] for c in spoke.card.capabilities]}")
        console.print(f"  Memory Backend: {spoke.memory_backend_name}")
        
        if name == "orchestrator":
            orchestrator_found = True
        if name == "letta":
            letta_found = True
            
    if not (orchestrator_found and letta_found):
        console.print("[bold red]FAILED: Could not find both agents[/bold red]")
        return

    # Simulate Delegation
    console.print("\n[bold blue]Simulating Delegation: Orchestrator -> Letta[/bold blue]")
    try:
        delegation = await hub.prepare_delegation(
            registry=registry,
            agent_name="letta",
            description="Store this important memory",
            context={"priority": "high"},
            artifacts=[]
        )
        
        console.print("[green]Delegation payload created successfully:[/green]")
        console.print(delegation)
        
    except Exception as e:
        console.print(f"[bold red]Delegation failed: {e}[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
