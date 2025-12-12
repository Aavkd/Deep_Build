"""
DeepBuild Pipeline Runner

Interactive script to run the full autonomous coding pipeline.
Configure via .env file.

Usage:
    python run_pipeline.py
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing services
load_dotenv()

# Now import services (they'll pick up env vars)
from services import (
    LLMService,
    ExecutionService,
    WorkspaceManager,
    AgentService
)


def get_config():
    """Get configuration from environment variables."""
    return {
        "ollama_host": os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "granite4:3b"),
        "max_context_chars": int(os.getenv("OLLAMA_MAX_CONTEXT_CHARS", "100000")),
        "execution_timeout": int(os.getenv("EXECUTION_TIMEOUT", "60")),
        "max_fix_attempts": int(os.getenv("MAX_FIX_ATTEMPTS", "3")),
    }


def print_header():
    """Print the application header."""
    print("\n" + "=" * 60)
    print("🏗️  DeepBuild - Autonomous Coding Agent")
    print("=" * 60)


def print_config(config: dict):
    """Display current configuration."""
    print("\n📋 Configuration:")
    print(f"   Model: {config['ollama_model']}")
    print(f"   Ollama Host: {config['ollama_host']}")
    print(f"   Timeout: {config['execution_timeout']}s")
    print(f"   Max Fix Attempts: {config['max_fix_attempts']}")


def run_pipeline():
    """Run the full DeepBuild pipeline interactively."""
    print_header()
    
    # Load configuration
    config = get_config()
    print_config(config)
    
    # Initialize workspace
    workspace_root = Path(__file__).parent / "DeepBuild_Workspace"
    
    # Initialize services
    print("\n🔧 Initializing services...")
    
    workspace_manager = WorkspaceManager(workspace_root=workspace_root)
    
    llm_service = LLMService(
        model=config["ollama_model"],
        max_context_chars=config["max_context_chars"],
        ollama_host=config["ollama_host"]
    )
    
    execution_service = ExecutionService(
        workspace_root=workspace_root,
        default_timeout=config["execution_timeout"]
    )
    
    agent_service = AgentService(
        workspace_manager=workspace_manager,
        llm_service=llm_service,
        execution_service=execution_service,
        prompts_dir=Path(__file__).parent / "PROMPTS"
    )
    agent_service.max_fix_attempts = config["max_fix_attempts"]
    
    # Check Ollama connection
    print("\n🔌 Checking Ollama connection...")
    if llm_service.check_connection():
        print("   ✅ Connected to Ollama")
    else:
        print("   ❌ Failed to connect to Ollama")
        print(f"   Make sure Ollama is running at {config['ollama_host']}")
        sys.exit(1)
    
    # Get project details from user
    print("\n" + "-" * 60)
    project_name = input("📁 Project name: ").strip()
    if not project_name:
        project_name = "my_project"
    
    print("\n💡 What would you like to build?")
    print("   (Examples: 'Build a Snake game', 'Create a CLI todo app')")
    user_query = input(">>> ").strip()
    
    if not user_query:
        print("❌ No query provided. Exiting.")
        sys.exit(1)
    
    # Initialize project
    print(f"\n📂 Initializing project '{project_name}'...")
    project_path = workspace_manager.init_project(project_name, user_query)
    print(f"   Created: {project_path}")
    
    # Generate build plan
    print("\n🧠 Generating build plan...")
    print("   (This may take a moment...)")
    
    start_time = time.time()
    plan_content = agent_service.generate_plan(project_name, user_query)
    plan_time = time.time() - start_time
    
    print(f"   ✅ Plan generated in {plan_time:.1f}s")
    
    # Show plan preview
    print("\n" + "-" * 60)
    print("📋 BUILD PLAN:")
    print("-" * 60)
    
    # Show first 40 lines of plan
    plan_lines = plan_content.split('\n')[:40]
    for line in plan_lines:
        print(line)
    
    if len(plan_content.split('\n')) > 40:
        print("\n... (truncated, see full plan in project folder)")
    
    print("-" * 60)
    
    # Ask to proceed
    print("\n🚀 Ready to execute the build plan.")
    proceed = input("   Proceed with execution? [Y/n]: ").strip().lower()
    
    if proceed == 'n':
        print("\n📄 Plan saved. You can review it at:")
        print(f"   {project_path / 'build_plan.md'}")
        print("\nRun 'python run_pipeline.py' again to continue.")
        sys.exit(0)
    
    # Execute all steps
    print("\n⚡ Executing build steps...")
    print("=" * 60)
    
    step_count = 0
    start_time = time.time()
    
    while True:
        result = agent_service.execute_next_step(project_name)
        
        if result.get("completed"):
            print("\n✅ All steps completed!")
            break
        
        if not result.get("success"):
            print(f"\n❌ Error: {result.get('message', 'Unknown error')}")
            retry = input("   Try to continue? [Y/n]: ").strip().lower()
            if retry == 'n':
                break
            continue
        
        step = result.get("step", {})
        step_count += 1
        
        # Display step result
        status = "✅" if result.get("success") else "❌"
        step_type = step.get("type", "?")
        step_title = step.get("title", "Unknown step")[:50]
        
        print(f"\n{status} Step {step_count}: [{step_type}] {step_title}")
        
        if step_type == "command":
            inner_result = result.get("result", {})
            if inner_result.get("stdout"):
                # Show first 3 lines of output
                stdout_lines = inner_result["stdout"].strip().split('\n')[:3]
                for line in stdout_lines:
                    print(f"   │ {line[:70]}")
    
    total_time = time.time() - start_time
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 BUILD SUMMARY")
    print("=" * 60)
    print(f"   Project: {project_name}")
    print(f"   Steps executed: {step_count}")
    print(f"   Total time: {total_time:.1f}s")
    print(f"\n📁 Output location:")
    print(f"   {project_path / 'code'}")
    print(f"\n📄 Build report:")
    print(f"   {project_path / 'build_report.md'}")
    print("=" * 60)


def list_projects():
    """List existing projects."""
    workspace_root = Path(__file__).parent / "DeepBuild_Workspace"
    workspace_manager = WorkspaceManager(workspace_root=workspace_root)
    
    projects = workspace_manager.list_projects()
    
    if not projects:
        print("\nNo projects found.")
        return
    
    print("\n📁 Existing Projects:")
    for p in projects:
        status = p.get("status", "unknown")
        name = p.get("name", "unnamed")
        print(f"   • {name} [{status}]")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_projects()
            return
        elif sys.argv[1] == "--help":
            print("DeepBuild Pipeline Runner")
            print("\nUsage:")
            print("  python run_pipeline.py          Run the build pipeline")
            print("  python run_pipeline.py --list   List existing projects")
            print("  python run_pipeline.py --help   Show this help")
            print("\nConfiguration via .env file:")
            print("  OLLAMA_HOST, OLLAMA_MODEL, EXECUTION_TIMEOUT, etc.")
            return
    
    run_pipeline()


if __name__ == "__main__":
    main()
