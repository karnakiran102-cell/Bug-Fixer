# QUICK REFERENCE GUIDE

## Multi-Agent SDLC System - Cheat Sheet

---

## INSTALLATION (1 minute)

### Windows
```batch
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## CONFIGURATION

### Add API Key to .env
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Or Set Environment Variable
**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY = "sk-your-key"
```

**macOS/Linux**:
```bash
export OPENAI_API_KEY="sk-your-key"
```

---

## QUICK START

### Basic Usage
```bash
python agents_sdlc.py
```

### View Examples
```bash
python examples.py
```

### Explore Different Examples
```bash
python examples.py 1    # Basic Usage
python examples.py 2    # Claude (Anthropic)
python examples.py 3    # Budget-Friendly (GPT-3.5)
python examples.py 8    # Complex Application
```

---

## PYTHON API

### Minimal Example
```python
from agents_sdlc import SDLCOrchestrator, LLMConfig, LLMProvider

# Setup
llm_config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")
orchestrator = SDLCOrchestrator(llm_config)

# Execute
requirement = "Build a simple calculator"
artifacts = orchestrator.execute_workflow(requirement)

# Save
orchestrator.save_artifacts("./output")
```

### With Different Provider
```python
# Claude
llm_config = LLMConfig(
    provider=LLMProvider.ANTHROPIC,
    model="claude-3-sonnet-20240229"
)

# Gemini
llm_config = LLMConfig(
    provider=LLMProvider.GEMINI,
    model="gemini-pro"
)
```

### Access Individual Artifacts
```python
generated_code = artifacts["generated_code"]
test_suite = artifacts["test_suite"]
deployment = artifacts["deployment_artifacts"]

# Save to custom location
orchestrator.save_artifacts("./my_project")
```

---

## COMMON COMMANDS

| Task | Command |
|------|---------|
| Install dependencies | `pip install -r requirements.txt` |
| Activate venv (Windows) | `venv\Scripts\activate.bat` |
| Activate venv (macOS/Linux) | `source venv/bin/activate` |
| Run main workflow | `python agents_sdlc.py` |
| View examples | `python examples.py` |
| Edit config | `nano .env` or `notepad .env` |
| List installed packages | `pip list` |
| Upgrade pip | `python -m pip install --upgrade pip` |
| Deactivate venv | `deactivate` |

---

## WORKFLOW STAGES

```
1. CODE GENERATION      → Generated code with docstrings
2. REVIEW & SECURITY    → Feedback and vulnerabilities
3. REFACTORING          → Fixed and improved code
4. TEST GENERATION      → Pytest test suite
5. DEPLOYMENT CONFIG    → Docker, CI/CD, requirements.txt
```

---

## OUTPUT FILES

After running, check `sdlc_output/` folder:

```
sdlc_output/
├── generated_code.txt           ← Initial code
├── review_feedback.txt          ← Combined feedback
├── refactored_code.txt          ← Final improved code
├── test_suite.txt               ← Pytest tests
├── deployment_artifacts.txt     ← Dockerfile, etc.
└── workflow_history.json        ← Execution timeline
```

---

## CUSTOMIZING REQUIREMENTS

Edit `main()` function in `agents_sdlc.py`:

```python
def main():
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4"
    )
    
    sample_requirement = """
    Your custom requirement here:
    - Feature 1
    - Feature 2
    - Feature 3
    """
    
    orchestrator = SDLCOrchestrator(llm_config)
    artifacts = orchestrator.execute_workflow(sample_requirement)
    orchestrator.save_artifacts("./sdlc_output")
```

---

## TROUBLESHOOTING

### "API key not found"
**Solution**: Add to .env file:
```
OPENAI_API_KEY=sk-your-actual-key
```

### "ModuleNotFoundError"
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### "Activation failed"
**Solution**: Create virtual environment:
```bash
python -m venv venv
```

### Rate limit exceeded
**Solution**: Use cheaper model:
```python
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-3.5-turbo"  # Use this instead
)
```

### Long execution time
**Solution**: Check model choice:
- GPT-4: ~10-15 minutes
- GPT-3.5: ~3-5 minutes (recommended)

---

## PRICING ESTIMATES

Using OpenAI (approximate per workflow):

| Model | Speed | Cost | Use Case |
|-------|-------|------|----------|
| GPT-4 | Slow | $2-5 | Best quality |
| GPT-3.5 | Fast | $0.50-1 | Budget-friendly |
| Claude | Medium | $1-3 | Good reasoning |

