#!/bin/bash
################################################################################
# Agent Communication System - Automated Migration Script
################################################################################
# This script automates the migration of the agent communication system
# to a new directory on the same machine or a different machine.
#
# Usage:
#   ./migrate_agent_system.sh                    # Installs to current directory
#   ./migrate_agent_system.sh /path/to/dest      # Installs to specified path
#
# Examples:
#   cd /home/myuser/my_project
#   ./migrate_agent_system.sh                    # Installs here
#
#   ./migrate_agent_system.sh /home/myuser/my_project  # Installs there
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Source paths (current location)
SOURCE_AGENT_MESSAGING="/home/adamsl/planner/a2a_communicating_agents/agent_messaging"
SOURCE_RAG_SYSTEM="/home/adamsl/planner/rag_system"

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗ ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.10 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.10"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python version $PYTHON_VERSION is too old. Need 3.10 or higher."
        exit 1
    fi

    print_step "Python $PYTHON_VERSION detected"
}

check_source_exists() {
    if [ ! -d "$SOURCE_AGENT_MESSAGING" ]; then
        print_error "Source directory not found: $SOURCE_AGENT_MESSAGING"
        print_info "Make sure you're running this script on the source machine"
        exit 1
    fi

    if [ ! -d "$SOURCE_RAG_SYSTEM" ]; then
        print_error "RAG system directory not found: $SOURCE_RAG_SYSTEM"
        exit 1
    fi

    print_step "Source directories verified"
}

create_directory_structure() {
    local dest=$1

    print_info "Creating directory structure at: $dest"

    mkdir -p "$dest/agent_messaging/storage/chromadb"
    mkdir -p "$dest/agent_messaging/tests"
    mkdir -p "$dest/rag_system/core"
    mkdir -p "$dest/rag_system/models"
    mkdir -p "$dest/rag_system/utils"
    mkdir -p "$dest/rag_system/storage"

    print_step "Directories created"
}

