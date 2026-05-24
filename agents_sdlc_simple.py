#!/usr/bin/env python3
"""
Multi-Agent Software Development Lifecycle (SDLC) System
Pure Python Implementation (No External Framework Dependencies)

This module implements a comprehensive multi-agent orchestration system that manages
the complete software development lifecycle using pure Python with OpenAI/Anthropic APIs.

Features:
- 6 specialized autonomous agents
- Multi-LLM provider support (OpenAI, Anthropic, Google)
- 5-stage SDLC workflow
- Full type hints and documentation
- No heavy framework dependencies (no CrewAI, numpy, etc.)

Usage:
    python agents_sdlc_simple.py

Author: Senior AI Architect & Principal Python Developer
Created: 2024
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback


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
    max_tokens: int = 2048

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
# AGENT DEFINITION
# ============================================================================

@dataclass
class Agent:
    """
    Represents an autonomous agent with specific role and expertise.
    
    Attributes:
        role: The agent's professional role
        goal: What the agent aims to achieve
        backstory: Background and expertise of the agent
        tools: List of tool functions available to the agent
    """
    role: str
    goal: str
    backstory: str
    tools: List[Callable] = field(default_factory=list)
    verbose: bool = True
    allow_delegation: bool = False

    def __repr__(self) -> str:
        return f"Agent(role='{self.role}')"


@dataclass
class Task:
    """
    Represents a specific task for an agent to complete.
    
    Attributes:
        description: Detailed task description
        expected_output: Expected output format and content
        agent: The agent responsible for this task
        output_file: Optional file to save output
    """
    description: str
    expected_output: str
    agent: Agent
    output_file: Optional[str] = None

    def __repr__(self) -> str:
        return f"Task(agent='{self.agent.role}')"


# ============================================================================
# LLM INTERFACE
# ============================================================================

class LLMClient:
    """Interface for calling LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM client."""
        self.config = config
        self._setup_provider()
    
    def _setup_provider(self):
        """Setup provider-specific configuration."""
        if self.config.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.config.api_key)
                self.client_type = "openai"
            except ImportError:
                raise ImportError("OpenAI not installed. Run: pip install openai")
        
        elif self.config.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config.api_key)
                self.client_type = "anthropic"
            except ImportError:
                raise ImportError("Anthropic not installed. Run: pip install anthropic")
        
        elif self.config.provider == LLMProvider.GEMINI:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.api_key)
                self.client_type = "gemini"
            except ImportError:
                raise ImportError("Google Generative AI not installed. Run: pip install google-generativeai")
    
    def call(self, prompt: str) -> str:
        """
        Call the LLM with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM response
        """
        try:
            if self.config.provider == LLMProvider.OPENAI:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content
            
            elif self.config.provider == LLMProvider.ANTHROPIC:
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.config.provider == LLMProvider.GEMINI:
                import google.generativeai as genai
                model = genai.GenerativeModel(self.config.model)
                response = model.generate_content(prompt)
                return response.text
        
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")


# ============================================================================
# AGENT FACTORY
# ============================================================================

class AgentFactory:
    """Factory for creating pre-configured agents."""
    
    @staticmethod
    def create_code_agent() -> Agent:
        """Create the Code Agent (Developer)."""
        return Agent(
            role="Senior Python Developer",
            goal="Write clean, well-documented, production-ready Python code that fully implements the user requirements",
            backstory="""You are a highly experienced Python developer with 15+ years of expertise.
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
            allow_delegation=False
        )
    
    @staticmethod
    def create_review_agent() -> Agent:
        """Create the Review Agent (Code Reviewer)."""
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

You provide constructive, actionable feedback that helps developers improve their craft.""",
            verbose=True,
            allow_delegation=False
        )
    
    @staticmethod
    def create_security_agent() -> Agent:
        """Create the Security Agent (AppSec Engineer)."""
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
            allow_delegation=False
        )
    
    @staticmethod
    def create_bugfix_agent() -> Agent:
        """Create the Bug Fix Agent (Refactoring Specialist)."""
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

You take feedback constructively and produce code that incorporates all suggestions.""",
            verbose=True,
            allow_delegation=False
        )
    
    @staticmethod
    def create_testing_agent() -> Agent:
        """Create the Testing Agent (QA Engineer)."""
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

