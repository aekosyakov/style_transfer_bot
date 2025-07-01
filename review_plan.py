#!/usr/bin/env python3
"""
Script to review AI assistant plans using Gemini CLI
Usage: python review_plan.py "Your plan text here"
"""

import sys
import subprocess
import argparse
from typing import Optional

def setup_gemini_review_prompt(plan_text: str) -> str:
    """Create a structured prompt for Gemini to review the assistant's plan."""
    return f"""
Please review this AI assistant's plan and provide feedback:

PLAN TO REVIEW:
{plan_text}

Please analyze:
1. **Feasibility**: Is this plan technically sound and achievable?
2. **Risks**: What potential issues or risks do you see?
3. **Improvements**: Any suggestions for better approaches?
4. **Missing Steps**: Are there important steps that seem to be missing?
5. **Overall Assessment**: Approve, suggest modifications, or recommend alternative approach?

Provide your response in this format:
ASSESSMENT: [Approve/Modify/Alternative]
RISK LEVEL: [Low/Medium/High]
KEY CONCERNS: [List main concerns]
RECOMMENDATIONS: [Specific suggestions]
"""

def call_gemini_cli_automated(prompt: str) -> Optional[str]:
    """Call Gemini CLI automatically and return the response."""
    try:
        print("🤖 Calling Gemini CLI automatically...")
        print("⏳ Waiting for response...\n")
        
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
                print("✅ Received response from Gemini CLI\n")
                return output
            else:
                print("⚠️ Empty response from Gemini CLI")
                return None
        else:
            print(f"❌ Gemini CLI error (exit code {result.returncode}): {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Gemini CLI timeout - response took too long")
        return None
    except FileNotFoundError:
        print("❌ Gemini CLI not found. Please install: npm install -g @google/generative-ai-cli")
        return None
    except Exception as e:
        print(f"❌ Error calling Gemini CLI: {e}")
        return None

def prepare_review_session(prompt: str) -> str:
    """Prepare a review session by saving the prompt and providing instructions."""
    import tempfile
    import os
    
    # Create a temporary file with the review prompt
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        temp_file = f.name
    
    print(f"📝 Review prompt saved to: {temp_file}")
    print("\n" + "="*60)
    print("🤖 GEMINI CLI REVIEW INSTRUCTIONS")
    print("="*60)
    print("1. The review prompt has been saved to a temporary file")
    print("2. You can now:")
    print("   a) Copy the prompt below and paste it into Gemini CLI")
    print("   b) Or run: gemini")
    print("   c) Then paste the review prompt")
    print("\n📋 REVIEW PROMPT TO COPY:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # Try to copy to clipboard if available
    try:
        import pyperclip
        pyperclip.copy(prompt)
        print("\n✅ Prompt copied to clipboard! You can paste it directly into Gemini CLI.")
    except ImportError:
        print("\n💡 Install pyperclip for auto-copy: pip install pyperclip")
    
    print(f"\n🚀 Ready! Run 'gemini' in another terminal and paste the prompt.")
    print(f"📁 Temp file: {temp_file}")
    
    return temp_file

def launch_gemini_cli() -> bool:
    """Try to launch Gemini CLI in a new terminal/process."""
    try:
        import os
        import platform
        
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            os.system("open -a Terminal && osascript -e 'tell application \"Terminal\" to do script \"gemini\"'")
        elif system == "linux":
            os.system("gnome-terminal -- gemini || xterm -e gemini || konsole -e gemini")
        elif system == "windows":
            os.system("start cmd /k gemini")
        else:
            print(f"❌ Unsupported system: {system}")
            return False
            
        print("✅ Gemini CLI launched in new terminal")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch Gemini CLI: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Review AI assistant plans using Gemini CLI")
    parser.add_argument("plan", nargs='?', help="The plan text to review")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode - read from stdin")
    parser.add_argument("--launch", "-l", action="store_true", help="Try to launch Gemini CLI automatically")
    parser.add_argument("--auto", "-a", action="store_true", help="Fully automated mode - call Gemini CLI automatically")
    parser.add_argument("--debug", "-d", action="store_true", help="Show debug information")
    
    args = parser.parse_args()
    
    # Get the plan text
    if args.interactive:
        print("📝 Enter the plan to review (press Ctrl+D when done):")
        plan_text = sys.stdin.read().strip()
    elif args.plan:
        plan_text = args.plan
    else:
        print("❌ No plan text provided. Use --interactive or provide plan as argument")
        print("Example: python review_plan.py 'I will fix the dress generation bug'")
        sys.exit(1)
    
    if not plan_text:
        print("❌ No plan text provided")
        sys.exit(1)
    
    if args.debug:
        print(f"🔍 Debug: Plan length: {len(plan_text)} characters")
    
    # Create the review prompt
    review_prompt = setup_gemini_review_prompt(plan_text)
    
    if args.debug:
        print("🔍 Debug: Review prompt:")
        print("-" * 50)
        print(review_prompt[:500] + "..." if len(review_prompt) > 500 else review_prompt)
        print("-" * 50)
    
    # Automated mode - call Gemini CLI directly
    if args.auto:
        print("🚀 AUTOMATED REVIEW MODE")
        print("="*50)
        
        response = call_gemini_cli_automated(review_prompt)
        
        if response:
            print("📋 GEMINI CLI RESPONSE:")
            print("="*50)
            print(response)
            print("="*50)
            print("✅ Review completed successfully!")
            return response
        else:
            print("❌ Failed to get automated response")
            return None
    
    # Manual mode (original behavior)
    else:
        # Prepare the review session
        temp_file = prepare_review_session(review_prompt)
        
        # Optionally launch Gemini CLI
        if args.launch:
            print("\n🚀 Attempting to launch Gemini CLI...")
            if launch_gemini_cli():
                print("📋 The review prompt is ready to paste!")
            else:
                print("💡 Please manually run 'gemini' in another terminal")
        
        print("\n" + "="*60)
        print("⏸️  WAITING FOR YOUR REVIEW")
        print("="*60)
        print("1. Run 'gemini' in another terminal")
        print("2. Paste the review prompt (copied to clipboard)")
        print("3. Review Gemini's response")
        print("4. Press Enter here when done...")
        
        input()  # Wait for user input
        
        # Clean up temp file
        try:
            import os
            os.unlink(temp_file)
            print("🗑️  Temporary file cleaned up")
        except:
            pass
        
        print("✅ Review session completed!")

if __name__ == "__main__":
    main() 