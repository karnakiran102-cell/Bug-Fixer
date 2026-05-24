"""
QUICK START GUIDE - Multi-Agent SDLC System

This file contains ready-to-use examples for common scenarios.
Copy and modify these examples to suit your needs.
"""

# ============================================================================
# EXAMPLE 1: BASIC USAGE - DEFAULT CONFIGURATION
# ============================================================================

def example_basic_usage():
    """Run the system with default OpenAI GPT-4 configuration."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider, EnvironmentType
    
    # Create config using environment variable
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4"
    )
    
    # Define requirement
    requirement = """
    Build a weather data processor that:
    1. Fetches weather data from an API
    2. Stores it in a local database
    3. Provides analytics (temperature trends, humidity averages)
    4. Exports reports as CSV
    """
    
    # Execute workflow
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(requirement)
    orchestrator.save_artifacts("./weather_app_output")
    
    return artifacts


# ============================================================================
# EXAMPLE 2: USING CLAUDE (ANTHROPIC)
# ============================================================================

def example_claude_anthropic():
    """Run with Anthropic's Claude for potentially better reasoning."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    
    llm_config = LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-sonnet-20240229",
        temperature=0.5  # Lower temperature for more deterministic output
    )
    
    requirement = "Create a task scheduling system with recurring tasks and notifications"
    
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(requirement)
    orchestrator.save_artifacts("./scheduler_output")
    
    return artifacts


# ============================================================================
# EXAMPLE 3: COST-EFFECTIVE USAGE WITH GPT-3.5
# ============================================================================

def example_budget_friendly():
    """Use cheaper GPT-3.5-turbo for faster, more economical processing."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-3.5-turbo",  # ~10x cheaper than GPT-4
        temperature=0.7
    )
    
    requirement = """
    Build a simple markdown-to-HTML converter with:
    - Support for headers, bold, italic
    - Code block highlighting
    - Link parsing
    """
    
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(requirement)
    orchestrator.save_artifacts("./markdown_converter_output")
    
    return artifacts


# ============================================================================
# EXAMPLE 4: ACCESSING ARTIFACTS PROGRAMMATICALLY
# ============================================================================

def example_programmatic_access():
    """Access generated artifacts programmatically without saving to disk."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4"
    )
    
    requirement = "Create a JSON config file validator"
    
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(requirement)
    
    # Access individual artifacts
    generated_code = artifacts["generated_code"]
    review_feedback = artifacts["review_feedback"]
    refactored_code = artifacts["refactored_code"]
    test_suite = artifacts["test_suite"]
    deployment_artifacts = artifacts["deployment_artifacts"]
    
    # Use the code in your application
    print(f"Generated Code:\n{generated_code[:500]}...")
    print(f"Test Suite:\n{test_suite[:500]}...")
    
    # Save artifacts with custom naming
    orchestrator.save_artifacts("./custom_output_dir")


# ============================================================================
# EXAMPLE 5: BATCH PROCESSING MULTIPLE REQUIREMENTS
# ============================================================================

def example_batch_processing():
    """Process multiple requirements in sequence."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-3.5-turbo"  # Use cheaper model for batch processing
    )
    
    requirements = [
        "Build a simple URL shortener service",
        "Create an email notification system",
        "Build a file backup utility",
    ]
    
    orchestrator = SDLCOrchestrator(llm_config)
    
    for i, requirement in enumerate(requirements, 1):
        print(f"\n{'='*80}")
        print(f"Processing requirement {i}/{len(requirements)}")
        print(f"{'='*80}\n")
        
        artifacts = orchestrator.execute_workflow(requirement)
        orchestrator.save_artifacts(f"./batch_output_{i}")
        
        # Optional: Process artifacts
        code = artifacts["generated_code"]
        tests = artifacts["test_suite"]
        # ... do something with artifacts ...


# ============================================================================
# EXAMPLE 6: CUSTOM CONFIGURATION WITH ALL OPTIONS
# ============================================================================

def example_full_configuration():
    """Demonstrate all available configuration options."""
    from agents_sdlc import (
        SDLCOrchestrator, 
        LLMConfig, 
        LLMProvider,
        EnvironmentType
    )
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        api_key="sk-...",  # Optional if in environment
        temperature=0.7,
        max_tokens=4096
    )
    
    requirement = "Build a real-time log aggregator for distributed systems"
    
    orchestrator = SDLCOrchestrator(llm_config)
    
    # Execute with specific environment
    artifacts = orchestrator.execute_workflow(
        requirement=requirement,
        environment=EnvironmentType.PRODUCTION  # or STAGING, DEVELOPMENT
    )
    
    # View execution history
    print("\nWorkflow Execution History:")
    for i, step in enumerate(orchestrator.workflow_history, 1):
        print(f"{i}. [{step['status'].upper()}] {step['step']}")
    
    # Save artifacts
    orchestrator.save_artifacts("./log_aggregator_output")


# ============================================================================
# EXAMPLE 7: ERROR HANDLING AND RESILIENCE
# ============================================================================

def example_with_error_handling():
    """Demonstrate proper error handling."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    import traceback
    
    try:
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4"
        )
        
        requirement = "Create a caching middleware for web applications"
        
        orchestrator = SDLCOrchestrator(llm_config)
        artifacts = orchestrator.execute_workflow(requirement)
        orchestrator.save_artifacts("./cache_middleware_output")
        
        print("✓ Workflow completed successfully!")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Hint: Check that API keys are properly set")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()


