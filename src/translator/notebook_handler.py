"""
Jupyter Notebook Handler for Code Translator
Parses, translates, and outputs .ipynb files
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import copy


@dataclass
class NotebookCell:
    """Represents a Jupyter notebook cell"""
    cell_type: str  # "code", "markdown", "raw"
    source: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    execution_count: Optional[int] = None


@dataclass
class Notebook:
    """Represents a Jupyter notebook"""
    cells: List[NotebookCell]
    metadata: Dict[str, Any]
    nbformat: int
    nbformat_minor: int


class NotebookHandler:
    """Handles Jupyter notebook translation"""

    def __init__(self, translator_engine=None):
        """
        Initialize notebook handler.
        
        Args:
            translator_engine: TranslatorEngine instance for code translation
        """
        self.translator = translator_engine

    def parse_notebook(self, content: str) -> Notebook:
        """
        Parse notebook JSON content.
        
        Args:
            content: JSON string of the notebook
            
        Returns:
            Parsed Notebook object
        """
        data = json.loads(content)
        
        cells = []
        for cell_data in data.get("cells", []):
            cell = NotebookCell(
                cell_type=cell_data.get("cell_type", "code"),
                source=cell_data.get("source", []),
                metadata=cell_data.get("metadata", {}),
                outputs=cell_data.get("outputs", []),
                execution_count=cell_data.get("execution_count")
            )
            cells.append(cell)
        
        return Notebook(
            cells=cells,
            metadata=data.get("metadata", {}),
            nbformat=data.get("nbformat", 4),
            nbformat_minor=data.get("nbformat_minor", 5)
        )

    def parse_notebook_file(self, file_path: str) -> Notebook:
        """
        Parse notebook from file path.
        
        Args:
            file_path: Path to .ipynb file
            
        Returns:
            Parsed Notebook object
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            return self.parse_notebook(f.read())

    def translate_notebook(
        self,
        notebook: Notebook,
        source_lang: str,
        target_lang: str,
        provider=None
    ) -> Tuple[Notebook, Dict[str, Any]]:
        """
        Translate all code cells in a notebook.
        
        Args:
            notebook: Notebook to translate
            source_lang: Source programming language
            target_lang: Target programming language
            provider: Optional translation provider
            
        Returns:
            Tuple of (translated notebook, translation stats)
        """
        if not self.translator:
            raise ValueError("TranslatorEngine not provided. Cannot translate.")
        
        # Deep copy to avoid modifying original
        translated = copy.deepcopy(notebook)
        
        stats = {
            "total_cells": len(notebook.cells),
            "code_cells": 0,
            "markdown_cells": 0,
            "translated_cells": 0,
            "failed_cells": 0,
            "errors": []
        }
        
        for i, cell in enumerate(translated.cells):
            if cell.cell_type == "code":
                stats["code_cells"] += 1
                
                # Get source code as string
                source_code = self._get_cell_source(cell)
                
                if source_code.strip():
                    try:
                        # Translate code
                        translated_code, confidence = self.translator.translate(
                            source_code,
                            source_lang,
                            target_lang,
                            provider
                        )
                        
                        # Update cell source
                        cell.source = [translated_code]
                        cell.outputs = []  # Clear outputs
                        cell.execution_count = None
                        
                        # Add translation metadata
                        cell.metadata["translation"] = {
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "confidence": confidence
                        }
                        
                        stats["translated_cells"] += 1
                        
                    except Exception as e:
                        stats["failed_cells"] += 1
                        stats["errors"].append({
                            "cell_index": i,
                            "error": str(e)
                        })
                        
                        # Add error comment to cell
                        cell.source = [
                            f"# Translation failed: {e}\n",
                            f"# Original code ({source_lang}):\n",
                            source_code
                        ]
            
            elif cell.cell_type == "markdown":
                stats["markdown_cells"] += 1
                # Preserve markdown cells as-is
        
        # Update notebook metadata
        translated.metadata["translation_info"] = {
            "source_language": source_lang,
            "target_language": target_lang,
            "translated_by": "Code Translator"
        }
        
        # Update kernel info for target language
        translated.metadata = self._update_kernel_metadata(
            translated.metadata,
            target_lang
        )
        
        return translated, stats

    def _get_cell_source(self, cell: NotebookCell) -> str:
        """Get cell source as string"""
        if isinstance(cell.source, list):
            return "".join(cell.source)
        return cell.source

    def _update_kernel_metadata(
        self,
        metadata: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Update notebook kernel metadata for target language"""
        metadata = copy.deepcopy(metadata)
        
        kernel_specs = {
            "Python": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "file_extension": ".py"
                }
            },
            "JavaScript": {
                "kernelspec": {
                    "display_name": "JavaScript (Node.js)",
                    "language": "javascript",
                    "name": "javascript"
                },
                "language_info": {
                    "name": "javascript",
                    "file_extension": ".js"
                }
            },
            "TypeScript": {
                "kernelspec": {
                    "display_name": "TypeScript",
                    "language": "typescript",
                    "name": "typescript"
                },
                "language_info": {
                    "name": "typescript",
                    "file_extension": ".ts"
                }
            },
            "Java": {
                "kernelspec": {
                    "display_name": "Java",
                    "language": "java",
                    "name": "java"
                },
                "language_info": {
                    "name": "java",
                    "file_extension": ".java"
                }
            },
            "Go": {
                "kernelspec": {
                    "display_name": "Go",
                    "language": "go",
                    "name": "go"
                },
                "language_info": {
                    "name": "go",
                    "file_extension": ".go"
                }
            },
            "Rust": {
                "kernelspec": {
                    "display_name": "Rust",
                    "language": "rust",
                    "name": "rust"
                },
                "language_info": {
                    "name": "rust",
                    "file_extension": ".rs"
                }
            },
            "Ruby": {
                "kernelspec": {
                    "display_name": "Ruby",
                    "language": "ruby",
                    "name": "ruby"
                },
                "language_info": {
                    "name": "ruby",
                    "file_extension": ".rb"
                }
            }
        }
        
        if target_lang in kernel_specs:
            metadata.update(kernel_specs[target_lang])
        
        return metadata

    def notebook_to_json(self, notebook: Notebook, indent: int = 1) -> str:
        """
        Convert Notebook object back to JSON string.
        
        Args:
            notebook: Notebook to serialize
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        cells_data = []
        for cell in notebook.cells:
            cell_data = {
                "cell_type": cell.cell_type,
                "source": cell.source,
                "metadata": cell.metadata
            }
            
            if cell.cell_type == "code":
                cell_data["outputs"] = cell.outputs
                cell_data["execution_count"] = cell.execution_count
            
            cells_data.append(cell_data)
        
        notebook_data = {
            "cells": cells_data,
            "metadata": notebook.metadata,
            "nbformat": notebook.nbformat,
            "nbformat_minor": notebook.nbformat_minor
        }
        
        return json.dumps(notebook_data, indent=indent, ensure_ascii=False)

    def save_notebook(self, notebook: Notebook, file_path: str) -> None:
        """
        Save notebook to file.
        
        Args:
            notebook: Notebook to save
            file_path: Output file path
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.notebook_to_json(notebook))

    def translate_notebook_file(
        self,
        input_path: str,
        output_path: str,
        source_lang: str,
        target_lang: str,
        provider=None
    ) -> Dict[str, Any]:
        """
        Convenience method to translate a notebook file.
        
        Args:
            input_path: Path to input .ipynb file
            output_path: Path for output .ipynb file
            source_lang: Source programming language
            target_lang: Target programming language
            provider: Optional translation provider
            
        Returns:
            Translation statistics
        """
        notebook = self.parse_notebook_file(input_path)
        translated, stats = self.translate_notebook(
            notebook, source_lang, target_lang, provider
        )
        self.save_notebook(translated, output_path)
        
        stats["input_path"] = input_path
        stats["output_path"] = output_path
        
        return stats

    def extract_code_cells(self, notebook: Notebook) -> List[str]:
        """
        Extract all code from code cells.
        
        Args:
            notebook: Notebook to extract from
            
        Returns:
            List of code strings, one per cell
        """
        code_cells = []
        for cell in notebook.cells:
            if cell.cell_type == "code":
                code_cells.append(self._get_cell_source(cell))
        return code_cells

    def create_notebook_from_code(
        self,
        code_snippets: List[str],
        language: str,
        markdown_headers: Optional[List[str]] = None
    ) -> Notebook:
        """
        Create a new notebook from code snippets.
        
        Args:
            code_snippets: List of code strings
            language: Programming language for kernel
            markdown_headers: Optional headers for each code cell
            
        Returns:
            New Notebook object
        """
        cells = []
        
        for i, code in enumerate(code_snippets):
            # Add markdown header if provided
            if markdown_headers and i < len(markdown_headers):
                cells.append(NotebookCell(
                    cell_type="markdown",
                    source=[f"## {markdown_headers[i]}\n"],
                    metadata={}
                ))
            
            # Add code cell
            cells.append(NotebookCell(
                cell_type="code",
                source=[code],
                metadata={},
                outputs=[],
                execution_count=None
            ))
        
        metadata = self._update_kernel_metadata({}, language)
        
        return Notebook(
            cells=cells,
            metadata=metadata,
            nbformat=4,
            nbformat_minor=5
        )
