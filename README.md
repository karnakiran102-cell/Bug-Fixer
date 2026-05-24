# Multi-Agent Software Development Lifecycle (SDLC) System

A comprehensive Python system that orchestrates multiple autonomous AI agents to collaborate on a complete software development lifecycle, from code generation through deployment.

## Overview

This system implements a sophisticated multi-agent framework that manages the entire software development process:

1. **Code Agent** (Developer) - Generates clean, documented Python code
2. **Review Agent** (Senior Reviewer) - Analyzes code quality and architecture
3. **Security Agent** (AppSec Engineer) - Performs security audits
4. **Bug Fix Agent** (Refactoring Specialist) - Implements feedback and fixes
5. **Testing Agent** (QA Engineer) - Creates comprehensive test suites
6. **Deployment Agent** (DevOps Engineer) - Generates deployment artifacts

## Features

✓ **Multi-Agent Orchestration** - Uses CrewAI for sophisticated agent coordination  
✓ **Parallel Execution** - Review and security analysis run in parallel  
✓ **Flexible LLM Support** - Works with OpenAI, Anthropic (Claude), Google Gemini  
✓ **Type-Hinted** - Full Python type hints for IDE support  
✓ **Error Handling** - Comprehensive error handling for API failures  
✓ **Modular Design** - Easy to swap LLM providers or add custom agents  
✓ **Artifact Generation** - Produces Dockerfile, CI/CD configs, test suites  
✓ **Workflow Tracking** - Logs all stages and maintains execution history  

## System Requirements

- Python 3.10 or higher
- Valid API key for at least one LLM provider
- pip (Python package manager)
- 4GB+ RAM recommended for optimal performance

## Installation

### 1. Clone or Navigate to Project Directory

```bash
cd Bug\ Fixer/backend
```

### 2. Create Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure LLM API Keys

Create a `.env` file in the project root with your API keys:

**For OpenAI:**
```
OPENAI_API_KEY=sk-your-key-here
```

**For Anthropic (Claude):**
```
ANTHROPIC_API_KEY=your-key-here
```

**For Google Gemini:**
```
GOOGLE_API_KEY=your-key-here
```

Alternatively, set environment variables:

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-your-key-here"
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

## Usage

### Quick Start

Run the sample workflow:

```bash
python agents_sdlc.py
```

This executes a pre-configured workflow that:
1. Generates a calculator API
2. Reviews and audits the code
3. Refactors based on feedback
4. Creates test suites
5. Generates deployment artifacts

### Customizing the Workflow

Edit the `main()` function in `agents_sdlc.py` to change the requirement:

```python
def main():
    # Configure LLM
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4",  # or "gpt-3.5-turbo"
        temperature=0.7
    )
    
    # Change this requirement
    sample_requirement = """
    Your custom requirement here:
    - Feature 1
    - Feature 2
    - Feature 3
    """
    
    # Execute workflow
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(sample_requirement)
    orchestrator.save_artifacts("./sdlc_output")
```

### Switching LLM Providers

**Use Claude (Anthropic):**
```python
llm_config = LLMConfig(
    provider=LLMProvider.ANTHROPIC,
    model="claude-3-sonnet-20240229",
    temperature=0.7
)
```

**Use Gemini (Google):**
```python
llm_config = LLMConfig(
    provider=LLMProvider.GEMINI,
    model="gemini-pro",
    temperature=0.7
)
```

## Output Structure

After execution, check the `sdlc_output/` directory:

```
sdlc_output/
├── generated_code.txt          # Initial code from Code Agent
├── review_feedback.txt         # Combined review and security feedback
├── refactored_code.txt         # Final code after fixes
├── test_suite.txt              # Complete pytest test suite
├── deployment_artifacts.txt    # Dockerfile, CI/CD, docker-compose
└── workflow_history.json       # Complete execution timeline
```

## Workflow Stages Explained

### Stage 1: Code Generation
The **Code Agent** analyzes your requirements and generates:
- Clean, pythonic code
- Type hints and docstrings
- Error handling
- Architectural overview

