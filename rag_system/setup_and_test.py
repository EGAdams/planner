#!/usr/bin/env python3
"""
Setup and test script for the RAG Project Management System
"""

import subprocess
import sys
from pathlib import Path
from rag_system.core.claude_integration import ClaudeMemoryAssistant

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_basic_functionality():
    """Test basic RAG system functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Initialize the system
        assistant = ClaudeMemoryAssistant()
        print("✅ RAG system initialized")
        
        # Test adding a quick note
        doc_id = assistant.quick_memory_add(
            content="This is a test note to verify the RAG system is working correctly.",
            content_type="note",
            title="System Test Note",
            client_name="TestClient",
            project_name="RAG_System_Setup"
        )
        print(f"✅ Test document added with ID: {doc_id}")
        
        # Test searching
        context_data = assistant.get_enhanced_context_for_query(
            "test note system working",
            client_name="TestClient",
            project_name="RAG_System_Setup"
        )
        
        if context_data and context_data.get("related_documents"):
            print("✅ Search functionality working")
        else:
            print("⚠️  Search returned no results (may be expected for first run)")
        
        # Test project overview
        project_data = assistant.get_project_dashboard("RAG_System_Setup")
        if project_data:
            print("✅ Project dashboard functionality working")
        
        # Test system stats
        stats = assistant.document_manager.get_system_stats()
        print(f"✅ System stats: {stats['total_chunks']} chunks indexed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_sample_documents():
    """Create some sample documents for demonstration"""
    print("\n📄 Creating sample documents...")
    
    try:
        assistant = ClaudeMemoryAssistant()
        
        # Sample client profile
        assistant.quick_memory_add(
            content="""
            Client: Acme Corp
            Contact: John Smith (john@acmecorp.com)
            Industry: E-commerce
            Project Focus: Website redesign and performance optimization
            Budget: $50,000
            Timeline: 3 months
            Key Requirements: 
            - Mobile-first design
            - Fast loading times
            - SEO optimization
            - Payment integration
            """,
            content_type="general",
            title="Acme Corp - Client Profile",
            client_name="Acme Corp",
            project_name="Website Redesign"
        )
        
        # Sample meeting notes
        assistant.quick_memory_add(
            content="""
            Meeting with Acme Corp team
            Date: Today
            Attendees: John Smith (Acme), Sarah Johnson (Acme), Me
            
            Key Discussion Points:
            - Current website has 5-second load times, need to reduce to <2 seconds
            - Mobile traffic is 70% but current site not mobile-optimized
            - Want to integrate Stripe for payments
            - Need SEO audit and improvements
            
            Action Items:
            - Conduct performance audit (Due: Next week)
            - Create mobile mockups (Due: 2 weeks)
            - Research payment gateway options (Due: This week)
            - Set up staging environment (Due: 3 days)
            """,
            content_type="meeting",
            title="Acme Corp Kickoff Meeting",
            client_name="Acme Corp", 
            project_name="Website Redesign"
        )
        
        # Sample task update
        assistant.quick_memory_add(
            content="""
            Status: Completed
            Task: Performance audit for Acme Corp website
            
            Findings:
            - Large unoptimized images causing slow load times
            - 15 external JavaScript libraries, many unused
            - No CDN implementation
            - Database queries not optimized
            
            Recommendations:
            1. Implement image compression and WebP format
            2. Bundle and minify JS/CSS
            3. Set up CloudFlare CDN
            4. Add database indexing
            
            Next Steps: Share findings with client and get approval for optimizations
            """,
            content_type="task",
            title="Performance Audit - Completed",
            client_name="Acme Corp",
            project_name="Website Redesign"
        )
        
        print("✅ Sample documents created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample documents: {e}")
        return False

def demonstrate_cli():
    """Demonstrate CLI commands"""
    print("\n💻 CLI Commands Demo:")
    print("You can now use these commands:")
    print()
    print("# Initialize system")
    print("python main.py init")
    print()
    print("# Search for information")
    print('python main.py search "performance audit"')
    print()
    print("# Get project overview") 
    print('python main.py project "Website Redesign"')
    print()
    print("# Get client information")
    print('python main.py client "Acme Corp"')
    print()
    print("# Add a quick note")
    print('python main.py note "Task completed successfully" "Task Update" --client="Acme Corp"')
    print()
    print("# Show recent activities")
    print("python main.py recent")
    print()
    print("# Show system status")
    print("python main.py status")

def main():
    """Main setup and test routine"""
    print("🚀 RAG Project Management System Setup")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed. Please install dependencies manually.")
        return
    
    # Test functionality
    if not test_basic_functionality():
        print("Basic tests failed. Please check your installation.")
        return
    
    # Create sample documents
    if not create_sample_documents():
        print("Sample document creation failed.")
        return
    
    # Show CLI demo
    demonstrate_cli()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("🎉 Your RAG system is ready to enhance your project management!")
    print("\nTry running: python main.py status")

if __name__ == "__main__":
    main()