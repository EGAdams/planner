"""Initialize Letta SQLite database by creating all tables from ORM models."""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Letta ORM base
from letta.orm.base import Base
from letta.settings import settings

# Import all ORM model classes to register them with Base.metadata
from letta.orm import (
    Agent, AgentEnvironmentVariable, AgentsTags,
    ArchivalPassage, Archive, ArchivesAgents,
    BasePassage, Block, BlockHistory, BlocksAgents,
    FileAgent, FileMetadata,
    Group, GroupsAgents, GroupsBlocks,
    IdentitiesAgents, IdentitiesBlocks, Identity,
    Job, LLMBatchItem, LLMBatchJob,
    MCPOAuth, MCPServer, Message,
    Organization, PassageTag, Prompt,
    Provider, ProviderModel, ProviderTrace,
    Run, RunMetrics,
    SandboxConfig, SandboxEnvironmentVariable,
    Source, SourcePassage, SourcesAgents,
    Step, StepMetrics,
    Tool, ToolsAgents,
    User
)

def init_database():
    """Create all tables in the Letta database."""

    # Get database settings
    print(f"Database engine: {settings.database_engine}")

    # Construct SQLite database URI
    db_path = os.path.join(settings.letta_dir, "letta.db")
    db_uri = f"sqlite:///{db_path}"

    print(f"Database path: {db_path}")
    print(f"Database URI: {db_uri}")

    # Create engine
    engine = create_engine(db_uri, echo=True)

    # Create all tables
    print("\nCreating all tables...")
    Base.metadata.create_all(engine)

    print(f"\n✅ Database initialized successfully!")
    print(f"Tables created: {list(Base.metadata.tables.keys())}")

    return True

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