# ============================================================================
# EXAMPLE 8: COMPLEX MULTI-FEATURE REQUIREMENT
# ============================================================================

def example_complex_application():
    """Process a complex real-world requirement."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4"
    )
    
    complex_requirement = """
    Build a comprehensive e-commerce inventory management system with:
    
    FEATURES:
    1. Product Management
       - CRUD operations for products
       - SKU tracking
       - Price history
       - Category management
    
    2. Inventory Tracking
       - Stock level monitoring
       - Low stock alerts
       - Batch operations
       - Warehouse management
    
    3. Order Processing
       - Order creation and tracking
       - Inventory deduction
       - Fulfillment status
       - Return management
    
    4. Reporting
       - Sales analytics
       - Inventory turnover
       - Revenue reports
       - Demand forecasting
    
    5. Integration
       - REST API endpoints
       - Webhook support
       - Database persistence (PostgreSQL)
       - Caching layer (Redis)
    
    REQUIREMENTS:
    - Production-ready code
    - Comprehensive error handling
    - Full test coverage
    - API documentation
    - Docker deployment
    - CI/CD pipeline
    """
    
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(complex_requirement)
    orchestrator.save_artifacts("./ecommerce_inventory_output")
    
    return artifacts


# ============================================================================
# EXAMPLE 9: MIGRATING EXISTING CODE
# ============================================================================

def example_code_improvement():
    """Improve and refactor existing code using the system."""
    from agents_sdlc import (
        Agent, 
        Task, 
        Crew, 
        Process,
        AgentFactory,
        LLMConfig,
        LLMProvider
    )
    
    existing_code = """
    def calc(x, y, op):
        if op == '+':
            return x + y
        elif op == '-':
            return x - y
        elif op == '*':
            return x * y
        elif op == '/':
            return x / y
        else:
            return None
    """
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4"
    )
    
    agent_factory = AgentFactory(llm_config)
    review_agent = agent_factory.create_review_agent()
    security_agent = agent_factory.create_security_agent()
    
    # Review and improve the code
    # ... use agents to analyze and refactor ...


# ============================================================================
# EXAMPLE 10: RUNNING AS A SERVICE
# ============================================================================

def example_service_mode():
    """Run as a background service processing requirements from a queue."""
    from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider
    import time
    from datetime import datetime
    
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-3.5-turbo"
    )
    
    orchestrator = SDLCOrchestrator(llm_config)
    
    # Example queue of requirements
    requirement_queue = [
        "Build a simple TODO API",
        "Create a password strength checker",
        "Build a CSV data cleaner",
    ]
    
    for requirement in requirement_queue:
        try:
            print(f"\n[{datetime.now()}] Processing: {requirement}")
            
            artifacts = orchestrator.execute_workflow(requirement)
            
            # Save with timestamp
            output_dir = f"./service_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            orchestrator.save_artifacts(output_dir)
            
            print(f"✓ Saved to {output_dir}")
            
            # Optional: Add delay between requests to avoid rate limiting
            time.sleep(5)
            
        except Exception as e:
            print(f"✗ Error processing: {e}")
            continue


# ============================================================================
# MAIN - RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Basic Usage", example_basic_usage),
        "2": ("Claude (Anthropic)", example_claude_anthropic),
        "3": ("Budget-Friendly (GPT-3.5)", example_budget_friendly),
        "4": ("Programmatic Access", example_programmatic_access),
        "5": ("Batch Processing", example_batch_processing),
        "6": ("Full Configuration", example_full_configuration),
        "7": ("Error Handling", example_with_error_handling),
        "8": ("Complex Application", example_complex_application),
        "10": ("Service Mode", example_service_mode),
    }
    
    print("\n" + "="*80)
    print("MULTI-AGENT SDLC SYSTEM - EXAMPLE MENU")
    print("="*80)
    print("\nAvailable Examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("\n  0. Exit")
    print("="*80)
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nSelect an example (1-10, or 0 to exit): ").strip()
    
    if choice == "0":
        print("Exiting...")
    elif choice in examples:
        name, example_func = examples[choice]
        print(f"\nRunning: {name}")
        print("="*80 + "\n")
        
        try:
            example_func()
            print("\n" + "="*80)
            print("✓ Example completed successfully!")
            print("="*80)
        except Exception as e:
            print("\n" + "="*80)
            print(f"✗ Example failed: {e}")
            print("="*80)
            import traceback
            traceback.print_exc()
    else:
        print("Invalid choice. Please select a valid example.")
