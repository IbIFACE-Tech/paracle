"""Code Creation Capability for MetaAgent.

LLM-powered code generation and manipulation:
- Generate code from natural language descriptions
- Create complete modules, classes, and functions
- Refactor existing code
- Add tests for code
- Apply code transformations

Uses Anthropic SDK for intelligent generation with FileSystem for persistence.

Example:
    >>> cap = CodeCreationCapability()
    >>> await cap.initialize()
    >>>
    >>> # Generate a module
    >>> result = await cap.create_module(
    ...     name="user_service",
    ...     description="User management service with CRUD operations"
    ... )
    >>>
    >>> # Generate tests
    >>> result = await cap.create_tests(
    ...     code=existing_code,
    ...     test_framework="pytest"
    ... )
    >>>
    >>> # Refactor code
    >>> result = await cap.refactor_code(
    ...     code=existing_code,
    ...     instructions="Extract database logic into repository pattern"
    ... )
"""

import time
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.anthropic_integration import (
    AnthropicCapability,
    AnthropicConfig,
)
from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)
from paracle_meta.capabilities.filesystem import FileSystemCapability, FileSystemConfig


class CodeCreationConfig(CapabilityConfig):
    """Configuration for Code Creation capability."""

    output_path: str | None = Field(
        default=None, description="Default output path for generated code"
    )
    default_language: str = Field(
        default="python", description="Default programming language"
    )
    include_docstrings: bool = Field(
        default=True, description="Include docstrings in generated code"
    )
    include_type_hints: bool = Field(
        default=True, description="Include type hints (for Python)"
    )
    test_framework: str = Field(default="pytest", description="Default test framework")
    style_guide: str = Field(
        default="google", description="Code style guide (google, numpy, sphinx)"
    )
    auto_save: bool = Field(
        default=False, description="Automatically save generated code to files"
    )
    anthropic_config: AnthropicConfig | None = Field(
        default=None, description="Anthropic configuration"
    )
    filesystem_config: FileSystemConfig | None = Field(
        default=None, description="FileSystem configuration"
    )


