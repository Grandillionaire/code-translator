"""
Unit Test Generator for translated code
Generates test suites for Python, JavaScript, and Java
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TestFramework(Enum):
    """Supported test frameworks"""
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"


@dataclass
class FunctionSignature:
    """Represents a function signature extracted from code"""
    name: str
    params: List[Tuple[str, Optional[str]]]  # (name, type_hint)
    return_type: Optional[str]
    is_async: bool = False
    is_method: bool = False
    class_name: Optional[str] = None


class TestGenerator:
    """Generates unit tests for code in various languages"""

    def __init__(self):
        self.extractors = {
            "Python": self._extract_python_functions,
            "JavaScript": self._extract_js_functions,
            "TypeScript": self._extract_ts_functions,
            "Java": self._extract_java_methods,
        }

    def generate_tests(
        self,
        code: str,
        language: str,
        framework: Optional[TestFramework] = None
    ) -> str:
        """
        Generate unit tests for the given code.
        
        Args:
            code: Source code to generate tests for
            language: Programming language of the code
            framework: Test framework to use (auto-detected if not specified)
            
        Returns:
            Generated test code
        """
        # Auto-detect framework if not specified
        if framework is None:
            framework = self._get_default_framework(language)

        # Extract function signatures
        functions = self._extract_functions(code, language)

        if not functions:
            return self._generate_placeholder_test(language, framework)

        # Generate tests based on framework
        if framework == TestFramework.PYTEST:
            return self._generate_pytest(functions, code)
        elif framework == TestFramework.JEST:
            return self._generate_jest(functions, code)
        elif framework == TestFramework.JUNIT:
            return self._generate_junit(functions, code)
        else:
            return self._generate_placeholder_test(language, framework)

    def _get_default_framework(self, language: str) -> TestFramework:
        """Get default test framework for language"""
        frameworks = {
            "Python": TestFramework.PYTEST,
            "JavaScript": TestFramework.JEST,
            "TypeScript": TestFramework.JEST,
            "Java": TestFramework.JUNIT,
            "Kotlin": TestFramework.JUNIT,
        }
        return frameworks.get(language, TestFramework.PYTEST)

    def _extract_functions(self, code: str, language: str) -> List[FunctionSignature]:
        """Extract function signatures from code"""
        extractor = self.extractors.get(language)
        if extractor:
            return extractor(code)
        return []

    def _extract_python_functions(self, code: str) -> List[FunctionSignature]:
        """Extract Python function signatures"""
        functions = []
        
        # Match async and regular functions
        pattern = r'^(\s*)(async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*(\w+(?:\[[\w,\s]+\])?))?'
        
        current_class = None
        for line in code.split('\n'):
            # Check for class definition
            class_match = re.match(r'^class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
                continue
            
            # Check if we're back to module level
            if not line.startswith((' ', '\t')) and line.strip():
                current_class = None
            
            match = re.match(pattern, line)
            if match:
                indent, is_async, name, params_str, return_type = match.groups()
                
                # Skip private/dunder methods except __init__
                if name.startswith('_') and name != '__init__':
                    continue
                
                # Parse parameters
                params = self._parse_python_params(params_str)
                
                # Check if it's a method
                is_method = bool(indent) and (params and params[0][0] in ('self', 'cls'))
                if is_method and params:
                    params = params[1:]  # Remove self/cls
                
                functions.append(FunctionSignature(
                    name=name,
                    params=params,
                    return_type=return_type,
                    is_async=bool(is_async),
                    is_method=is_method,
                    class_name=current_class if is_method else None
                ))
        
        return functions

    def _parse_python_params(self, params_str: str) -> List[Tuple[str, Optional[str]]]:
        """Parse Python parameter string"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if not param or param in ('self', 'cls'):
                if param:
                    params.append((param, None))
                continue
            
            # Handle type hints
            if ':' in param:
                name, type_hint = param.split(':', 1)
                name = name.strip()
                type_hint = type_hint.split('=')[0].strip()
                params.append((name, type_hint))
            else:
                name = param.split('=')[0].strip()
                params.append((name, None))
        
        return params

    def _extract_js_functions(self, code: str) -> List[FunctionSignature]:
        """Extract JavaScript function signatures"""
        functions = []
        
        # Match function declarations and arrow functions
        patterns = [
            r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
            r'(\w+)\s*[=:]\s*(?:async\s+)?function\s*\([^)]*\)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, code):
                name = match.group(1)
                if name.startswith('_'):
                    continue
                
                # Get params if available
                params_str = match.group(2) if len(match.groups()) > 1 else ""
                params = [(p.strip(), None) for p in params_str.split(',') if p.strip()]
                
                is_async = 'async' in match.group(0)
                
                functions.append(FunctionSignature(
                    name=name,
                    params=params,
                    return_type=None,
                    is_async=is_async
                ))
        
        return functions

    def _extract_ts_functions(self, code: str) -> List[FunctionSignature]:
        """Extract TypeScript function signatures"""
        functions = self._extract_js_functions(code)
        
        # Also look for typed functions
        pattern = r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+(?:<[^>]+>)?)'
        for match in re.finditer(pattern, code):
            name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3)
            
            if any(f.name == name for f in functions):
                continue
            
            params = []
            for p in params_str.split(','):
                if ':' in p:
                    pname, ptype = p.split(':', 1)
                    params.append((pname.strip(), ptype.strip()))
                elif p.strip():
                    params.append((p.strip(), None))
            
            functions.append(FunctionSignature(
                name=name,
                params=params,
                return_type=return_type,
                is_async='async' in match.group(0)
            ))
        
        return functions

    def _extract_java_methods(self, code: str) -> List[FunctionSignature]:
        """Extract Java method signatures"""
        functions = []
        
        # Match method signatures
        pattern = r'(public|private|protected)\s+(static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        
        # Find class name
        class_match = re.search(r'class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else None
        
        for match in re.finditer(pattern, code):
            visibility, is_static, return_type, name, params_str = match.groups()
            
            if name.startswith('_'):
                continue
            
            params = []
            if params_str.strip():
                for p in params_str.split(','):
                    parts = p.strip().split()
                    if len(parts) >= 2:
                        params.append((parts[-1], parts[-2]))
                    elif parts:
                        params.append((parts[0], None))
            
            functions.append(FunctionSignature(
                name=name,
                params=params,
                return_type=return_type,
                is_method=True,
                class_name=class_name
            ))
        
        return functions

    def _generate_pytest(self, functions: List[FunctionSignature], original_code: str) -> str:
        """Generate pytest test file"""
        lines = [
            '"""',
            'Unit tests generated by Code Translator',
            '"""',
            '',
            'import pytest',
            '',
            '# Import the module under test',
            '# from your_module import *',
            '',
            ''
        ]
        
        # Group by class
        classes: Dict[Optional[str], List[FunctionSignature]] = {}
        for func in functions:
            key = func.class_name
            if key not in classes:
                classes[key] = []
            classes[key].append(func)
        
        for class_name, funcs in classes.items():
            if class_name:
                lines.append(f'class Test{class_name}:')
                lines.append(f'    """Tests for {class_name} class"""')
                lines.append('')
                lines.append('    @pytest.fixture')
                lines.append('    def instance(self):')
                lines.append(f'        """Create a {class_name} instance for testing"""')
                lines.append(f'        # TODO: Configure initialization parameters')
                lines.append(f'        return {class_name}()')
                lines.append('')
                
                for func in funcs:
                    lines.extend(self._generate_pytest_test(func, indent='    ', use_fixture=True))
            else:
                for func in funcs:
                    lines.extend(self._generate_pytest_test(func))
        
        return '\n'.join(lines)

    def _generate_pytest_test(
        self,
        func: FunctionSignature,
        indent: str = '',
        use_fixture: bool = False
    ) -> List[str]:
        """Generate a single pytest test function"""
        lines = []
        
        # Async decorator if needed
        if func.is_async:
            lines.append(f'{indent}@pytest.mark.asyncio')
        
        # Test function definition
        fixture_param = ', instance' if use_fixture else ''
        async_prefix = 'async ' if func.is_async else ''
        lines.append(f'{indent}{async_prefix}def test_{func.name}(self{fixture_param}):')
        lines.append(f'{indent}    """Test {func.name} function"""')
        
        # Generate test body
        if func.params:
            lines.append(f'{indent}    # Arrange')
            for param_name, param_type in func.params:
                value = self._get_sample_value(param_type)
                lines.append(f'{indent}    {param_name} = {value}')
        
        lines.append(f'{indent}    ')
        lines.append(f'{indent}    # Act')
        
        call_params = ', '.join(p[0] for p in func.params)
        if func.is_method and use_fixture:
            call = f'instance.{func.name}({call_params})'
        else:
            call = f'{func.name}({call_params})'
        
        if func.is_async:
            lines.append(f'{indent}    result = await {call}')
        else:
            lines.append(f'{indent}    result = {call}')
        
        lines.append(f'{indent}    ')
        lines.append(f'{indent}    # Assert')
        lines.append(f'{indent}    assert result is not None  # TODO: Add specific assertions')
        lines.append('')
        
        return lines

    def _generate_jest(self, functions: List[FunctionSignature], original_code: str) -> str:
        """Generate Jest test file"""
        lines = [
            '/**',
            ' * Unit tests generated by Code Translator',
            ' */',
            '',
            "// Import the module under test",
            "// const { functionName } = require('./your-module');",
            '',
            ''
        ]
        
        # Group by class
        classes: Dict[Optional[str], List[FunctionSignature]] = {}
        for func in functions:
            key = func.class_name
            if key not in classes:
                classes[key] = []
            classes[key].append(func)
        
        for class_name, funcs in classes.items():
            if class_name:
                lines.append(f"describe('{class_name}', () => {{")
                lines.append(f'  let instance;')
                lines.append('')
                lines.append('  beforeEach(() => {')
                lines.append(f'    instance = new {class_name}();')
                lines.append('  });')
                lines.append('')
                
                for func in funcs:
                    lines.extend(self._generate_jest_test(func, indent='  ', use_instance=True))
                
                lines.append('});')
                lines.append('')
            else:
                for func in funcs:
                    lines.extend(self._generate_jest_test(func))
        
        return '\n'.join(lines)

    def _generate_jest_test(
        self,
        func: FunctionSignature,
        indent: str = '',
        use_instance: bool = False
    ) -> List[str]:
        """Generate a single Jest test"""
        lines = []
        
        async_prefix = 'async ' if func.is_async else ''
        lines.append(f"{indent}test('{func.name} should work correctly', {async_prefix}() => {{")
        
        # Generate test body
        if func.params:
            lines.append(f'{indent}  // Arrange')
            for param_name, param_type in func.params:
                value = self._get_sample_value_js(param_type)
                lines.append(f'{indent}  const {param_name} = {value};')
        
        lines.append(f'{indent}')
        lines.append(f'{indent}  // Act')
        
        call_params = ', '.join(p[0] for p in func.params)
        if func.is_method and use_instance:
            call = f'instance.{func.name}({call_params})'
        else:
            call = f'{func.name}({call_params})'
        
        if func.is_async:
            lines.append(f'{indent}  const result = await {call};')
        else:
            lines.append(f'{indent}  const result = {call};')
        
        lines.append(f'{indent}')
        lines.append(f'{indent}  // Assert')
        lines.append(f'{indent}  expect(result).toBeDefined(); // TODO: Add specific assertions')
        lines.append(f'{indent}}});')
        lines.append('')
        
        return lines

    def _generate_junit(self, functions: List[FunctionSignature], original_code: str) -> str:
        """Generate JUnit test file"""
        # Find class name
        class_match = re.search(r'class\s+(\w+)', original_code)
        class_name = class_match.group(1) if class_match else "MyClass"
        
        lines = [
            '/**',
            ' * Unit tests generated by Code Translator',
            ' */',
            '',
            'import org.junit.jupiter.api.Test;',
            'import org.junit.jupiter.api.BeforeEach;',
            'import org.junit.jupiter.api.DisplayName;',
            'import static org.junit.jupiter.api.Assertions.*;',
            '',
            f'class {class_name}Test {{',
            '',
            f'    private {class_name} instance;',
            '',
            '    @BeforeEach',
            '    void setUp() {',
            f'        instance = new {class_name}();',
            '    }',
            ''
        ]
        
        for func in functions:
            lines.extend(self._generate_junit_test(func, class_name))
        
        lines.append('}')
        
        return '\n'.join(lines)

    def _generate_junit_test(self, func: FunctionSignature, class_name: str) -> List[str]:
        """Generate a single JUnit test"""
        lines = []
        
        test_name = f'test{func.name[0].upper()}{func.name[1:]}'
        
        lines.append('    @Test')
        lines.append(f'    @DisplayName("{func.name} should work correctly")')
        lines.append(f'    void {test_name}() {{')
        
        # Generate test body
        if func.params:
            lines.append('        // Arrange')
            for param_name, param_type in func.params:
                value = self._get_sample_value_java(param_type)
                java_type = param_type or 'Object'
                lines.append(f'        {java_type} {param_name} = {value};')
        
        lines.append('')
        lines.append('        // Act')
        
        call_params = ', '.join(p[0] for p in func.params)
        lines.append(f'        var result = instance.{func.name}({call_params});')
        
        lines.append('')
        lines.append('        // Assert')
        lines.append('        assertNotNull(result); // TODO: Add specific assertions')
        lines.append('    }')
        lines.append('')
        
        return lines

    def _get_sample_value(self, type_hint: Optional[str]) -> str:
        """Get Python sample value based on type hint"""
        if not type_hint:
            return '"test_value"'
        
        type_map = {
            'str': '"test_string"',
            'int': '42',
            'float': '3.14',
            'bool': 'True',
            'list': '[]',
            'dict': '{}',
            'List': '[]',
            'Dict': '{}',
            'Optional': 'None',
        }
        
        for key, value in type_map.items():
            if key in type_hint:
                return value
        
        return 'None'

    def _get_sample_value_js(self, type_hint: Optional[str]) -> str:
        """Get JavaScript sample value"""
        if not type_hint:
            return '"test_value"'
        
        type_map = {
            'string': '"test_string"',
            'number': '42',
            'boolean': 'true',
            'array': '[]',
            'object': '{}',
        }
        
        type_lower = type_hint.lower() if type_hint else ''
        return type_map.get(type_lower, 'null')

    def _get_sample_value_java(self, type_hint: Optional[str]) -> str:
        """Get Java sample value"""
        if not type_hint:
            return 'null'
        
        type_map = {
            'String': '"test_string"',
            'int': '42',
            'Integer': '42',
            'long': '42L',
            'Long': '42L',
            'double': '3.14',
            'Double': '3.14',
            'boolean': 'true',
            'Boolean': 'true',
            'List': 'new ArrayList<>()',
            'Map': 'new HashMap<>()',
        }
        
        for key, value in type_map.items():
            if key in type_hint:
                return value
        
        return 'null'

    def _generate_placeholder_test(self, language: str, framework: TestFramework) -> str:
        """Generate placeholder test when no functions found"""
        if framework == TestFramework.PYTEST:
            return '''"""
Unit tests (placeholder)
No testable functions were detected.
"""

import pytest


def test_placeholder():
    """Placeholder test - add your tests here"""
    assert True
'''
        elif framework == TestFramework.JEST:
            return '''/**
 * Unit tests (placeholder)
 * No testable functions were detected.
 */

test('placeholder', () => {
  expect(true).toBe(true);
});
'''
        else:
            return '''/**
 * Unit tests (placeholder)
 * No testable functions were detected.
 */

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class PlaceholderTest {
    @Test
    void placeholder() {
        assertTrue(true);
    }
}
'''
