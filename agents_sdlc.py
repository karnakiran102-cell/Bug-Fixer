#!/usr/bin/env python3
"""
Multi-Agent Software Development Lifecycle (SDLC) System

This module implements a comprehensive multi-agent orchestration system that manages
the complete software development lifecycle, from code generation through deployment.

The system uses a lightweight local orchestration layer to coordinate six
specialized agents:
- Code Agent: Generates initial implementation
- Review Agent: Analyzes code quality and architecture
- Security Agent: Performs security audits
- Bug Fix Agent: Refactors code based on feedback
- Testing Agent: Creates comprehensive test suites
- Deployment Agent: Generates deployment artifacts

Usage:
    python agents_sdlc.py

Author: Senior AI Architect & Principal Python Developer
Created: 2024
"""

import os
import json
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Third-party imports
from pydantic import BaseModel, Field


# ============================================================================
# CONFIGURATION & ENUMS
# ============================================================================

class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

    def __post_init__(self):
        """Validate and set API keys from environment."""
        if self.api_key is None:
            env_map = {
                LLMProvider.OPENAI: "OPENAI_API_KEY",
                LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
                LLMProvider.GEMINI: "GOOGLE_API_KEY",
            }
            env_var = env_map.get(self.provider)
            if env_var:
                self.api_key = os.getenv(env_var)
                if not self.api_key:
                    raise ValueError(f"Missing environment variable: {env_var}")


