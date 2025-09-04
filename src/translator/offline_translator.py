"""
Offline translation engine for basic syntax conversion
"""

import re
from typing import Dict, List, Optional


class OfflineTranslator:
    """Basic offline translation for common patterns"""
    
    def __init__(self):
        self.setup_translation_rules()
        
    def setup_translation_rules(self):
        """Setup basic translation rules between languages"""
        self.type_mappings = {
            "Python->JavaScript": {
                "int": "number",
                "float": "number", 
                "str": "string",
                "bool": "boolean",
                "list": "Array",
                "dict": "Object",
                "None": "null",
                "True": "true",
                "False": "false"
            },
            "Python->Java": {
                "int": "int",
                "float": "double",
                "str": "String",
                "bool": "boolean",
                "list": "ArrayList",
                "dict": "HashMap",
                "None": "null",
                "True": "true",
                "False": "false"
            },
            "JavaScript->Python": {
                "number": "float",
                "string": "str",
                "boolean": "bool",
                "null": "None",
                "true": "True",
                "false": "False",
                "undefined": "None"
            },
            "JavaScript->Java": {
                "number": "double",
                "string": "String",
                "boolean": "boolean",
                "null": "null",
                "true": "true",
                "false": "false"
            }
        }
        
        self.function_patterns = {
            "Python": {
                "function": r"def\s+(\w+)\s*\((.*?)\)\s*:",
                "class": r"class\s+(\w+)(?:\((.*?)\))?\s*:",
                "import": r"import\s+(.*?)$|from\s+(.*?)\s+import\s+(.*?)$",
                "print": r"print\s*\((.*?)\)",
                "comment": r"#\s*(.*?)$",
                "if": r"if\s+(.*?):",
                "for": r"for\s+(\w+)\s+in\s+(.*?):",
                "while": r"while\s+(.*?):"
            },
            "JavaScript": {
                "function": r"function\s+(\w+)\s*\((.*?)\)\s*{",
                "arrow": r"const\s+(\w+)\s*=\s*\((.*?)\)\s*=>\s*{",
                "class": r"class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{",
                "import": r"import\s+(.*?)\s+from\s+['\"](.+?)['\"];",
                "print": r"console\.log\s*\((.*?)\)",
                "comment": r"//\s*(.*?)$",
                "if": r"if\s*\((.*?)\)\s*{",
                "for": r"for\s*\((.*?)\)\s*{",
                "while": r"while\s*\((.*?)\)\s*{"
            },
            "Java": {
                "function": r"(?:public|private|protected)?\s*(?:static)?\s*(\w+)\s+(\w+)\s*\((.*?)\)\s*{",
                "class": r"(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{",
                "import": r"import\s+(.*?);",
                "print": r"System\.out\.println\s*\((.*?)\)",
                "comment": r"//\s*(.*?)$",
                "if": r"if\s*\((.*?)\)\s*{",
                "for": r"for\s*\((.*?)\)\s*{",
                "while": r"while\s*\((.*?)\)\s*{"
            }
        }
        
    def translate(self, code: str, source_lang: str, target_lang: str) -> str:
        """Perform basic offline translation"""
        if source_lang == target_lang:
            return code
            
        # Get appropriate translation rules
        translation_key = f"{source_lang}->{target_lang}"
        
        # Start with original code
        translated = code
        
        # Apply type mappings
        if translation_key in self.type_mappings:
            for src_type, tgt_type in self.type_mappings[translation_key].items():
                translated = re.sub(
                    r'\b' + re.escape(src_type) + r'\b',
                    tgt_type,
                    translated
                )
                
        # Apply specific translations
        if source_lang == "Python" and target_lang == "JavaScript":
            translated = self._python_to_javascript(translated)
        elif source_lang == "Python" and target_lang == "Java":
            translated = self._python_to_java(translated)
        elif source_lang == "JavaScript" and target_lang == "Python":
            translated = self._javascript_to_python(translated)
        elif source_lang == "JavaScript" and target_lang == "Java":
            translated = self._javascript_to_java(translated)
        elif source_lang == "Java" and target_lang == "Python":
            translated = self._java_to_python(translated)
        elif source_lang == "Java" and target_lang == "JavaScript":
            translated = self._java_to_javascript(translated)
        else:
            # Generic attempt for other combinations
            translated = self._generic_translation(translated, source_lang, target_lang)
            
        return translated
        
    def _python_to_javascript(self, code: str) -> str:
        """Translate Python to JavaScript"""
        lines = code.split('\n')
        translated_lines = []
        indent_stack = [0]
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                translated_lines.append(line)
                continue
                
            # Detect indentation
            indent = len(line) - len(line.lstrip())
            
            # Handle dedentation
            while indent_stack and indent < indent_stack[-1]:
                indent_stack.pop()
                translated_lines.append(' ' * indent + '}')
                
            # Function definition
            func_match = re.match(r'(\s*)def\s+(\w+)\s*\((.*?)\)\s*:', line)
            if func_match:
                spaces, func_name, params = func_match.groups()
                translated_lines.append(f'{spaces}function {func_name}({params}) {{')
                indent_stack.append(indent)
                continue
                
            # Class definition
            class_match = re.match(r'(\s*)class\s+(\w+)(?:\((.*?)\))?\s*:', line)
            if class_match:
                spaces, class_name, parent = class_match.groups()
                if parent:
                    translated_lines.append(f'{spaces}class {class_name} extends {parent} {{')
                else:
                    translated_lines.append(f'{spaces}class {class_name} {{')
                indent_stack.append(indent)
                continue
                
            # If statement
            if_match = re.match(r'(\s*)if\s+(.*?):', line)
            if if_match:
                spaces, condition = if_match.groups()
                translated_lines.append(f'{spaces}if ({condition}) {{')
                indent_stack.append(indent)
                continue
                
            # For loop
            for_match = re.match(r'(\s*)for\s+(\w+)\s+in\s+(.*?):', line)
            if for_match:
                spaces, var, iterable = for_match.groups()
                translated_lines.append(f'{spaces}for (let {var} of {iterable}) {{')
                indent_stack.append(indent)
                continue
                
            # Print statement
            line = re.sub(r'print\s*\((.*?)\)', r'console.log(\1)', line)
            
            # Method calls with self
            line = re.sub(r'self\.', 'this.', line)
            
            # String formatting
            line = re.sub(r'f["\']([^"\']*?)\{([^}]+)\}([^"\']*?)["\']', 
                         r'`\1${\2}\3`', line)
            
            translated_lines.append(line)
            
        # Close any remaining blocks
        while len(indent_stack) > 1:
            indent_stack.pop()
            translated_lines.append('}')
            
        return '\n'.join(translated_lines)
        
    def _python_to_java(self, code: str) -> str:
        """Translate Python to Java"""
        # Start with a basic class wrapper
        class_name = "TranslatedCode"
        
        lines = code.split('\n')
        translated_lines = [
            f"public class {class_name} {{",
            "    public static void main(String[] args) {"
        ]
        
        for line in lines:
            if not line.strip():
                translated_lines.append(line)
                continue
                
            # Function to method
            func_match = re.match(r'(\s*)def\s+(\w+)\s*\((.*?)\)\s*:', line)
            if func_match:
                spaces, func_name, params = func_match.groups()
                # Simple type inference
                typed_params = self._infer_java_params(params)
                translated_lines.append(
                    f'    public static void {func_name}({typed_params}) {{'
                )
                continue
                
            # Print statement
            line = re.sub(r'print\s*\((.*?)\)', r'System.out.println(\1);', line)
            
            # Variables (simple type inference)
            var_match = re.match(r'(\s*)(\w+)\s*=\s*(.+)', line)
            if var_match:
                spaces, var_name, value = var_match.groups()
                java_type = self._infer_java_type(value)
                line = f'{spaces}{java_type} {var_name} = {value};'
                
            # Add semicolons where needed
            if line.strip() and not line.strip().endswith(('{', '}', ';')):
                line = line + ';'
                
            translated_lines.append('        ' + line.strip())
            
        translated_lines.extend([
            "    }",
            "}"
        ])
        
        return '\n'.join(translated_lines)
        
    def _javascript_to_python(self, code: str) -> str:
        """Translate JavaScript to Python"""
        lines = code.split('\n')
        translated_lines = []
        
        for line in lines:
            # Function definitions
            func_match = re.match(r'(\s*)function\s+(\w+)\s*\((.*?)\)\s*{', line)
            if func_match:
                spaces, func_name, params = func_match.groups()
                translated_lines.append(f'{spaces}def {func_name}({params}):')
                continue
                
            # Arrow functions
            arrow_match = re.match(r'(\s*)const\s+(\w+)\s*=\s*\((.*?)\)\s*=>\s*{', line)
            if arrow_match:
                spaces, func_name, params = arrow_match.groups()
                translated_lines.append(f'{spaces}def {func_name}({params}):')
                continue
                
            # Class definitions
            class_match = re.match(r'(\s*)class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{', line)
            if class_match:
                spaces, class_name, parent = class_match.groups()
                if parent:
                    translated_lines.append(f'{spaces}class {class_name}({parent}):')
                else:
                    translated_lines.append(f'{spaces}class {class_name}:')
                continue
                
            # Console.log to print
            line = re.sub(r'console\.log\s*\((.*?)\)', r'print(\1)', line)
            
            # this to self
            line = re.sub(r'this\.', 'self.', line)
            
            # Remove semicolons
            line = re.sub(r';\s*$', '', line)
            
            # Remove closing braces
            if line.strip() == '}':
                continue
                
            # Variable declarations
            line = re.sub(r'\b(const|let|var)\s+', '', line)
            
            translated_lines.append(line)
            
        return '\n'.join(translated_lines)
        
    def _javascript_to_java(self, code: str) -> str:
        """Translate JavaScript to Java"""
        # Similar to Python to Java but with JS specifics
        return self._generic_translation(code, "JavaScript", "Java")
        
    def _java_to_python(self, code: str) -> str:
        """Translate Java to Python"""
        lines = code.split('\n')
        translated_lines = []
        
        for line in lines:
            # Skip package and import for now
            if line.strip().startswith(('package', 'import')):
                continue
                
            # Class definitions
            class_match = re.match(
                r'(\s*)(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{',
                line
            )
            if class_match:
                spaces, class_name, parent = class_match.groups()
                if parent:
                    translated_lines.append(f'{spaces}class {class_name}({parent}):')
                else:
                    translated_lines.append(f'{spaces}class {class_name}:')
                continue
                
            # Method definitions
            method_match = re.match(
                r'(\s*)(?:public|private|protected)?\s*(?:static)?\s*(\w+)\s+(\w+)\s*\((.*?)\)\s*{',
                line
            )
            if method_match:
                spaces, return_type, method_name, params = method_match.groups()
                # Simplify parameters
                simple_params = re.sub(r'\w+\s+(\w+)', r'\1', params)
                translated_lines.append(f'{spaces}def {method_name}({simple_params}):')
                continue
                
            # System.out.println to print
            line = re.sub(r'System\.out\.println\s*\((.*?)\)', r'print(\1)', line)
            
            # Remove type declarations
            line = re.sub(r'\b(int|double|String|boolean|float|char)\s+(\w+)', r'\2', line)
            
            # Remove semicolons
            line = re.sub(r';\s*$', '', line)
            
            # Remove closing braces
            if line.strip() == '}':
                continue
                
            translated_lines.append(line)
            
        return '\n'.join(translated_lines)
        
    def _java_to_javascript(self, code: str) -> str:
        """Translate Java to JavaScript"""
        lines = code.split('\n')
        translated_lines = []
        
        for line in lines:
            # Skip package declarations
            if line.strip().startswith('package'):
                continue
                
            # Convert imports
            import_match = re.match(r'(\s*)import\s+(.*?);', line)
            if import_match:
                spaces, import_path = import_match.groups()
                # Convert common Java imports to JS equivalents where possible
                continue
                
            # Class definitions
            class_match = re.match(
                r'(\s*)(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{',
                line
            )
            if class_match:
                spaces, class_name, parent = class_match.groups()
                if parent:
                    translated_lines.append(f'{spaces}class {class_name} extends {parent} {{')
                else:
                    translated_lines.append(f'{spaces}class {class_name} {{')
                continue
                
            # System.out.println to console.log
            line = re.sub(r'System\.out\.println\s*\((.*?)\)', r'console.log(\1)', line)
            
            # Remove type declarations for variables
            line = re.sub(r'\b(int|double|String|boolean|float|char)\s+(\w+)\s*=', r'let \2 =', line)
            
            translated_lines.append(line)
            
        return '\n'.join(translated_lines)
        
    def _generic_translation(self, code: str, source_lang: str, target_lang: str) -> str:
        """Generic translation attempt for unsupported combinations"""
        # This is a fallback - just return code with a comment
        return f"// Note: Direct translation from {source_lang} to {target_lang} may require manual adjustments\n{code}"
        
    def _infer_java_type(self, value: str) -> str:
        """Simple type inference for Java"""
        value = value.strip()
        if value.isdigit():
            return "int"
        elif value.replace('.', '').replace('-', '').isdigit():
            return "double"
        elif value.startswith('"') or value.startswith("'"):
            return "String"
        elif value in ('true', 'false'):
            return "boolean"
        else:
            return "Object"
            
    def _infer_java_params(self, params: str) -> str:
        """Add simple types to Java parameters"""
        if not params.strip():
            return ""
            
        typed_params = []
        for param in params.split(','):
            param = param.strip()
            if param:
                typed_params.append(f"Object {param}")
                
        return ', '.join(typed_params)