---

## AGENTS AT A GLANCE

| Agent | Role | Output |
|-------|------|--------|
| Code | Developer | Clean Python code |
| Review | Reviewer | Quality feedback |
| Security | Auditor | Vulnerability report |
| BugFix | Specialist | Refactored code |
| Testing | QA Engineer | Test suite |
| Deployment | DevOps | Docker config |

---

## LLM PROVIDER COMPARISON

| Provider | Model | Speed | Quality | Cost |
|----------|-------|-------|---------|------|
| OpenAI | gpt-4 | Slow | Excellent | $$ |
| OpenAI | gpt-3.5 | Fast | Good | $ |
| Anthropic | Claude 3 | Medium | Excellent | $$ |
| Google | Gemini Pro | Fast | Good | $ |

---

## ENVIRONMENT VARIABLES

```bash
# Required (at least one)
OPENAI_API_KEY=sk-...           # For OpenAI
ANTHROPIC_API_KEY=sk-ant-...    # For Claude
GOOGLE_API_KEY=...              # For Gemini

# Optional
LOG_LEVEL=INFO
VERBOSE_LOGGING=false
USE_MOCK_LLM=false
```

---

## FILE STRUCTURE

```
backend/
├── agents_sdlc.py              ← Main system
├── examples.py                 ← Example usage
├── requirements.txt            ← Dependencies
├── .env.example                ← Config template
├── README.md                   ← Full documentation
├── ARCHITECTURE.md             ← Design docs
├── setup.sh                    ← Linux/macOS setup
├── setup.bat                   ← Windows setup
├── venv/                       ← Virtual environment
└── sdlc_output/               ← Generated artifacts
```

---

## EXTENDING THE SYSTEM

### Add Custom Tool
```python
from crewai_tools import tool

@tool
def my_tool(input_data: str) -> str:
    """Tool description."""
    return result

# Add to agent
agent = Agent(..., tools=[my_tool])
```

### Add Custom Agent
```python
def create_my_agent(self) -> Agent:
    return Agent(
        role="My Role",
        goal="My Goal",
        backstory="My Backstory",
        tools=[]
    )
```

### Add Custom Task
```python
def create_my_task(agent: Agent) -> Task:
    return Task(
        description="Task description",
        expected_output="Output format",
        agent=agent
    )
```

---

## PERFORMANCE TIPS

1. **Use GPT-3.5** for fast, cheap processing
2. **Lower temperature** (0.3-0.5) for consistency
3. **Run stages sequentially** (current default)
4. **Check token usage** in OpenAI dashboard
5. **Cache results** for repeated requirements

---

## USEFUL LINKS

- **OpenAI API**: https://platform.openai.com/api-keys
- **Anthropic Claude**: https://console.anthropic.com/
- **Google Gemini**: https://ai.google.dev/
- **CrewAI Docs**: https://docs.crewai.com/
- **Python Docs**: https://docs.python.org/3/

---

## KEY CONCEPTS

| Term | Definition |
|------|-----------|
| Agent | Autonomous AI entity with role and tools |
| Task | Specific work for an agent to complete |
| Crew | Collection of agents working together |
| Orchestrator | Manages workflow execution and state |
| Artifact | Generated output from a stage |
| LLM | Large Language Model (GPT, Claude, etc.) |

---

## WORKFLOW VISUALIZATION

```
Requirement
    ↓
[Code Agent] generates code
    ↓
[Review + Security] (parallel)
    ↓
[Bug Fix Agent] refactors
    ↓
[Testing Agent] creates tests
    ↓
[Deployment Agent] packages app
    ↓
Artifacts ready for use
```

---

## QUICK DEBUG CHECKLIST

- [ ] API key set in .env or environment
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Virtual environment activated
- [ ] Internet connection available
- [ ] API provider account active
- [ ] Check error messages carefully
- [ ] Review `workflow_history.json`

---

## NEXT STEPS

1. **Install**: Run setup script
2. **Configure**: Add API key to .env
3. **Test**: Run `python agents_sdlc.py`
4. **Explore**: Check `sdlc_output/` folder
5. **Customize**: Modify requirement in code
6. **Integrate**: Use in your projects

---

**Last Updated**: 2024  
**Version**: 1.0.0
