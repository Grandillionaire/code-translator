"""
Complexity Analyzer for Code Translator
Calculates cyclomatic complexity, estimates Big-O, and suggests optimizations
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class BigO(Enum):
    """Big-O complexity classifications"""
    O_1 = "O(1)"
    O_LOG_N = "O(log n)"
    O_N = "O(n)"
    O_N_LOG_N = "O(n log n)"
    O_N_SQUARED = "O(n²)"
    O_N_CUBED = "O(n³)"
    O_2_N = "O(2^n)"
    O_N_FACTORIAL = "O(n!)"
    UNKNOWN = "Unknown"


@dataclass
class FunctionAnalysis:
    """Analysis results for a single function"""
    name: str
    start_line: int
    end_line: int
    cyclomatic_complexity: int
    estimated_big_o: BigO
    nesting_depth: int
    parameter_count: int
    has_recursion: bool
    loop_count: int
    branch_count: int
    suggestions: List[str] = field(default_factory=list)


@dataclass
class CodeAnalysis:
    """Complete analysis results for code"""
    language: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    functions: List[FunctionAnalysis]
    average_complexity: float
    max_complexity: int
    overall_big_o: BigO
    suggestions: List[str] = field(default_factory=list)


class ComplexityAnalyzer:
    """Analyzes code complexity and provides optimization suggestions"""

    # Complexity thresholds
    LOW_COMPLEXITY = 5
    MEDIUM_COMPLEXITY = 10
    HIGH_COMPLEXITY = 20

    def __init__(self):
        """Initialize the complexity analyzer"""
        self.language_patterns = {
            "Python": {
                "function": r"^\s*(async\s+)?def\s+(\w+)\s*\(",
                "class": r"^\s*class\s+(\w+)",
                "if": r"\b(if|elif)\s+",
                "else": r"\belse\s*:",
                "for": r"\bfor\s+\w+\s+in\s+",
                "while": r"\bwhile\s+",
                "try": r"\btry\s*:",
                "except": r"\bexcept\s*",
                "and": r"\band\b",
                "or": r"\bor\b",
                "ternary": r".+\sif\s+.+\selse\s+",
                "comprehension": r"\[.+\sfor\s+.+\sin\s+.+\]",
                "recursion_check": lambda code, name: re.search(rf"\b{name}\s*\(", code) is not None,
                "comment": r"^\s*#",
                "docstring_start": r'^\s*("""|\'\'\')',
            },
            "JavaScript": {
                "function": r"(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?function|\bconst\s+(\w+)\s*=\s*(?:async\s+)?\()",
                "class": r"\bclass\s+(\w+)",
                "if": r"\bif\s*\(",
                "else": r"\belse\s*[{\n]",
                "for": r"\bfor\s*\(",
                "while": r"\bwhile\s*\(",
                "try": r"\btry\s*\{",
                "catch": r"\bcatch\s*\(",
                "and": r"&&",
                "or": r"\|\|",
                "ternary": r"\?.+:",
                "recursion_check": lambda code, name: re.search(rf"\b{name}\s*\(", code) is not None,
                "comment": r"^\s*//",
                "block_comment_start": r"/\*",
            },
            "Java": {
                "function": r"(?:public|private|protected)\s+(?:static\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(",
                "class": r"\bclass\s+(\w+)",
                "if": r"\bif\s*\(",
                "else": r"\belse\s*[{\n]",
                "for": r"\bfor\s*\(",
                "while": r"\bwhile\s*\(",
                "try": r"\btry\s*\{",
                "catch": r"\bcatch\s*\(",
                "and": r"&&",
                "or": r"\|\|",
                "ternary": r"\?.+:",
                "recursion_check": lambda code, name: re.search(rf"\b{name}\s*\(", code) is not None,
                "comment": r"^\s*//",
                "block_comment_start": r"/\*",
            },
        }
        
        # Copy patterns for similar languages
        self.language_patterns["TypeScript"] = self.language_patterns["JavaScript"]
        self.language_patterns["Go"] = self._create_go_patterns()
        self.language_patterns["Rust"] = self._create_rust_patterns()

    def _create_go_patterns(self) -> Dict:
        """Create Go-specific patterns"""
        return {
            "function": r"\bfunc\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(",
            "if": r"\bif\s+",
            "else": r"\belse\s*{",
            "for": r"\bfor\s+",
            "switch": r"\bswitch\s+",
            "select": r"\bselect\s*{",
            "and": r"&&",
            "or": r"\|\|",
            "recursion_check": lambda code, name: re.search(rf"\b{name}\s*\(", code) is not None,
            "comment": r"^\s*//",
        }

    def _create_rust_patterns(self) -> Dict:
        """Create Rust-specific patterns"""
        return {
            "function": r"\bfn\s+(\w+)\s*[<(]",
            "if": r"\bif\s+",
            "else": r"\belse\s*{",
            "for": r"\bfor\s+\w+\s+in\s+",
            "while": r"\bwhile\s+",
            "loop": r"\bloop\s*{",
            "match": r"\bmatch\s+",
            "and": r"&&",
            "or": r"\|\|",
            "recursion_check": lambda code, name: re.search(rf"\b{name}\s*\(", code) is not None,
            "comment": r"^\s*//",
        }

    def analyze(self, code: str, language: str) -> CodeAnalysis:
        """
        Perform complete complexity analysis on code.
        
        Args:
            code: Source code to analyze
            language: Programming language
            
        Returns:
            CodeAnalysis with complete results
        """
        lines = code.split('\n')
        
        # Count line types
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comment_lines(code, language)
        code_lines = total_lines - blank_lines - comment_lines
        
        # Analyze functions
        functions = self._analyze_functions(code, language)
        
        # Calculate averages
        if functions:
            avg_complexity = sum(f.cyclomatic_complexity for f in functions) / len(functions)
            max_complexity = max(f.cyclomatic_complexity for f in functions)
        else:
            avg_complexity = 0.0
            max_complexity = 0
        
        # Estimate overall Big-O
        overall_big_o = self._estimate_overall_big_o(functions)
        
        # Generate overall suggestions
        suggestions = self._generate_overall_suggestions(functions, avg_complexity)
        
        return CodeAnalysis(
            language=language,
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            functions=functions,
            average_complexity=round(avg_complexity, 2),
            max_complexity=max_complexity,
            overall_big_o=overall_big_o,
            suggestions=suggestions
        )

    def _count_comment_lines(self, code: str, language: str) -> int:
        """Count lines that are primarily comments"""
        patterns = self.language_patterns.get(language, {})
        comment_pattern = patterns.get("comment", r"^\s*#")
        
        count = 0
        in_block_comment = False
        
        for line in code.split('\n'):
            if language == "Python":
                if re.match(patterns.get("docstring_start", r'^\s*("""|\'\'\')''), line):
                    in_block_comment = not in_block_comment
                    count += 1
                    continue
            else:
                if "/*" in line:
                    in_block_comment = True
                if "*/" in line:
                    in_block_comment = False
                    count += 1
                    continue
            
            if in_block_comment or re.match(comment_pattern, line):
                count += 1
        
        return count

    def _analyze_functions(self, code: str, language: str) -> List[FunctionAnalysis]:
        """Analyze all functions in the code"""
        functions = []
        patterns = self.language_patterns.get(language, self.language_patterns.get("Python"))
        
        if not patterns:
            return functions
        
        func_pattern = patterns.get("function")
        if not func_pattern:
            return functions
        
        lines = code.split('\n')
        
        # Find all function definitions
        for i, line in enumerate(lines):
            match = re.search(func_pattern, line)
            if match:
                # Get function name (find first non-None group)
                name = next((g for g in match.groups() if g), None)
                if not name:
                    continue
                
                # Find function body
                start_line = i + 1
                end_line, func_code = self._extract_function_body(lines, i, language)
                
                # Analyze function
                analysis = self._analyze_single_function(
                    name, func_code, start_line, end_line, language, patterns
                )
                functions.append(analysis)
        
        return functions

    def _extract_function_body(
        self,
        lines: List[str],
        start_idx: int,
        language: str
    ) -> Tuple[int, str]:
        """Extract the body of a function"""
        if language == "Python":
            # Python uses indentation
            base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
            func_lines = [lines[start_idx]]
            
            for i in range(start_idx + 1, len(lines)):
                line = lines[i]
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    if indent <= base_indent:
                        return i, '\n'.join(func_lines)
                func_lines.append(line)
            
            return len(lines), '\n'.join(func_lines)
        
        else:
            # C-style languages use braces
            brace_count = 0
            func_lines = []
            found_start = False
            
            for i in range(start_idx, len(lines)):
                line = lines[i]
                func_lines.append(line)
                
                brace_count += line.count('{') - line.count('}')
                
                if '{' in line:
                    found_start = True
                
                if found_start and brace_count == 0:
                    return i + 1, '\n'.join(func_lines)
            
            return len(lines), '\n'.join(func_lines)

    def _analyze_single_function(
        self,
        name: str,
        code: str,
        start_line: int,
        end_line: int,
        language: str,
        patterns: Dict
    ) -> FunctionAnalysis:
        """Analyze a single function"""
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(code, patterns)
        
        # Count loops and branches
        loop_count = self._count_loops(code, patterns)
        branch_count = self._count_branches(code, patterns)
        
        # Calculate nesting depth
        nesting_depth = self._calculate_nesting_depth(code, language)
        
        # Check for recursion
        recursion_check = patterns.get("recursion_check")
        has_recursion = False
        if callable(recursion_check):
            # Check in function body (skip the definition line)
            body_lines = code.split('\n')[1:]
            body = '\n'.join(body_lines)
            has_recursion = recursion_check(body, name)
        
        # Estimate Big-O
        big_o = self._estimate_big_o(code, loop_count, has_recursion, patterns)
        
        # Count parameters
        param_count = self._count_parameters(code)
        
        # Generate suggestions
        suggestions = self._generate_function_suggestions(
            name, complexity, nesting_depth, loop_count, has_recursion
        )
        
        return FunctionAnalysis(
            name=name,
            start_line=start_line,
            end_line=end_line,
            cyclomatic_complexity=complexity,
            estimated_big_o=big_o,
            nesting_depth=nesting_depth,
            parameter_count=param_count,
            has_recursion=has_recursion,
            loop_count=loop_count,
            branch_count=branch_count,
            suggestions=suggestions
        )

    def _calculate_cyclomatic_complexity(self, code: str, patterns: Dict) -> int:
        """
        Calculate cyclomatic complexity.
        CC = E - N + 2P (simplified to decision points + 1)
        """
        complexity = 1  # Base complexity
        
        decision_patterns = ["if", "elif", "else", "for", "while", "try", 
                          "except", "catch", "switch", "case", "and", "or"]
        
        for pattern_name in decision_patterns:
            pattern = patterns.get(pattern_name)
            if pattern:
                complexity += len(re.findall(pattern, code))
        
        # Count ternary operators
        ternary = patterns.get("ternary")
        if ternary:
            complexity += len(re.findall(ternary, code))
        
        return complexity

    def _count_loops(self, code: str, patterns: Dict) -> int:
        """Count loop constructs"""
        count = 0
        for pattern_name in ["for", "while", "loop"]:
            pattern = patterns.get(pattern_name)
            if pattern:
                count += len(re.findall(pattern, code))
        return count

    def _count_branches(self, code: str, patterns: Dict) -> int:
        """Count branch constructs"""
        count = 0
        for pattern_name in ["if", "elif", "else", "switch", "match"]:
            pattern = patterns.get(pattern_name)
            if pattern:
                count += len(re.findall(pattern, code))
        return count

    def _calculate_nesting_depth(self, code: str, language: str) -> int:
        """Calculate maximum nesting depth"""
        if language == "Python":
            max_depth = 0
            for line in code.split('\n'):
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    depth = indent // 4  # Assume 4-space indent
                    max_depth = max(max_depth, depth)
            return max_depth
        else:
            max_depth = 0
            current_depth = 0
            for char in code:
                if char == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == '}':
                    current_depth = max(0, current_depth - 1)
            return max_depth

    def _count_parameters(self, code: str) -> int:
        """Count function parameters"""
        match = re.search(r'\(([^)]*)\)', code)
        if match:
            params = match.group(1)
            if not params.strip():
                return 0
            return len([p for p in params.split(',') if p.strip()])
        return 0

    def _estimate_big_o(
        self,
        code: str,
        loop_count: int,
        has_recursion: bool,
        patterns: Dict
    ) -> BigO:
        """Estimate Big-O complexity"""
        # Check for nested loops
        nested_loop_patterns = [
            r'for.*:\s*\n\s+for',  # Python
            r'for\s*\([^)]+\)\s*\{[^}]*for\s*\(',  # C-style
        ]
        
        nested_loops = 0
        for pattern in nested_loop_patterns:
            nested_loops += len(re.findall(pattern, code, re.DOTALL))
        
        # Check for sorting patterns
        sort_patterns = [r'\.sort\(', r'sorted\(', r'Arrays\.sort', r'\.sort\s*\(']
        has_sort = any(re.search(p, code) for p in sort_patterns)
        
        # Check for binary search patterns
        binary_search_patterns = [
            r'while\s+(?:left|lo|low)\s*[<>=]+\s*(?:right|hi|high)',
            r'mid\s*=\s*\([^)]+\)\s*/\s*2',
            r'bisect',
            r'binary[_\s]?search'
        ]
        has_binary_search = any(re.search(p, code, re.IGNORECASE) for p in binary_search_patterns)
        
        # Estimate based on patterns
        if has_recursion and nested_loops > 0:
            return BigO.O_2_N
        elif nested_loops >= 2:
            return BigO.O_N_CUBED
        elif nested_loops == 1:
            return BigO.O_N_SQUARED
        elif has_sort:
            return BigO.O_N_LOG_N
        elif has_binary_search:
            return BigO.O_LOG_N
        elif loop_count >= 1:
            return BigO.O_N
        elif has_recursion:
            return BigO.O_N  # Conservative estimate for recursion
        else:
            return BigO.O_1

    def _estimate_overall_big_o(self, functions: List[FunctionAnalysis]) -> BigO:
        """Estimate overall Big-O from all functions"""
        if not functions:
            return BigO.O_1
        
        # Use the worst case
        complexity_order = [
            BigO.O_1, BigO.O_LOG_N, BigO.O_N, BigO.O_N_LOG_N,
            BigO.O_N_SQUARED, BigO.O_N_CUBED, BigO.O_2_N, BigO.O_N_FACTORIAL
        ]
        
        worst = BigO.O_1
        for func in functions:
            if func.estimated_big_o != BigO.UNKNOWN:
                if complexity_order.index(func.estimated_big_o) > complexity_order.index(worst):
                    worst = func.estimated_big_o
        
        return worst

    def _generate_function_suggestions(
        self,
        name: str,
        complexity: int,
        nesting_depth: int,
        loop_count: int,
        has_recursion: bool
    ) -> List[str]:
        """Generate optimization suggestions for a function"""
        suggestions = []
        
        if complexity > self.HIGH_COMPLEXITY:
            suggestions.append(
                f"High complexity ({complexity}). Consider breaking into smaller functions."
            )
        elif complexity > self.MEDIUM_COMPLEXITY:
            suggestions.append(
                f"Moderate complexity ({complexity}). Review for potential simplification."
            )
        
        if nesting_depth > 4:
            suggestions.append(
                f"Deep nesting ({nesting_depth} levels). Consider early returns or guard clauses."
            )
        
        if loop_count > 2:
            suggestions.append(
                "Multiple loops detected. Consider combining or using more efficient data structures."
            )
        
        if has_recursion:
            suggestions.append(
                "Contains recursion. Ensure base case is correct and consider tail recursion or iteration."
            )
        
        return suggestions

    def _generate_overall_suggestions(
        self,
        functions: List[FunctionAnalysis],
        avg_complexity: float
    ) -> List[str]:
        """Generate overall code suggestions"""
        suggestions = []
        
        if avg_complexity > self.MEDIUM_COMPLEXITY:
            suggestions.append(
                f"High average complexity ({avg_complexity:.1f}). Consider refactoring complex functions."
            )
        
        high_complexity_funcs = [f for f in functions if f.cyclomatic_complexity > self.HIGH_COMPLEXITY]
        if high_complexity_funcs:
            names = ", ".join(f.name for f in high_complexity_funcs[:3])
            suggestions.append(
                f"Functions with high complexity: {names}. Priority targets for refactoring."
            )
        
        deep_nesting_funcs = [f for f in functions if f.nesting_depth > 4]
        if deep_nesting_funcs:
            suggestions.append(
                "Some functions have deep nesting. Consider flattening with early returns."
            )
        
        recursive_funcs = [f for f in functions if f.has_recursion]
        if recursive_funcs:
            suggestions.append(
                f"{len(recursive_funcs)} recursive function(s) detected. Verify termination conditions."
            )
        
        return suggestions

    def get_complexity_rating(self, complexity: int) -> str:
        """Get human-readable complexity rating"""
        if complexity <= self.LOW_COMPLEXITY:
            return "Low"
        elif complexity <= self.MEDIUM_COMPLEXITY:
            return "Moderate"
        elif complexity <= self.HIGH_COMPLEXITY:
            return "High"
        else:
            return "Very High"

    def format_analysis(self, analysis: CodeAnalysis) -> str:
        """Format analysis results as readable text"""
        lines = [
            "=" * 60,
            "CODE COMPLEXITY ANALYSIS",
            "=" * 60,
            "",
            f"Language: {analysis.language}",
            f"Total Lines: {analysis.total_lines}",
            f"  - Code: {analysis.code_lines}",
            f"  - Comments: {analysis.comment_lines}",
            f"  - Blank: {analysis.blank_lines}",
            "",
            f"Functions Analyzed: {len(analysis.functions)}",
            f"Average Complexity: {analysis.average_complexity} ({self.get_complexity_rating(int(analysis.average_complexity))})",
            f"Maximum Complexity: {analysis.max_complexity}",
            f"Overall Time Complexity: {analysis.overall_big_o.value}",
            "",
        ]
        
        if analysis.functions:
            lines.append("-" * 60)
            lines.append("FUNCTION DETAILS")
            lines.append("-" * 60)
            
            for func in sorted(analysis.functions, key=lambda f: -f.cyclomatic_complexity):
                lines.append(f"\n{func.name}:")
                lines.append(f"  Lines: {func.start_line}-{func.end_line}")
                lines.append(f"  Complexity: {func.cyclomatic_complexity} ({self.get_complexity_rating(func.cyclomatic_complexity)})")
                lines.append(f"  Time Complexity: {func.estimated_big_o.value}")
                lines.append(f"  Nesting Depth: {func.nesting_depth}")
                lines.append(f"  Parameters: {func.parameter_count}")
                lines.append(f"  Loops: {func.loop_count}, Branches: {func.branch_count}")
                if func.has_recursion:
                    lines.append("  ⚠️ Contains recursion")
                
                if func.suggestions:
                    lines.append("  Suggestions:")
                    for suggestion in func.suggestions:
                        lines.append(f"    • {suggestion}")
        
        if analysis.suggestions:
            lines.append("")
            lines.append("-" * 60)
            lines.append("OVERALL SUGGESTIONS")
            lines.append("-" * 60)
            for suggestion in analysis.suggestions:
                lines.append(f"• {suggestion}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