class EnvironmentType(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# ============================================================================
# LOCAL AGENT COMPATIBILITY LAYER
# ============================================================================

def tool(func: Optional[Callable] = None, **metadata: Any) -> Callable:
    """
    Lightweight replacement for the CrewAI tool decorator.

    It preserves the public decorator shape used by this module while keeping the
    callable usable as a plain Python function.
    """
    def decorator(wrapped: Callable) -> Callable:
        wrapped.is_tool = True
        wrapped.tool_metadata = metadata
        return wrapped

    if func is None:
        return decorator
    return decorator(func)


@dataclass
class Agent:
    """
    Public compatibility type representing an autonomous SDLC agent.

    The fields mirror the CrewAI-style constructor used by the original module,
    with an optional LLM config attached by AgentFactory for local execution.
    """
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False
    tools: List[Callable] = field(default_factory=list)
    llm_config: Optional[LLMConfig] = None

    def __repr__(self) -> str:
        return f"Agent(role={self.role!r})"


@dataclass
class Task:
    """Public compatibility type representing work assigned to an agent."""
    description: str
    expected_output: str
    agent: Agent
    output_file: Optional[str] = None

    def __repr__(self) -> str:
        return f"Task(agent={self.agent.role!r})"


class Process(Enum):
    """Supported execution process modes."""
    sequential = "sequential"
    SEQUENTIAL = "sequential"


class LLMClient:
    """Small provider adapter for OpenAI, Anthropic, and Gemini."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def call(self, prompt: str) -> str:
        """Call the configured LLM provider with a single prompt."""
        if self.config.provider == LLMProvider.OPENAI:
            return self._call_openai(prompt)
        if self.config.provider == LLMProvider.ANTHROPIC:
            return self._call_anthropic(prompt)
        if self.config.provider == LLMProvider.GEMINI:
            return self._call_gemini(prompt)
        raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

    def _call_openai(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai") from exc

        client = OpenAI(api_key=self.config.api_key)
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content or ""

    def _call_anthropic(self, prompt: str) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError("Anthropic SDK not installed. Run: pip install anthropic") from exc

        client = anthropic.Anthropic(api_key=self.config.api_key)
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "text", None)
        )

    def _call_gemini(self, prompt: str) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "Google Generative AI SDK not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self.config.api_key)
        model = genai.GenerativeModel(self.config.model)
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            },
        )
        return getattr(response, "text", "") or ""


class Crew:
    """
    Minimal local CrewAI-compatible executor.

    Tasks are executed sequentially through the LLM config attached to their
    agent, or through an explicit llm_config passed to the crew.
    """

    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.sequential,
        verbose: bool = True,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self.llm_config = llm_config

    def kickoff(self) -> str:
        """Execute all tasks and return their combined text output."""
        if self.process not in (Process.sequential, Process.SEQUENTIAL):
            raise NotImplementedError("Only sequential process execution is supported")

        results: List[str] = []
        for task in self.tasks:
            result = self._execute_task(task)
            results.append(result)
            if task.output_file:
                with open(task.output_file, "w", encoding="utf-8") as output:
                    output.write(result)

        return "\n\n".join(results)

    def _execute_task(self, task: Task) -> str:
        llm_config = self._resolve_llm_config(task.agent)
        prompt = self._build_prompt(task)
        if self.verbose or task.agent.verbose:
            print(f"\n-> Agent: {task.agent.role}")
        return LLMClient(llm_config).call(prompt)

    def _resolve_llm_config(self, agent: Agent) -> LLMConfig:
        if self.llm_config:
            return self.llm_config
        if agent.llm_config:
            return agent.llm_config
        for candidate in self.agents:
            if candidate.llm_config:
                return candidate.llm_config
        raise ValueError(
            "No LLM configuration found. Create agents with AgentFactory or pass "
            "llm_config to Crew."
        )

    def _build_prompt(self, task: Task) -> str:
        tools = self._format_tools(task.agent.tools)
        return f"""Role: {task.agent.role}
Goal: {task.agent.goal}
Backstory:
{task.agent.backstory}

Available local tool references:
{tools}

Task:
{task.description}

Expected output:
{task.expected_output}
"""

    @staticmethod
    def _format_tools(tools: List[Callable]) -> str:
        if not tools:
            return "None"
        descriptions = []
        for item in tools:
            name = getattr(item, "__name__", "tool")
            doc = (getattr(item, "__doc__", "") or "").strip().splitlines()
            summary = doc[0].strip() if doc else "No description"
            descriptions.append(f"- {name}: {summary}")
        return "\n".join(descriptions)


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUTS
# ============================================================================

class CodeOutput(BaseModel):
    """Structured output from Code Agent."""
    code: str = Field(description="The generated Python code")
    documentation: str = Field(description="Code documentation and docstrings")
    dependencies: List[str] = Field(description="External dependencies required")
    architecture: str = Field(description="High-level architecture description")


class ReviewFeedback(BaseModel):
    """Structured feedback from Review Agent."""
    issues: List[Dict[str, str]] = Field(description="List of identified issues")
    suggestions: List[str] = Field(description="Improvement suggestions")
    severity_levels: Dict[str, int] = Field(
        description="Count of issues by severity (low, medium, high)"
    )
    overall_score: float = Field(description="Code quality score 0-100")


class SecurityAudit(BaseModel):
    """Structured security audit output."""
    vulnerabilities: List[Dict[str, str]] = Field(description="Found vulnerabilities")
    risk_score: float = Field(description="Overall risk score 0-100")
    recommendations: List[str] = Field(description="Security recommendations")
    compliance_notes: str = Field(description="Compliance and best practices notes")


class TestSuite(BaseModel):
    """Structured test suite output."""
    test_code: str = Field(description="Complete test code")
    test_cases: List[str] = Field(description="List of test case names")
    coverage_estimate: float = Field(description="Estimated code coverage 0-100")
    mock_data: str = Field(description="Mock data and fixtures")


class DeploymentArtifacts(BaseModel):
    """Structured deployment artifacts."""
    dockerfile: str = Field(description="Dockerfile content")
    requirements: str = Field(description="Python requirements.txt content")
    github_actions: str = Field(description="GitHub Actions CI/CD YAML")
    docker_compose: Optional[str] = Field(description="Docker Compose configuration")
    deployment_guide: str = Field(description="Deployment instructions")


# ============================================================================
# TOOLS FOR AGENTS
# ============================================================================

@tool
def analyze_code_quality(code: str) -> Dict[str, Any]:
    """
    Analyze code for quality metrics (complexity, readability, etc.).
    
    Args:
        code: Python code to analyze
        
    Returns:
        Dictionary with quality metrics
    """
    lines = code.split('\n')
    metrics = {
        "lines_of_code": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
        "comment_ratio": len([l for l in lines if l.strip().startswith('#')]) / max(1, len(lines)),
        "function_count": code.count('def '),
        "class_count": code.count('class '),
        "import_count": code.count('import '),
    }
    return metrics


@tool
def scan_security_vulnerabilities(code: str) -> Dict[str, Any]:
    """
    Scan code for common security vulnerabilities.
    
    Args:
        code: Python code to scan
        
    Returns:
        Dictionary with found vulnerabilities
    """
    vulnerabilities = []
    
    # Check for hardcoded secrets
    if any(keyword in code.lower() for keyword in ['password', 'api_key', 'secret', 'token']):
        if '=' in code and any(kw in code.lower() for kw in ['=', '"', "'"]):
            vulnerabilities.append({
                "type": "Hardcoded Secrets",
                "severity": "HIGH",
                "message": "Potential hardcoded credentials detected"
            })
    
    # Check for unsafe operations
    if 'eval(' in code or 'exec(' in code:
        vulnerabilities.append({
            "type": "Unsafe Code Execution",
            "severity": "CRITICAL",
            "message": "Use of eval() or exec() detected"
        })
    
    # Check for SQL injection risks
    if ('f"' in code or "f'" in code) and 'SELECT' in code.upper():
        vulnerabilities.append({
            "type": "SQL Injection Risk",
            "severity": "HIGH",
            "message": "F-string formatting in SQL queries detected"
        })
    
    # Check for insecure random
    if 'random.' in code and 'secrets.' not in code:
        vulnerabilities.append({
            "type": "Weak Random Generation",
            "severity": "MEDIUM",
            "message": "Consider using 'secrets' module instead of 'random' for security"
        })
    
    return {
        "vulnerabilities": vulnerabilities,
        "total_issues": len(vulnerabilities),
        "critical_count": sum(1 for v in vulnerabilities if v.get("severity") == "CRITICAL"),
    }


@tool
def generate_test_template(code: str, test_type: str = "unit") -> str:
    """
    Generate test template for given code.
    
    Args:
        code: Python code to test
        test_type: Type of test (unit, integration, e2e)
        
    Returns:
        Test template string
    """
    functions = []
    classes = []
    
    lines = code.split('\n')
    for line in lines:
        if line.strip().startswith('def '):
            func_name = line.split('def ')[1].split('(')[0]
            functions.append(func_name)
        elif line.strip().startswith('class '):
            class_name = line.split('class ')[1].split('(')[0].split(':')[0]
            classes.append(class_name)
    
    template = f"""
import pytest
from unittest.mock import Mock, patch, MagicMock

# Test fixtures
@pytest.fixture
def setup_test_data():
    '''Setup test data.'''
    return {{'test_key': 'test_value'}}

# Test classes
"""
    
    for class_name in classes:
        template += f"""
class Test{class_name}:
    '''Tests for {class_name} class.'''
    
    def test_initialization(self):
        '''Test {class_name} initialization.'''
        pass
"""
    
    for func_name in functions:
        template += f"""
def test_{func_name}():
    '''Test {func_name} function.'''
    pass
"""
    
    return template


@tool
def validate_deployment_config(config: str) -> Dict[str, Any]:
    """
    Validate deployment configuration files.
    
    Args:
        config: Configuration content (Dockerfile, docker-compose, etc.)
        
    Returns:
        Validation results
    """
    validation_result = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "recommendations": []
    }
    
    if 'FROM' in config:  # Dockerfile
        if 'HEALTHCHECK' not in config:
            validation_result["recommendations"].append(
                "Add HEALTHCHECK instruction for container health monitoring"
            )
        if 'USER' not in config:
            validation_result["warnings"].append(
                "Consider running container as non-root user"
            )
    
    return validation_result


# ============================================================================
# AGENT FACTORY
# ============================================================================

class AgentFactory:
    """Factory for creating configured agents."""
    
    def __init__(self, llm_config: LLMConfig):
        """
        Initialize agent factory with LLM configuration.
        
        Args:
            llm_config: LLM configuration object
        """
        self.llm_config = llm_config
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup LLM based on provider configuration."""
        if self.llm_config.provider == LLMProvider.OPENAI:
            os.environ["OPENAI_API_KEY"] = self.llm_config.api_key
            os.environ["OPENAI_MODEL_NAME"] = self.llm_config.model
        elif self.llm_config.provider == LLMProvider.ANTHROPIC:
            os.environ["ANTHROPIC_API_KEY"] = self.llm_config.api_key
        elif self.llm_config.provider == LLMProvider.GEMINI:
            os.environ["GOOGLE_API_KEY"] = self.llm_config.api_key
    
    def create_code_agent(self) -> Agent:
        """
        Create the Code Agent (The Developer).
        
        Responsible for: Taking user requirements and writing clean Python code.
        
        Returns:
            Configured Code Agent
        """
        return Agent(
            role="Senior Python Developer",
            goal="Write clean, well-documented, production-ready Python code that fully implements the user requirements",
            backstory="""You are a highly experienced Python developer with 15+ years of experience.
            You excel at:
            - Writing clean, pythonic code following PEP-8
            - Creating comprehensive docstrings and comments
            - Designing scalable and maintainable architectures
            - Implementing best practices for error handling
            - Using appropriate design patterns
            
            Your code should be:
            - Well-organized with clear separation of concerns
            - Type-hinted for better IDE support
            - Fully documented with docstrings
            - Ready for immediate code review""",
            verbose=True,
            allow_delegation=False,
            llm_config=self.llm_config,
            tools=[analyze_code_quality]
        )
    
    def create_review_agent(self) -> Agent:
        """
        Create the Review Agent (Senior Code Reviewer).
        
        Responsible for: Code quality analysis, PEP-8 compliance, architecture review.
        
        Returns:
            Configured Review Agent
        """
        return Agent(
            role="Senior Code Reviewer",
            goal="Provide comprehensive code review feedback focusing on quality, maintainability, and best practices",
            backstory="""You are a Principal Engineer with extensive experience reviewing code across thousands of projects.
            Your expertise includes:
            - PEP-8 compliance and Python style guidelines
            - Code smell detection
            - Architectural pattern review
            - Performance optimization identification
            - Maintainability assessment
            
            You provide constructive, actionable feedback that helps developers improve their craft.
            Your reviews are thorough but respectful, always explaining the 'why' behind suggestions.""",
            verbose=True,
            allow_delegation=False,
            llm_config=self.llm_config,
            tools=[analyze_code_quality]
        )
    
    def create_security_agent(self) -> Agent:
        """
        Create the Security Agent (AppSec Engineer).
        
        Responsible for: Security vulnerability detection, compliance verification.
        
        Returns:
            Configured Security Agent
        """
        return Agent(
            role="Application Security Engineer",
            goal="Identify and document security vulnerabilities, compliance issues, and recommend security improvements",
            backstory="""You are a seasoned AppSec engineer with certifications in security architecture.
            Your expertise spans:
            - OWASP Top 10 vulnerabilities
            - Secure coding practices
            - Dependency vulnerability analysis
            - Encryption and secrets management
            - Authentication and authorization patterns
            - Compliance requirements (GDPR, HIPAA, SOC2)
            
            You conduct thorough security audits and provide clear remediation guidance.""",
            verbose=True,
            allow_delegation=False,
            llm_config=self.llm_config,
            tools=[scan_security_vulnerabilities]
        )
    
    def create_bugfix_agent(self) -> Agent:
        """
        Create the Bug Fix Agent (Refactoring Specialist).
        
        Responsible for: Implementing fixes from review and security feedback.
        
        Returns:
            Configured Bug Fix Agent
        """
        return Agent(
            role="Code Refactoring Specialist",
            goal="Implement all feedback from reviewers and security audits, producing improved and secure code",
            backstory="""You are an expert refactoring specialist known for transforming code quality.
            Your strengths:
            - Implementing complex refactoring while maintaining functionality
            - Applying design patterns to improve architecture
            - Writing backward-compatible updates
            - Comprehensive regression testing mindset
            - Clear documentation of changes
            
            You take feedback constructively and produce code that incorporates all suggestions
            while maintaining the original functionality and intent.""",
            verbose=True,
            allow_delegation=False,
            llm_config=self.llm_config,
            tools=[analyze_code_quality, scan_security_vulnerabilities]
        )
    
    def create_testing_agent(self) -> Agent:
        """
        Create the Testing Agent (QA Engineer).
        
        Responsible for: Comprehensive test suite creation and coverage analysis.
        
        Returns:
            Configured Testing Agent
        """
        return Agent(
            role="QA Engineer & Test Architect",
            goal="Create comprehensive test suites with high code coverage and clear test documentation",
            backstory="""You are a testing expert with deep experience in pytest, unittest, and test design.
            Your expertise includes:
            - Test-driven development (TDD)
            - Unit, integration, and end-to-end testing
            - Mock and fixture creation
            - Test coverage analysis
            - Performance and load testing
            - CI/CD pipeline integration
            
            You create tests that:
            - Cover happy paths and edge cases
            - Are maintainable and clear
            - Serve as living documentation
            - Catch regressions early""",
            verbose=True,
            allow_delegation=False,
            llm_config=self.llm_config,
            tools=[generate_test_template]
        )
    
    def create_deployment_agent(self) -> Agent:
        """
        Create the Deployment Agent (DevOps Engineer).
        
        Responsible for: Generating deployment artifacts and CI/CD configurations.
        
        Returns:
            Configured Deployment Agent
        """
        return Agent(
            role="DevOps Engineer",
            goal="Create production-ready deployment configurations and CI/CD pipelines for the application",
            backstory="""You are a DevOps architect with expertise in containerization and infrastructure as code.
            Your expertise:
            - Docker and container orchestration
            - Kubernetes deployments
            - GitHub Actions and CI/CD automation
            - Infrastructure as Code (Terraform, CloudFormation)
            - Monitoring and logging setup
            - Security in deployment pipelines
            
            You produce deployment configurations that are:
            - Production-ready
            - Secure and audited
            - Scalable and maintainable
            - Well-documented with clear deployment instructions""",
            verbose=True,
            allow_delegation=False,
            llm_config=self.llm_config,
            tools=[validate_deployment_config]
        )


# ============================================================================
# TASK FACTORY
# ============================================================================

class TaskFactory:
    """Factory for creating orchestrated tasks."""
    
    @staticmethod
    def create_code_task(agent: Agent, requirement: str) -> Task:
        """
        Create task for Code Agent.
        
        Args:
            agent: The Code Agent
            requirement: User requirement/specification
            
        Returns:
            Configured Code Generation Task
        """
        return Task(
            description=f"""Analyze the following requirement and write complete, production-ready Python code:

REQUIREMENT:
{requirement}

Your output should include:
1. Complete, working Python code with all necessary imports
2. Comprehensive docstrings for all functions and classes
3. Type hints throughout
4. Error handling for edge cases
5. Clear comments explaining complex logic
6. A list of external dependencies (if any)
7. Brief architecture overview

IMPORTANT: Output ONLY valid Python code. Ensure all code is syntactically correct and runnable.""",
            expected_output="Complete, documented Python code ready for review",
            agent=agent,
            output_file="code_output.py"
        )
    
    @staticmethod
    def create_review_task(agent: Agent, code: str) -> Task:
        """
        Create task for Review Agent.
        
        Args:
            agent: The Review Agent
            code: Code to review
            
        Returns:
            Configured Code Review Task
        """
        return Task(
            description=f"""Perform a comprehensive code review of the following Python code:

CODE TO REVIEW:
```python
{code}
```

Evaluate the code on these criteria:
1. PEP-8 Compliance: Style, naming conventions, formatting
2. Code Quality: Readability, maintainability, complexity
3. Architecture: Design patterns, separation of concerns
4. Error Handling: Exception handling, edge cases
5. Documentation: Docstrings, comments, clarity
6. Performance: Optimization opportunities
7. Testing: Testability of the code

Provide:
- A detailed list of issues found (with severity: low/medium/high)
- Specific, actionable suggestions for improvement
- An overall code quality score (0-100)
- Positive aspects of the code""",
            expected_output="Comprehensive review with issues, suggestions, and quality score",
            agent=agent
        )
    
    @staticmethod
    def create_security_task(agent: Agent, code: str) -> Task:
        """
        Create task for Security Agent.
        
        Args:
            agent: The Security Agent
            code: Code to audit
            
        Returns:
            Configured Security Audit Task
        """
        return Task(
            description=f"""Perform a security audit of the following Python code:

CODE TO AUDIT:
```python
{code}
```

Analyze for:
1. OWASP Top 10 vulnerabilities relevant to Python
2. Hardcoded secrets (passwords, API keys, tokens)
3. SQL injection risks
4. Input validation issues
5. Unsafe deserialization (pickle, yaml, etc.)
6. Cryptography weaknesses
7. Dependency vulnerabilities
8. Authentication/authorization issues
9. Data exposure risks
10. Error handling that reveals sensitive info

Provide:
- List of found vulnerabilities with severity (CRITICAL/HIGH/MEDIUM/LOW)
- Overall risk score (0-100, where 100 is critical)
- Specific remediation recommendations
- Compliance considerations (GDPR, etc.)""",
            expected_output="Security audit report with vulnerabilities and recommendations",
            agent=agent
        )
    
    @staticmethod
    def create_bugfix_task(agent: Agent, original_code: str, review_feedback: str, security_feedback: str) -> Task:
        """
        Create task for Bug Fix Agent.
        
        Args:
            agent: The Bug Fix Agent
            original_code: The original code
            review_feedback: Feedback from code review
            security_feedback: Feedback from security audit
            
        Returns:
            Configured Refactoring Task
        """
        return Task(
            description=f"""Refactor the following Python code based on review and security feedback:

ORIGINAL CODE:
```python
{original_code}
```

CODE REVIEW FEEDBACK:
{review_feedback}

SECURITY AUDIT FEEDBACK:
{security_feedback}

Your task:
1. Address ALL issues identified in the review feedback
2. Fix ALL security vulnerabilities identified in the audit
3. Maintain the original functionality
4. Improve code quality and maintainability
5. Ensure all changes are well-documented

Output the complete refactored code with:
- All improvements implemented
- Clear comments explaining changes
- Maintained type hints and docstrings
- Enhanced error handling if needed""",
            expected_output="Refactored Python code addressing all feedback",
            agent=agent,
            output_file="refactored_code.py"
        )
    
    @staticmethod
    def create_testing_task(agent: Agent, code: str) -> Task:
        """
        Create task for Testing Agent.
        
        Args:
            agent: The Testing Agent
            code: Code to test
            
        Returns:
            Configured Testing Task
        """
        return Task(
            description=f"""Create a comprehensive test suite for the following Python code:

CODE TO TEST:
```python
{code}
```

Create tests that:
1. Test all functions and methods
2. Cover happy paths and edge cases
3. Handle error conditions
4. Use appropriate mocking where needed
5. Include test fixtures and setup/teardown
6. Test integration between components

Output:
- Complete test code using pytest
- Test cases for all major functions/classes
- Mock data and fixtures
- Estimated code coverage percentage
- Notes on untestable sections (if any)

Format: Valid, runnable pytest code""",
            expected_output="Complete pytest test suite with coverage analysis",
            agent=agent,
            output_file="test_suite.py"
        )
    
    @staticmethod
    def create_deployment_task(agent: Agent, code: str, test_code: str, requirements: str = "") -> Task:
        """
        Create task for Deployment Agent.
        
        Args:
            agent: The Deployment Agent
            code: The application code
            test_code: The test suite
            requirements: List of dependencies
            
        Returns:
            Configured Deployment Task
        """
        return Task(
            description=f"""Create deployment artifacts for the following application:

APPLICATION CODE:
```python
{code}
```

TEST SUITE:
```python
{test_code}
```

DEPENDENCIES:
{requirements or "Standard library only or minimal external dependencies"}

Create the following deployment artifacts:

1. **Dockerfile**: Production-ready Docker image
   - Appropriate base image (python:3.11-slim)
   - Multi-stage build if beneficial
   - Health checks
   - Non-root user execution
   - Security best practices

2. **requirements.txt**: Python dependencies
   - All external packages with pinned versions
   - Comments explaining purpose of each

3. **GitHub Actions CI/CD**: Complete workflow YAML
   - Test on multiple Python versions
   - Code quality checks
   - Security scanning
   - Build and push Docker image
   - Deploy to staging/production

4. **docker-compose.yml** (if applicable):
   - Service definitions
   - Environment variables
   - Volume mounts
   - Network configuration

5. **Deployment Guide**: Step-by-step instructions
   - Prerequisites
   - Environment setup
   - Deployment steps
   - Rollback procedures
   - Monitoring setup""",
            expected_output="Complete deployment artifacts and guide",
            agent=agent,
            output_file="deployment_artifacts.md"
        )


# ============================================================================
# SDLC ORCHESTRATOR
# ============================================================================

class SDLCOrchestrator:
    """Main orchestrator for the multi-agent SDLC system."""
    
    def __init__(self, llm_config: LLMConfig):
        """
        Initialize the SDLC orchestrator.
        
        Args:
            llm_config: LLM configuration
            
        Raises:
            ValueError: If LLM configuration is invalid
        """
        self.llm_config = llm_config
        self.agent_factory = AgentFactory(llm_config)
        self.task_factory = TaskFactory()
        self.workflow_history: List[Dict[str, Any]] = []
        self.artifacts: Dict[str, Any] = {}
    
    def log_step(self, step_name: str, output: str, status: str = "success"):
        """
        Log a step in the workflow.
        
        Args:
            step_name: Name of the workflow step
            output: Output from the step
            status: Status of the step (success/warning/error)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "status": status,
            "output_preview": output[:500] + "..." if len(output) > 500 else output
        }
        self.workflow_history.append(entry)
        print(f"\n[{status.upper()}] {step_name}")
        print(f"Output preview: {entry['output_preview']}\n")
    
    def execute_workflow(self, requirement: str, environment: EnvironmentType = EnvironmentType.DEVELOPMENT) -> Dict[str, Any]:
        """
        Execute the complete SDLC workflow.
        
        Args:
            requirement: User requirement/specification
            environment: Deployment environment
            
        Returns:
            Dictionary containing all workflow outputs and artifacts
            
        Raises:
            Exception: If any critical step fails
        """
        print("\n" + "="*80)
        print("MULTI-AGENT SDLC SYSTEM - WORKFLOW EXECUTION")
        print("="*80)
        print(f"Requirement: {requirement}")
        print(f"Environment: {environment.value}")
        print(f"LLM Provider: {self.llm_config.provider.value}")
        print("="*80 + "\n")
        
        try:
            # STAGE 1: CODE GENERATION
            print("\n--- STAGE 1: CODE GENERATION ---\n")
            code_agent = self.agent_factory.create_code_agent()
            code_task = self.task_factory.create_code_task(code_agent, requirement)
            
            code_crew = Crew(
                agents=[code_agent],
                tasks=[code_task],
                process=Process.sequential,
                verbose=True
            )
            
            code_output = code_crew.kickoff()
            code_result = str(code_output)
            self.artifacts["generated_code"] = code_result
            self.log_step("Code Generation", code_result)
            
            # STAGE 2: PARALLEL REVIEW & SECURITY (Can be parallel)
            print("\n--- STAGE 2: PARALLEL REVIEW & SECURITY AUDIT ---\n")
            
            review_agent = self.agent_factory.create_review_agent()
            review_task = self.task_factory.create_review_task(review_agent, code_result)
            
            security_agent = self.agent_factory.create_security_agent()
            security_task = self.task_factory.create_security_task(security_agent, code_result)
            
            review_crew = Crew(
                agents=[review_agent, security_agent],
                tasks=[review_task, security_task],
                process=Process.sequential,  # Sequential due to dependencies
                verbose=True
            )
            
            review_output = review_crew.kickoff()
            review_result = str(review_output)
            self.artifacts["review_feedback"] = review_result
            self.log_step("Code Review & Security Audit", review_result)
            
            # STAGE 3: BUG FIXING & REFACTORING
            print("\n--- STAGE 3: BUG FIXING & REFACTORING ---\n")
            
            bugfix_agent = self.agent_factory.create_bugfix_agent()
            bugfix_task = self.task_factory.create_bugfix_task(
                bugfix_agent,
                code_result,
                review_result,
                review_result  # Using combined feedback
            )
            
            bugfix_crew = Crew(
                agents=[bugfix_agent],
                tasks=[bugfix_task],
                process=Process.sequential,
                verbose=True
            )
            
            bugfix_output = bugfix_crew.kickoff()
            bugfix_result = str(bugfix_output)
            self.artifacts["refactored_code"] = bugfix_result
            self.log_step("Code Refactoring", bugfix_result)
            
            # STAGE 4: TEST SUITE GENERATION
            print("\n--- STAGE 4: TEST SUITE GENERATION ---\n")
            
            testing_agent = self.agent_factory.create_testing_agent()
            testing_task = self.task_factory.create_testing_task(testing_agent, bugfix_result)
            
            testing_crew = Crew(
                agents=[testing_agent],
                tasks=[testing_task],
                process=Process.sequential,
                verbose=True
            )
            
            testing_output = testing_crew.kickoff()
            testing_result = str(testing_output)
            self.artifacts["test_suite"] = testing_result
            self.log_step("Test Suite Generation", testing_result)
            
            # STAGE 5: DEPLOYMENT PREPARATION
            print("\n--- STAGE 5: DEPLOYMENT PREPARATION ---\n")
            
            deployment_agent = self.agent_factory.create_deployment_agent()
            deployment_task = self.task_factory.create_deployment_task(
                deployment_agent,
                bugfix_result,
                testing_result
            )
            
            deployment_crew = Crew(
                agents=[deployment_agent],
                tasks=[deployment_task],
                process=Process.sequential,
                verbose=True
            )
            
            deployment_output = deployment_crew.kickoff()
            deployment_result = str(deployment_output)
            self.artifacts["deployment_artifacts"] = deployment_result
            self.log_step("Deployment Artifact Generation", deployment_result)
            
            # FINAL SUMMARY
            self._generate_workflow_summary()
            
            return self.artifacts
            
        except Exception as e:
            self.log_step("Workflow Execution", str(e), status="error")
            raise


    def _generate_workflow_summary(self):
        """Generate and display workflow execution summary."""
        print("\n" + "="*80)
        print("WORKFLOW EXECUTION SUMMARY")
        print("="*80)
        print(f"Total Stages Completed: {len(self.workflow_history)}")
        print(f"Execution Time: {datetime.now().isoformat()}")
        print("\nWorkflow History:")
        for i, entry in enumerate(self.workflow_history, 1):
            print(f"{i}. [{entry['status'].upper()}] {entry['step']}")
            print(f"   Time: {entry['timestamp']}")
        print("="*80 + "\n")
    
    def save_artifacts(self, output_dir: str = "./sdlc_output"):
        """
        Save all artifacts to disk.
        
        Args:
            output_dir: Directory to save artifacts
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for artifact_name, artifact_content in self.artifacts.items():
            filename = f"{output_dir}/{artifact_name}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(str(artifact_content))
            print(f"Saved: {filename}")
        
        # Save workflow history
        history_file = f"{output_dir}/workflow_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.workflow_history, f, indent=2)
        print(f"Saved: {history_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point for the SDLC system.
    
    Demonstrates the complete workflow with a sample requirement.
    """
    
    # Configure LLM - Using OpenAI by default
    # You can switch providers by changing LLMProvider
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper execution
        temperature=0.7
    )
    
    # Alternative providers:
    # llm_config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-sonnet-20240229")
    # llm_config = LLMConfig(provider=LLMProvider.GEMINI, model="gemini-pro")
    
    # Sample requirement
    sample_requirement = """
    Build a simple Python calculator API with the following features:
    1. Basic arithmetic operations (add, subtract, multiply, divide)
    2. Input validation for numeric values
    3. Error handling for division by zero
    4. Detailed logging of calculations
    5. RESTful API endpoint using Flask
    6. Should be production-ready with proper error messages
    """
    
    # Initialize orchestrator
    orchestrator = SDLCOrchestrator(llm_config)
    
    # Execute the complete SDLC workflow
    try:
        artifacts = orchestrator.execute_workflow(
            requirement=sample_requirement,
            environment=EnvironmentType.PRODUCTION
        )
        
        # Save all outputs
        orchestrator.save_artifacts("./sdlc_output")
        
        print("\nSUCCESS: SDLC Workflow Completed Successfully!")
        print("Check the 'sdlc_output' directory for all generated artifacts.")
        
    except Exception as e:
        print(f"\nERROR: Workflow failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