You create tests that cover happy paths and edge cases.""",
            verbose=True,
            allow_delegation=False
        )
    
    @staticmethod
    def create_deployment_agent() -> Agent:
        """Create the Deployment Agent (DevOps Engineer)."""
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

You produce deployment configurations that are production-ready and well-documented.""",
            verbose=True,
            allow_delegation=False
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
        """
        self.llm_config = llm_config
        self.llm_client = LLMClient(llm_config)
        self.agent_factory = AgentFactory()
        self.workflow_history: List[Dict[str, Any]] = []
        self.artifacts: Dict[str, Any] = {}
    
    def log_step(self, step_name: str, output: str, status: str = "success"):
        """Log a workflow step."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "status": status,
            "output_preview": output[:300] + "..." if len(output) > 300 else output
        }
        self.workflow_history.append(entry)
        
        status_icon = "✓" if status == "success" else "✗" if status == "error" else "⚠"
        print(f"\n[{status_icon} {status.upper()}] {step_name}")
        print(f"Output preview: {entry['output_preview']}\n")
    
    def execute_agent_task(self, agent: Agent, task: Task) -> str:
        """
        Execute a task with an agent.
        
        Args:
            agent: The agent to execute the task
            task: The task to execute
            
        Returns:
            The agent's response
        """
        print(f"\n→ Agent: {agent.role}")
        print(f"  Goal: {agent.goal}")
        print(f"  Task: {task.description[:100]}...")
        
        # Create the prompt
        prompt = f"""Role: {agent.role}
Goal: {agent.goal}
Backstory: {agent.backstory}

Task:
{task.description}

Expected Output Format:
{task.expected_output}

Please complete this task and provide the output in the exact format specified."""
        
        try:
            response = self.llm_client.call(prompt)
            return response
        except Exception as e:
            print(f"Error executing agent task: {e}")
            raise
    
    def execute_workflow(self, requirement: str, environment: EnvironmentType = EnvironmentType.DEVELOPMENT) -> Dict[str, Any]:
        """
        Execute the complete SDLC workflow.
        
        Args:
            requirement: User requirement/specification
            environment: Deployment environment
            
        Returns:
            Dictionary containing all workflow outputs and artifacts
        """
        print("\n" + "="*80)
        print("MULTI-AGENT SDLC SYSTEM - WORKFLOW EXECUTION")
        print("="*80)
        print(f"Requirement: {requirement[:100]}...")
        print(f"Environment: {environment.value}")
        print(f"LLM Provider: {self.llm_config.provider.value}")
        print(f"Model: {self.llm_config.model}")
        print("="*80 + "\n")
        
        try:
            # STAGE 1: CODE GENERATION
            print("\n" + "="*80)
            print("STAGE 1: CODE GENERATION")
            print("="*80)
            
            code_agent = self.agent_factory.create_code_agent()
            code_task = Task(
                description=f"""Analyze and code the following requirement:

{requirement}

Provide ONLY the complete, working Python code with:
1. All necessary imports
2. Comprehensive docstrings
3. Type hints throughout
4. Error handling
5. Clear comments""",
                expected_output="Complete, documented Python code",
                agent=code_agent
            )
            
            code_result = self.execute_agent_task(code_agent, code_task)
            self.artifacts["generated_code"] = code_result
            self.log_step("Code Generation", code_result)
            
            # STAGE 2: CODE REVIEW
            print("\n" + "="*80)
            print("STAGE 2: CODE REVIEW & SECURITY AUDIT")
            print("="*80)
            
            review_agent = self.agent_factory.create_review_agent()
            review_task = Task(
                description=f"""Review the following Python code:

```python
{code_result}
```

Provide detailed feedback on:
1. PEP-8 compliance
2. Code quality and readability
3. Architecture and design patterns
4. Error handling
5. Documentation
6. Performance issues""",
                expected_output="List of issues with severity levels and improvement suggestions",
                agent=review_agent
            )
            
            review_result = self.execute_agent_task(review_agent, review_task)
            self.artifacts["review_feedback"] = review_result
            self.log_step("Code Review", review_result)
            
            # STAGE 3: SECURITY AUDIT
            security_agent = self.agent_factory.create_security_agent()
            security_task = Task(
                description=f"""Perform a security audit of this Python code:

```python
{code_result}
```

Check for:
1. OWASP Top 10 vulnerabilities
2. Hardcoded secrets
3. SQL injection risks
4. Input validation issues
5. Unsafe operations
6. Compliance issues""",
                expected_output="Security vulnerabilities list with risk scores and recommendations",
                agent=security_agent
            )
            
            security_result = self.execute_agent_task(security_agent, security_task)
            self.artifacts["security_audit"] = security_result
            self.log_step("Security Audit", security_result)
            
            # STAGE 4: BUG FIXING & REFACTORING
            print("\n" + "="*80)
            print("STAGE 3: BUG FIXING & REFACTORING")
            print("="*80)
            
            bugfix_agent = self.agent_factory.create_bugfix_agent()
            bugfix_task = Task(
                description=f"""Refactor the following code based on the review and security feedback:

ORIGINAL CODE:
```python
{code_result}
```

REVIEW FEEDBACK:
{review_result}

SECURITY FEEDBACK:
{security_result}

Create improved code that addresses all issues. Output ONLY the complete refactored code.""",
                expected_output="Refactored Python code addressing all feedback",
                agent=bugfix_agent
            )
            
            bugfix_result = self.execute_agent_task(bugfix_agent, bugfix_task)
            self.artifacts["refactored_code"] = bugfix_result
            self.log_step("Code Refactoring", bugfix_result)
            
            # STAGE 5: TEST GENERATION
            print("\n" + "="*80)
            print("STAGE 4: TEST SUITE GENERATION")
            print("="*80)
            
            testing_agent = self.agent_factory.create_testing_agent()
            testing_task = Task(
                description=f"""Create comprehensive pytest tests for:

```python
{bugfix_result}
```

Include:
1. Unit tests for all functions
2. Test fixtures and mocks
3. Edge case coverage
4. Error condition tests""",
                expected_output="Complete pytest test suite code",
                agent=testing_agent
            )
            
            testing_result = self.execute_agent_task(testing_agent, testing_task)
            self.artifacts["test_suite"] = testing_result
            self.log_step("Test Suite Generation", testing_result)
            
            # STAGE 6: DEPLOYMENT
            print("\n" + "="*80)
            print("STAGE 5: DEPLOYMENT CONFIGURATION")
            print("="*80)
            
            deployment_agent = self.agent_factory.create_deployment_agent()
            deployment_task = Task(
                description=f"""Create deployment artifacts for this application:

APPLICATION CODE:
```python
{bugfix_result}
```

Generate:
1. Dockerfile for containerization
2. requirements.txt with dependencies
3. GitHub Actions CI/CD workflow YAML
4. docker-compose.yml if applicable
5. Deployment guide with instructions""",
                expected_output="Deployment artifacts (Dockerfile, CI/CD, docker-compose, guide)",
                agent=deployment_agent
            )
            
            deployment_result = self.execute_agent_task(deployment_agent, deployment_task)
            self.artifacts["deployment_artifacts"] = deployment_result
            self.log_step("Deployment Configuration", deployment_result)
            
            # SUMMARY
            self._generate_workflow_summary()
            
            return self.artifacts
        
        except Exception as e:
            self.log_step("Workflow Execution", str(e), status="error")
            print(f"\nError traceback:")
            traceback.print_exc()
            raise
    
    def _generate_workflow_summary(self):
        """Generate workflow execution summary."""
        print("\n" + "="*80)
        print("WORKFLOW EXECUTION SUMMARY")
        print("="*80)
        print(f"Total Stages: {len(self.workflow_history)}")
        print(f"Completion Time: {datetime.now().isoformat()}")
        print("\nWorkflow Timeline:")
        for i, entry in enumerate(self.workflow_history, 1):
            print(f"{i}. [{entry['status'].upper()}] {entry['step']}")
        print("="*80 + "\n")
    
    def save_artifacts(self, output_dir: str = "./sdlc_output"):
        """Save all artifacts to disk."""
        os.makedirs(output_dir, exist_ok=True)
        
        for artifact_name, artifact_content in self.artifacts.items():
            filename = f"{output_dir}/{artifact_name}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(str(artifact_content))
            print(f"✓ Saved: {filename}")
        
        # Save workflow history
        history_file = f"{output_dir}/workflow_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.workflow_history, f, indent=2)
        print(f"✓ Saved: {history_file}")
        print(f"\nAll artifacts saved to: {output_dir}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point for the SDLC system."""
    
    # Configure LLM
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-3.5-turbo",  # Using turbo for faster/cheaper execution
        temperature=0.7
    )
    
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
    
    # Execute workflow
    try:
        artifacts = orchestrator.execute_workflow(
            requirement=sample_requirement,
            environment=EnvironmentType.PRODUCTION
        )
        
        # Save results
        orchestrator.save_artifacts("./sdlc_output")
        
        print("\n" + "="*80)
        print("✓ SDLC WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nAll artifacts saved to './sdlc_output' directory")
        print("\nGenerated files:")
        for filename in os.listdir("./sdlc_output"):
            print(f"  - {filename}")
        
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        raise


if __name__ == "__main__":
    main()