class CodeCreationCapability(BaseCapability):
    """LLM-powered code creation and manipulation capability.

    Combines Anthropic Claude for intelligent code generation
    with FileSystem for persistence and file operations.

    Features:
    - Natural language to code generation
    - Module, class, and function creation
    - Test generation
    - Code refactoring
    - Documentation generation
    - Code transformations

    Example:
        >>> cap = CodeCreationCapability()
        >>> await cap.initialize()
        >>>
        >>> result = await cap.create_function(
        ...     name="calculate_fibonacci",
        ...     description="Calculate nth Fibonacci number recursively"
        ... )
        >>> print(result.output["code"])
    """

    name = "code_creation"
    description = "LLM-powered code generation and manipulation"

    # Code generation prompts
    MODULE_PROMPT = """Generate a complete Python module with the following requirements:

Module name: {name}
Description: {description}

Requirements:
- Use Python 3.10+ features
- Include comprehensive docstrings (Google style)
- Include type hints for all functions
- Follow PEP 8 style guidelines
- Include necessary imports
- Add __all__ export list

{additional_context}

Generate ONLY the Python code, no explanations."""

    CLASS_PROMPT = """Generate a Python class with the following requirements:

Class name: {name}
Description: {description}
Base classes: {base_classes}

Requirements:
- Use Python 3.10+ features
- Include class and method docstrings
- Include type hints
- Use dataclass or Pydantic BaseModel if appropriate
- Include __init__, __repr__, and relevant dunder methods

{additional_context}

Generate ONLY the Python code, no explanations."""

    FUNCTION_PROMPT = """Generate a Python function with the following requirements:

Function name: {name}
Description: {description}
Parameters: {parameters}
Return type: {return_type}

Requirements:
- Include comprehensive docstring with Args, Returns, Raises sections
- Include type hints
- Handle edge cases appropriately
- Add input validation if needed

{additional_context}

Generate ONLY the Python code, no explanations."""

    TEST_PROMPT = """Generate comprehensive tests for the following code:

```python
{code}
```

Requirements:
- Use {test_framework} framework
- Test all public functions and methods
- Include edge cases and error conditions
- Use descriptive test names
- Include fixtures where appropriate
- Aim for high coverage

Generate ONLY the test code, no explanations."""

    REFACTOR_PROMPT = """Refactor the following code according to these instructions:

Instructions: {instructions}

Original code:
```python
{code}
```

Requirements:
- Maintain existing functionality
- Improve code quality and readability
- Follow best practices
- Add type hints if missing
- Update docstrings if needed

Generate ONLY the refactored Python code, no explanations."""

    def __init__(self, config: CodeCreationConfig | None = None):
        """Initialize Code Creation capability."""
        super().__init__(config or CodeCreationConfig())
        self.config: CodeCreationConfig = self.config

        # Sub-capabilities
        self._anthropic: AnthropicCapability | None = None
        self._filesystem: FileSystemCapability | None = None

    async def initialize(self) -> None:
        """Initialize capability and sub-capabilities."""
        await super().initialize()

        # Initialize Anthropic capability
        anthropic_config = self.config.anthropic_config or AnthropicConfig(
            temperature=0.3,  # Lower temperature for code generation
            max_tokens=8192,
        )
        self._anthropic = AnthropicCapability(config=anthropic_config)
        await self._anthropic.initialize()

        # Initialize FileSystem capability
        filesystem_config = self.config.filesystem_config or FileSystemConfig()
        self._filesystem = FileSystemCapability(config=filesystem_config)
        await self._filesystem.initialize()

    async def shutdown(self) -> None:
        """Shutdown capability and cleanup."""
        if self._anthropic:
            await self._anthropic.shutdown()
        if self._filesystem:
            await self._filesystem.shutdown()
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute code creation operation.

        Actions:
            - create_module: Create a complete module
            - create_class: Create a class
            - create_function: Create a function
            - create_tests: Generate tests for code
            - refactor: Refactor existing code
            - add_docstrings: Add docstrings to code
            - add_type_hints: Add type hints to code
            - create_api_endpoint: Create FastAPI/Flask endpoint
            - create_pydantic_model: Create Pydantic model
        """
        action = kwargs.get("action", "create_function")
        start_time = time.time()

        try:
            if action == "create_module":
                result = await self._create_module(
                    name=kwargs.get("name", "module"),
                    description=kwargs.get("description", ""),
                    components=kwargs.get("components", []),
                    save_path=kwargs.get("save_path"),
                )
            elif action == "create_class":
                result = await self._create_class(
                    name=kwargs.get("name", "MyClass"),
                    description=kwargs.get("description", ""),
                    base_classes=kwargs.get("base_classes", []),
                    attributes=kwargs.get("attributes", []),
                    methods=kwargs.get("methods", []),
                    save_path=kwargs.get("save_path"),
                )
            elif action == "create_function":
                result = await self._create_function(
                    name=kwargs.get("name", "my_function"),
                    description=kwargs.get("description", ""),
                    parameters=kwargs.get("parameters", []),
                    return_type=kwargs.get("return_type", "None"),
                    save_path=kwargs.get("save_path"),
                )
            elif action == "create_tests":
                result = await self._create_tests(
                    code=kwargs.get("code", ""),
                    test_framework=kwargs.get(
                        "test_framework", self.config.test_framework
                    ),
                    save_path=kwargs.get("save_path"),
                )
            elif action == "refactor":
                result = await self._refactor_code(
                    code=kwargs.get("code", ""),
                    instructions=kwargs.get("instructions", ""),
                    save_path=kwargs.get("save_path"),
                )
            elif action == "add_docstrings":
                result = await self._add_docstrings(
                    code=kwargs.get("code", ""),
                    style=kwargs.get("style", self.config.style_guide),
                )
            elif action == "add_type_hints":
                result = await self._add_type_hints(
                    code=kwargs.get("code", ""),
                )
            elif action == "create_api_endpoint":
                result = await self._create_api_endpoint(
                    name=kwargs.get("name", "endpoint"),
                    description=kwargs.get("description", ""),
                    method=kwargs.get("method", "GET"),
                    request_model=kwargs.get("request_model"),
                    response_model=kwargs.get("response_model"),
                    framework=kwargs.get("framework", "fastapi"),
                )
            elif action == "create_pydantic_model":
                result = await self._create_pydantic_model(
                    name=kwargs.get("name", "Model"),
                    description=kwargs.get("description", ""),
                    fields=kwargs.get("fields", []),
                )
            elif action == "generate_from_spec":
                result = await self._generate_from_spec(
                    spec=kwargs.get("spec", {}),
                )
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _generate_code(
        self,
        prompt: str,
        save_path: str | None = None,
    ) -> dict[str, Any]:
        """Generate code using Anthropic and optionally save."""
        result = await self._anthropic.complete(
            prompt=prompt,
            system="You are an expert Python developer. Generate clean, production-quality code.",
        )

        if not result.success:
            raise RuntimeError(f"Code generation failed: {result.error}")

        code = result.output.get("content", "")

        # Clean up code (remove markdown if present)
        code = self._clean_code(code)

        output = {
            "code": code,
            "lines": code.count("\n") + 1,
            "characters": len(code),
            "model": result.output.get("model"),
            "usage": result.output.get("usage"),
        }

        # Save if path provided
        if save_path or (self.config.auto_save and self.config.output_path):
            final_path = save_path or self.config.output_path
            save_result = await self._filesystem.write_file(final_path, code)
            if save_result.success:
                output["saved_to"] = final_path

        return output

    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting."""
        # Remove markdown code blocks
        if "```python" in code:
            parts = code.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
        elif "```" in code:
            parts = code.split("```")
            if len(parts) > 1:
                code = parts[1].split("```")[0]

        return code.strip()

    async def _create_module(
        self,
        name: str,
        description: str,
        components: list[str] = None,
        save_path: str | None = None,
    ) -> dict[str, Any]:
        """Create a complete Python module."""
        additional = ""
        if components:
            additional = "Include these components:\n- " + "\n- ".join(components)

        prompt = self.MODULE_PROMPT.format(
            name=name,
            description=description,
            additional_context=additional,
        )

        result = await self._generate_code(prompt, save_path)
        result["module_name"] = name
        return result

    async def _create_class(
        self,
        name: str,
        description: str,
        base_classes: list[str] = None,
        attributes: list[dict[str, Any]] = None,
        methods: list[dict[str, Any]] = None,
        save_path: str | None = None,
    ) -> dict[str, Any]:
        """Create a Python class."""
        additional = ""
        if attributes:
            additional += "Attributes:\n"
            for attr in attributes:
                additional += f"- {attr.get('name')}: {attr.get('type', 'Any')} - {attr.get('description', '')}\n"

        if methods:
            additional += "\nMethods:\n"
            for method in methods:
                additional += f"- {method.get('name')}({method.get('params', '')}): {method.get('description', '')}\n"

        prompt = self.CLASS_PROMPT.format(
            name=name,
            description=description,
            base_classes=", ".join(base_classes) if base_classes else "None",
            additional_context=additional,
        )

        result = await self._generate_code(prompt, save_path)
        result["class_name"] = name
        return result

    async def _create_function(
        self,
        name: str,
        description: str,
        parameters: list[dict[str, Any]] = None,
        return_type: str = "None",
        save_path: str | None = None,
    ) -> dict[str, Any]:
        """Create a Python function."""
        params_str = ""
        if parameters:
            for param in parameters:
                params_str += f"- {param.get('name')}: {param.get('type', 'Any')} - {param.get('description', '')}\n"

        prompt = self.FUNCTION_PROMPT.format(
            name=name,
            description=description,
            parameters=params_str or "None",
            return_type=return_type,
            additional_context="",
        )

        result = await self._generate_code(prompt, save_path)
        result["function_name"] = name
        return result

    async def _create_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        save_path: str | None = None,
    ) -> dict[str, Any]:
        """Generate tests for code."""
        prompt = self.TEST_PROMPT.format(
            code=code,
            test_framework=test_framework,
        )

        result = await self._generate_code(prompt, save_path)
        result["test_framework"] = test_framework
        return result

    async def _refactor_code(
        self,
        code: str,
        instructions: str,
        save_path: str | None = None,
    ) -> dict[str, Any]:
        """Refactor existing code."""
        prompt = self.REFACTOR_PROMPT.format(
            code=code,
            instructions=instructions,
        )

        result = await self._generate_code(prompt, save_path)
        result["refactoring_instructions"] = instructions
        return result

    async def _add_docstrings(
        self,
        code: str,
        style: str = "google",
    ) -> dict[str, Any]:
        """Add docstrings to code."""
        prompt = f"""Add comprehensive docstrings to this Python code.
Use {style} style docstrings.
Include Args, Returns, Raises sections where appropriate.

```python
{code}
```

Return the code with docstrings added. Generate ONLY the Python code."""

        return await self._generate_code(prompt)

    async def _add_type_hints(self, code: str) -> dict[str, Any]:
        """Add type hints to code."""
        prompt = f"""Add type hints to this Python code.
Use Python 3.10+ typing features (Union -> |, Optional -> | None).
Include type hints for all function parameters and return types.

```python
{code}
```

Return the code with type hints added. Generate ONLY the Python code."""

        return await self._generate_code(prompt)

    async def _create_api_endpoint(
        self,
        name: str,
        description: str,
        method: str = "GET",
        request_model: str | None = None,
        response_model: str | None = None,
        framework: str = "fastapi",
    ) -> dict[str, Any]:
        """Create an API endpoint."""
        prompt = f"""Create a {framework} API endpoint:

Name: {name}
Description: {description}
HTTP Method: {method}
Request Model: {request_model or 'None'}
Response Model: {response_model or 'None'}

Requirements:
- Include proper error handling
- Add input validation
- Include comprehensive docstring
- Follow RESTful conventions
- Include response status codes

Generate ONLY the Python code including necessary imports."""

        result = await self._generate_code(prompt)
        result["endpoint_name"] = name
        result["framework"] = framework
        result["method"] = method
        return result

    async def _create_pydantic_model(
        self,
        name: str,
        description: str,
        fields: list[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create a Pydantic model."""
        fields_str = ""
        if fields:
            for field in fields:
                fields_str += f"- {field.get('name')}: {field.get('type', 'str')} "
                if field.get("description"):
                    fields_str += f"- {field['description']} "
                if field.get("default"):
                    fields_str += f"(default: {field['default']})"
                fields_str += "\n"

        prompt = f"""Create a Pydantic v2 model:

Model name: {name}
Description: {description}

Fields:
{fields_str or 'Define appropriate fields based on the description'}

Requirements:
- Use Pydantic v2 (BaseModel from pydantic)
- Include Field() with descriptions
- Add validators where appropriate
- Include model_config if needed
- Include comprehensive docstring

Generate ONLY the Python code including imports."""

        result = await self._generate_code(prompt)
        result["model_name"] = name
        return result

    async def _generate_from_spec(
        self,
        spec: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate code from a specification dictionary."""
        import json

        prompt = f"""Generate Python code from this specification:

```json
{json.dumps(spec, indent=2)}
```

Requirements:
- Follow the specification exactly
- Include all specified components
- Add type hints and docstrings
- Follow Python best practices

Generate ONLY the Python code."""

        return await self._generate_code(prompt)

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def create_module(
        self,
        name: str,
        description: str,
        save_path: str | None = None,
    ) -> CapabilityResult:
        """Create a complete module."""
        return await self.execute(
            action="create_module",
            name=name,
            description=description,
            save_path=save_path,
        )

    async def create_class(
        self,
        name: str,
        description: str,
        **kwargs,
    ) -> CapabilityResult:
        """Create a class."""
        return await self.execute(
            action="create_class",
            name=name,
            description=description,
            **kwargs,
        )

    async def create_function(
        self,
        name: str,
        description: str,
        **kwargs,
    ) -> CapabilityResult:
        """Create a function."""
        return await self.execute(
            action="create_function",
            name=name,
            description=description,
            **kwargs,
        )

    async def create_tests(
        self,
        code: str,
        test_framework: str = "pytest",
    ) -> CapabilityResult:
        """Generate tests for code."""
        return await self.execute(
            action="create_tests",
            code=code,
            test_framework=test_framework,
        )

    async def refactor(
        self,
        code: str,
        instructions: str,
    ) -> CapabilityResult:
        """Refactor code."""
        return await self.execute(
            action="refactor",
            code=code,
            instructions=instructions,
        )

    async def create_api_endpoint(
        self,
        name: str,
        description: str,
        method: str = "GET",
        framework: str = "fastapi",
    ) -> CapabilityResult:
        """Create an API endpoint."""
        return await self.execute(
            action="create_api_endpoint",
            name=name,
            description=description,
            method=method,
            framework=framework,
        )

    async def create_pydantic_model(
        self,
        name: str,
        description: str,
        fields: list[dict[str, Any]] = None,
    ) -> CapabilityResult:
        """Create a Pydantic model."""
        return await self.execute(
            action="create_pydantic_model",
            name=name,
            description=description,
            fields=fields,
        )
