#!/usr/bin/env python3
"""
Script to review completed implementations using Gemini CLI (automatically calls Gemini by default)
Usage: python review_implementation.py [--files "file1,file2"] [--manual]
"""

import sys
import subprocess
import argparse
import json
from typing import Optional, List


def get_file_changes(files: List[str]) -> str:
    """Get changes for specific files."""
    if not files:
        return ""
    
    try:
        changes = []
        for file in files:
            # Get recent changes to the file
            result = subprocess.run(
                ['git', 'log', '--oneline', '-5', '--', file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                changes.append(f"\nFILE: {file}\nRecent changes:\n{result.stdout.strip()}")
        
        return "\n".join(changes) if changes else "No recent changes found for specified files"
        
    except Exception as e:
        return f"Error getting file changes: {e}"

def get_project_status() -> str:
    """Get current project status."""
    try:
        # Get current branch and status
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        status = status_result.stdout.strip() if status_result.returncode == 0 else ""
        
        # Count files by type
        try:
            result = subprocess.run(['find', '.', '-name', '*.py', '-not', '-path', './venv/*'], 
                                  capture_output=True, text=True, timeout=10)
            py_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except:
            py_files = "unknown"
        
        return f"""PROJECT STATUS:
Branch: {branch}
Python files: {py_files}
Working directory: {'Clean' if not status else 'Has uncommitted changes'}
{f'Uncommitted: {status}' if status else ''}"""
        
    except Exception as e:
        return f"Error getting project status: {e}"

def create_implementation_review_prompt(files_info: str, project_status: str, 
                                       custom_context: str = "") -> str:
    """Create a structured prompt for Gemini to review the implementation."""
    
    prompt = f"""Please review this AI assistant's implementation and provide feedback:

{project_status}

{files_info}

{custom_context}

Please analyze the implementation against these criteria:

1. **Code Quality**: Is the code well-structured, readable, and maintainable?
2. **Architecture**: Does the implementation follow good architectural principles?
3. **Testing**: Is there adequate test coverage for the changes?
4. **Documentation**: Are the changes properly documented?
5. **Git Practices**: Are commits atomic, well-described, and following good practices?
6. **Completion**: Does the implementation appear complete and production-ready?
7. **Potential Issues**: What risks or problems do you see?
8. **Improvements**: What could be done better?

Provide your response in this format:
IMPLEMENTATION_QUALITY: [Excellent/Good/Fair/Poor]
ARCHITECTURE_SCORE: [1-10]
TESTING_COVERAGE: [Excellent/Good/Fair/Poor/Missing]
KEY_STRENGTHS: [List main strengths]
CONCERNS: [List main concerns]
RECOMMENDATIONS: [Specific suggestions for improvement]
OVERALL_ASSESSMENT: [Approve for production/Needs minor fixes/Needs major revision/Reject]
"""
    
    return prompt

def call_gemini_cli_automated(prompt: str) -> Optional[str]:
    """Call Gemini CLI automatically and return the response."""
    try:
        print("🤖 Calling Gemini CLI for implementation review...")
        print("⏳ Analyzing implementation...\n")
        
        # Use subprocess to send prompt to gemini CLI
        result = subprocess.run(
            ['gemini'],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=120
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print("✅ Received implementation review from Gemini CLI\n")
                return output
            else:
                print("⚠️ Empty response from Gemini CLI")
                return None
        else:
            print(f"❌ Gemini CLI error (exit code {result.returncode}): {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Gemini CLI timeout - review took too long")
        return None
    except FileNotFoundError:
        print("❌ Gemini CLI not found. Please install: npm install -g @google/generative-ai-cli")
        return None
    except Exception as e:
        print(f"❌ Error calling Gemini CLI: {e}")
        return None

def copy_to_clipboard(text: str) -> bool:
    """Try to copy text to clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        return False

def main():
    parser = argparse.ArgumentParser(description="Review completed implementations using Gemini CLI")
    parser.add_argument("--files", "-f", type=str, help="Comma-separated list of specific files to review")
    parser.add_argument("--context", type=str, help="Additional context about the implementation")
    parser.add_argument("--auto", "-a", action="store_true", help="Explicitly use automated mode (default behavior)")
    parser.add_argument("--manual", "-m", action="store_true", help="Manual mode - copy prompt to clipboard only")
    parser.add_argument("--debug", "-d", action="store_true", help="Show debug information")
    
    args = parser.parse_args()
    
    if args.debug:
        if args.files:
            print(f"🔍 Debug: Specific files: {args.files}")
        else:
            print("🔍 Debug: Reviewing project status and recent changes")
    
    # Get implementation information
    print("📊 Gathering implementation information...")
    
    files_info = ""
    if args.files:
        files_list = [f.strip() for f in args.files.split(',')]
        files_info = get_file_changes(files_list)
    
    project_status = get_project_status()
    
    custom_context = ""
    if args.context:
        custom_context = f"ADDITIONAL CONTEXT:\n{args.context}\n"
    
    # Create review prompt
    review_prompt = create_implementation_review_prompt(
        files_info, project_status, custom_context
    )
    
    if args.debug:
        print("🔍 Debug: Review prompt created")
        print("-" * 50)
        print(review_prompt[:500] + "..." if len(review_prompt) > 500 else review_prompt)
        print("-" * 50)
    
    # Handle different modes
    if args.auto:
        print("🚀 AUTOMATED IMPLEMENTATION REVIEW")
        print("=" * 50)
        
        response = call_gemini_cli_automated(review_prompt)
        
        if response:
            print("📋 GEMINI IMPLEMENTATION REVIEW:")
            print("=" * 50)
            print(response)
            print("=" * 50)
            print("✅ Implementation review completed!")
            return response
        else:
            print("❌ Failed to get automated review")
            return None
    
    elif args.manual:
        print("📋 MANUAL REVIEW MODE")
        print("=" * 50)
        
        if copy_to_clipboard(review_prompt):
            print("✅ Review prompt copied to clipboard!")
        else:
            print("💡 Install pyperclip for auto-copy: pip install pyperclip")
        
        print("\n📋 REVIEW PROMPT:")
        print("-" * 40)
        print(review_prompt)
        print("-" * 40)
        print("\n🚀 Paste this into Gemini CLI for review")
        
    else:
        # Default: use automated mode
        print("🚀 AUTOMATED IMPLEMENTATION REVIEW (default mode)")
        print("=" * 50)
        
        response = call_gemini_cli_automated(review_prompt)
        
        if response:
            print("📋 GEMINI IMPLEMENTATION REVIEW:")
            print("=" * 50)
            print(response)
            print("=" * 50)
            print("✅ Implementation review completed!")
            return response
        else:
            print("❌ Failed to get automated review")
            print("💡 Try manual mode: python review_implementation.py --manual")
            return None

if __name__ == "__main__":
    main() 