copy_files() {
    local dest=$1

    print_info "Copying agent_messaging files..."
    cp -r "$SOURCE_AGENT_MESSAGING"/* "$dest/agent_messaging/" 2>/dev/null || true

    print_info "Copying rag_system files..."
    cp -r "$SOURCE_RAG_SYSTEM"/* "$dest/rag_system/" 2>/dev/null || true

    # Remove __pycache__ directories
    find "$dest" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

    print_step "Files copied successfully"
}

create_virtual_environment() {
    local dest=$1

    print_info "Creating Python virtual environment..."
    cd "$dest"
    python3 -m venv venv

    print_step "Virtual environment created"
}

install_dependencies() {
    local dest=$1

    print_info "Installing Python dependencies..."
    cd "$dest"
    source venv/bin/activate

    pip install --quiet --upgrade pip
    pip install --quiet websockets>=15.0.1
    pip install --quiet letta-client>=1.3.1
    pip install --quiet chromadb>=1.3.0
    pip install --quiet pydantic>=2.12.5
    pip install --quiet rich>=14.2.0

    print_step "Dependencies installed"
}

create_requirements_file() {
    local dest=$1

    cat > "$dest/requirements.txt" << 'EOF'
# Agent Communication System Dependencies
websockets>=15.0.1
letta-client>=1.3.1
chromadb>=1.3.0
pydantic>=2.12.5
rich>=14.2.0
EOF

    print_step "requirements.txt created"
}

create_setup_file() {
    local dest=$1

    cat > "$dest/setup.py" << 'EOF'
from setuptools import setup, find_packages

setup(
    name="agent_messaging",
    version="1.0.0",
    description="Agent-to-Agent Communication System with WebSocket, Letta, and RAG fallback",
    packages=find_packages(),
    install_requires=[
        "websockets>=15.0.1",
        "letta-client>=1.3.1",
        "chromadb>=1.3.0",
        "pydantic>=2.12.5",
        "rich>=14.2.0",
    ],
    python_requires=">=3.10",
)
EOF

    print_step "setup.py created"

    # Install in development mode
    cd "$dest"
    source venv/bin/activate
    pip install --quiet -e .
    print_step "Package installed in development mode"
}

create_env_file() {
    local dest=$1

    cat > "$dest/.env" << EOF
# WebSocket Configuration
WEBSOCKET_URL=ws://localhost:3030

# Letta Configuration (optional, for fallback)
LETTA_BASE_URL=http://localhost:8283
LETTA_API_KEY=your_letta_api_key_here

# Memory Configuration
MEMORY_STORAGE_PATH=$dest/agent_messaging/storage
EOF

    print_step ".env file created"
}

create_test_script() {
    local dest=$1

    cat > "$dest/test_system.py" << 'EOF'
#!/usr/bin/env python3
"""
Quick test script to verify the agent communication system works.
"""
import asyncio
from agent_messaging import AgentMessenger, AgentMessage

async def test_basic_messaging():
    """Test basic agent-to-agent messaging."""
    print("Testing agent communication system...")

    try:
        # Create two agents
        agent_a = AgentMessenger("test-agent-a")
        agent_b = AgentMessenger("test-agent-b")

        # Track received messages
        received = []

        # Agent B subscribes to messages
        async def handle_message(msg: AgentMessage):
            print(f"  ✓ Agent B received: '{msg.content}'")
            received.append(msg)

        await agent_b.subscribe("general", handle_message)

        # Agent A sends message
        print("  → Agent A sending message...")
        await agent_a.send_to_agent(
            "test-agent-b",
            "Hello from Agent A! System is working.",
            topic="general"
        )

        # Wait for delivery
        await asyncio.sleep(2)

        # Verify
        if len(received) > 0:
            print("\n✓ SUCCESS! Message delivered successfully.")
            print("✓ Agent communication system is working correctly.")
        else:
            print("\n✗ FAILED: Message was not received.")
            print("  Check that WebSocket server is running.")

        # Cleanup
        await agent_a.disconnect()
        await agent_b.disconnect()

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure WebSocket server is running:")
        print("     python agent_messaging/websocket_server.py")
        print("  2. Check virtual environment is activated:")
        print("     source venv/bin/activate")
        print("  3. Verify all dependencies are installed:")
        print("     pip install -r requirements.txt")

if __name__ == "__main__":
    print("═══════════════════════════════════════════════")
    print("Agent Communication System - Test")
    print("═══════════════════════════════════════════════\n")
    asyncio.run(test_basic_messaging())
EOF

    chmod +x "$dest/test_system.py"
    print_step "test_system.py created"
}

create_readme() {
    local dest=$1

    cat > "$dest/README.md" << 'EOF'
# Agent Communication System

This is a migrated copy of the agent-to-agent communication system.

## Quick Start

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Start WebSocket Server
```bash
python agent_messaging/websocket_server.py
```

### 3. Run Test (in another terminal)
```bash
source venv/bin/activate
python test_system.py
```

## System Components

- **agent_messaging/** - Core communication system
  - WebSocket transport (primary)
  - Letta transport (fallback)
  - RAG Board transport (final fallback)
  - Memory system

- **rag_system/** - RAG-based message board

## Configuration

Edit `.env` file to configure:
- WebSocket URL
- Letta server URL
- Storage paths

## Documentation

See `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md` for complete documentation.

## Testing

```bash
# Start server
python agent_messaging/websocket_server.py

# In another terminal, run test
python test_system.py
```
EOF

    print_step "README.md created"
}

verify_installation() {
    local dest=$1

    print_info "Verifying installation..."

    # Check critical files
    local critical_files=(
        "agent_messaging/__init__.py"
        "agent_messaging/websocket_transport.py"
        "agent_messaging/letta_transport.py"
        "agent_messaging/rag_board_transport.py"
        "agent_messaging/transport_factory.py"
        "agent_messaging/transport_manager.py"
        "agent_messaging/messenger.py"
        "rag_system/__init__.py"
        "rag_system/core/document_manager.py"
    )

    local missing_files=()
    for file in "${critical_files[@]}"; do
        if [ ! -f "$dest/$file" ]; then
            missing_files+=("$file")
        fi
    done

    if [ ${#missing_files[@]} -eq 0 ]; then
        print_step "All critical files present"
        return 0
    else
        print_error "Missing critical files:"
        for file in "${missing_files[@]}"; do
            echo "    - $file"
        done
        return 1
    fi
}

print_completion_message() {
    local dest=$1

    print_header "MIGRATION COMPLETE!"

    echo ""
    echo -e "${GREEN}✓ System successfully migrated to: $dest${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Navigate to the new directory:"
    echo -e "     ${YELLOW}cd $dest${NC}"
    echo ""
    echo "  2. Activate the virtual environment:"
    echo -e "     ${YELLOW}source venv/bin/activate${NC}"
    echo ""
    echo "  3. Start the WebSocket server:"
    echo -e "     ${YELLOW}python agent_messaging/websocket_server.py${NC}"
    echo ""
    echo "  4. In another terminal, run the test:"
    echo -e "     ${YELLOW}cd $dest${NC}"
    echo -e "     ${YELLOW}source venv/bin/activate${NC}"
    echo -e "     ${YELLOW}python test_system.py${NC}"
    echo ""
    echo "Documentation:"
    echo "  - README.md - Quick start guide"
    echo "  - AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md - Full documentation"
    echo ""
    print_header "READY TO USE"
}

################################################################################
# Main Script
################################################################################

main() {
    # Use current directory as destination if not provided
    if [ $# -eq 0 ]; then
        DESTINATION="."
        print_info "No destination provided, using current directory"
    else
        DESTINATION="$1"
    fi

    # Resolve absolute path
    DESTINATION=$(cd "$DESTINATION" 2>/dev/null && pwd || echo "$DESTINATION")

    # Start migration
    print_header "AGENT COMMUNICATION SYSTEM MIGRATION"
    echo ""
    print_info "Source: $SOURCE_AGENT_MESSAGING"
    print_info "Destination: $DESTINATION"
    echo ""

    # Pre-flight checks
    print_header "Pre-flight Checks"
    check_python
    check_source_exists

    # Confirm with user
    echo ""
    if [ "$DESTINATION" = "$(pwd)" ]; then
        read -p "Continue with migration to CURRENT DIRECTORY? (y/n) " -n 1 -r
    else
        read -p "Continue with migration to $DESTINATION? (y/n) " -n 1 -r
    fi
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Migration cancelled"
        exit 0
    fi

    # Create destination if it doesn't exist
    if [ ! -d "$DESTINATION" ]; then
        print_info "Creating destination directory..."
        mkdir -p "$DESTINATION"
    fi

    # Migration steps
    echo ""
    print_header "Step 1: Creating Directory Structure"
    create_directory_structure "$DESTINATION"

    echo ""
    print_header "Step 2: Copying Files"
    copy_files "$DESTINATION"

    echo ""
    print_header "Step 3: Setting Up Python Environment"
    create_virtual_environment "$DESTINATION"
    install_dependencies "$DESTINATION"

    echo ""
    print_header "Step 4: Creating Configuration Files"
    create_requirements_file "$DESTINATION"
    create_setup_file "$DESTINATION"
    create_env_file "$DESTINATION"

    echo ""
    print_header "Step 5: Creating Helper Scripts"
    create_test_script "$DESTINATION"
    create_readme "$DESTINATION"

    echo ""
    print_header "Step 6: Verification"
    if verify_installation "$DESTINATION"; then
        echo ""
        print_completion_message "$DESTINATION"
    else
        echo ""
        print_error "Installation verification failed"
        print_info "Some files may be missing. Check the log above."
        exit 1
    fi
}

# Run main function
main "$@"