### Stage 2: Review & Security Audit (Parallel)
- **Review Agent**: Checks PEP-8 compliance, code quality, maintainability
- **Security Agent**: Scans for vulnerabilities, hardcoded secrets, injection risks

### Stage 3: Bug Fixing & Refactoring
The **Bug Fix Agent** implements all feedback:
- Addresses all quality issues
- Fixes security vulnerabilities
- Improves architecture
- Maintains original functionality

### Stage 4: Test Suite Generation
The **Testing Agent** creates:
- Unit tests for all functions
- Integration tests
- Edge case coverage
- Mock fixtures and test data

### Stage 5: Deployment Preparation
The **Deployment Agent** generates:
- Production-ready Dockerfile
- requirements.txt with pinned versions
- GitHub Actions CI/CD workflow
- docker-compose configuration
- Deployment instructions

## API Configuration

### Environment Variables

```python
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4  # Optional, defaults to gpt-3.5-turbo

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
GOOGLE_API_KEY=...
```

### Programmatic Configuration

```python
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    api_key="sk-...",  # Optional if in environment
    temperature=0.7,   # 0.0 to 1.0
    max_tokens=4096
)
```

## Advanced Usage

### Programmatic Integration

```python
from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider, EnvironmentType

# Setup
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4"
)
orchestrator = SDLCOrchestrator(llm_config)

# Custom workflow
requirement = "Build a FastAPI web scraper with caching"
artifacts = orchestrator.execute_workflow(
    requirement=requirement,
    environment=EnvironmentType.PRODUCTION
)

# Access artifacts programmatically
generated_code = artifacts["generated_code"]
test_suite = artifacts["test_suite"]
deployment_config = artifacts["deployment_artifacts"]

# Save results
orchestrator.save_artifacts("./my_project_output")
```

### Creating Custom Agents

```python
from agents_sdlc import Agent, Task, Crew, Process

# Create custom agent
custom_agent = Agent(
    role="Your Role",
    goal="Your Goal",
    backstory="Your Backstory",
    verbose=True,
    allow_delegation=False
)

# Create corresponding task
custom_task = Task(
    description="Task description",
    expected_output="Expected output",
    agent=custom_agent
)

# Execute
crew = Crew(
    agents=[custom_agent],
    tasks=[custom_task],
    process=Process.sequential
)
result = crew.kickoff()
```

## Troubleshooting

### API Key Not Found
```
ValueError: Missing environment variable: OPENAI_API_KEY
```

**Solution:** Ensure your API key is set in environment variables or `.env` file.

### Rate Limiting
If you hit API rate limits, add delays between requests or use a smaller model:

```python
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-3.5-turbo",  # Faster and cheaper
    temperature=0.7
)
```

### Memory Issues
For large code bases, reduce `max_tokens`:

```python
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    max_tokens=2048  # Reduced from 4096
)
```

### CrewAI Installation Issues

If CrewAI fails to install:

```bash
pip install --upgrade pip setuptools wheel
pip install crewai --no-cache-dir
```

## Performance Tips

1. **Use gpt-3.5-turbo** for faster/cheaper execution
2. **Reduce temperature** to 0.3-0.5 for more deterministic output
3. **Run stages sequentially** to avoid quota issues (current default)
4. **Cache API responses** in production
5. **Use async execution** for multiple workflows

## Cost Estimation

Using OpenAI GPT-4 (approximate):
- Single workflow: $2-5 USD
- Using GPT-3.5-turbo: $0.50-1.50 USD
- 10 workflows/day: $5-50 USD/day

## Architecture Diagram

```
User Requirement
       ↓
   [Code Agent] → Generated Code
       ↓
   ┌───┴────────────────┐
   ↓                    ↓
[Review Agent]     [Security Agent]
   ↓                    ↓
   └───┬────────────────┘
       ↓
   [Bug Fix Agent] → Refactored Code
       ↓
   [Testing Agent] → Test Suite
       ↓
   [Deployment Agent] → Deployment Artifacts
       ↓
   Final Deliverables
```

## Project Structure

```
backend/
├── agents_sdlc.py          # Main SDLC system implementation
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .env                    # API keys (not in version control)
└── sdlc_output/           # Generated artifacts (created on first run)
    ├── generated_code.txt
    ├── review_feedback.txt
    ├── refactored_code.txt
    ├── test_suite.txt
    ├── deployment_artifacts.txt
    └── workflow_history.json
```

## Dependencies

- **crewai** - Multi-agent orchestration framework
- **crewai-tools** - Built-in tools for agents
- **openai** - OpenAI API client
- **anthropic** - Anthropic Claude API client
- **google-generativeai** - Google Gemini API client
- **pydantic** - Data validation
- **python-dotenv** - Environment variable management
- **pytest** - Testing framework
- **requests** - HTTP library

## Key Classes & Functions

### Main Classes

- `SDLCOrchestrator` - Main orchestrator managing workflow
- `AgentFactory` - Factory for creating configured agents
- `TaskFactory` - Factory for creating tasks
- `LLMConfig` - Configuration for LLM provider
- `LLMProvider` - Enum of supported providers

### Agents Available

- `create_code_agent()` - Developer role
- `create_review_agent()` - Code reviewer role
- `create_security_agent()` - Security auditor role
- `create_bugfix_agent()` - Refactoring specialist role
- `create_testing_agent()` - QA engineer role
- `create_deployment_agent()` - DevOps engineer role

### Key Methods

```python
# Execute complete workflow
artifacts = orchestrator.execute_workflow(requirement, environment)

# Save all outputs to disk
orchestrator.save_artifacts(output_dir)

# Access individual artifacts
code = artifacts["generated_code"]
tests = artifacts["test_suite"]
deployment = artifacts["deployment_artifacts"]
```

## Example Workflows

### Example 1: API Development

```python
requirement = """
Create a REST API for managing a to-do list with:
- CRUD operations for tasks
- User authentication with JWT
- Database persistence (SQLite)
- Input validation
- Proper error responses
"""
```

### Example 2: Data Processing

```python
requirement = """
Build a data processing pipeline that:
- Reads CSV files
- Cleans and validates data
- Performs statistical analysis
- Exports results to JSON
- Includes progress logging
"""
```

### Example 3: Utility Library

```python
requirement = """
Create a utility library for:
- String manipulation helpers
- File I/O operations
- Configuration management
- Logging utilities
- Type validation
"""
```

## Contributing

To extend the system:

1. **Add Custom Agents**: Extend `AgentFactory`
2. **Add Custom Tools**: Create `@tool` decorated functions
3. **Modify Workflow**: Update `execute_workflow()` method
4. **Add LLM Providers**: Extend `LLMProvider` enum and `LLMConfig`

## Security Considerations

1. **Never commit API keys** - Use `.env` file with `.gitignore`
2. **Use environment variables** - Don't hardcode credentials
3. **Validate all outputs** - Generated code should be reviewed
4. **Keep dependencies updated** - Regular `pip install --upgrade`
5. **Use minimal permissions** - API keys should have least required scope

## Limitations & Future Enhancements

Current Limitations:
- Requires valid LLM API keys and active internet
- Agent performance depends on LLM model quality
- Large code bases may hit token limits
- No persistent caching of results

Planned Enhancements:
- Support for local LLMs (Ollama, LLaMA)
- Caching layer for faster re-runs
- Web UI for workflow management
- Database integration for artifact storage
- Webhook support for CI/CD integration
- Real-time streaming of agent outputs
- Custom agent templates
- Performance metrics and analytics

## License

This project is open-source. Modify and use as needed.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review CrewAI documentation: https://docs.crewai.com/
3. Check LLM provider documentation
4. Review code comments for implementation details

## Related Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API](https://claude.ai/api/documentation)
- [Google Gemini API](https://ai.google.dev/)
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: 2024  
**Version**: 1.0.0  
**Status**: Production Ready
