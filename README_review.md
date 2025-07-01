# AI Plan Review Script

This script allows you to review AI assistant plans using Gemini CLI before execution.

## Prerequisites

1. **Gemini CLI installed:**
   ```bash
   npm install -g @google/gemini-cli
   ```

2. **Authentication set up:**
   - Either sign in with Google account when prompted
   - Or set `GEMINI_API_KEY` environment variable

3. **Python dependencies (auto-installed):**
   ```bash
   pip install pyperclip
   ```

## Usage

### Basic Usage
```bash
python3 review_plan.py "Your plan description here"
```

### Interactive Mode
```bash
python3 review_plan.py --interactive
# Then paste your plan and press Ctrl+D
```

### With Auto-Launch
```bash
python3 review_plan.py --launch "Your plan here"
# Attempts to open Gemini CLI automatically
```

### Debug Mode
```bash
python3 review_plan.py --debug "Your plan here"
# Shows additional debug information
```

## How It Works

1. **Input**: Takes your plan as argument or via stdin
2. **Prepare**: Creates a structured review prompt for Gemini
3. **Copy**: Automatically copies the prompt to clipboard
4. **Guide**: Shows clear instructions for using with Gemini CLI
5. **Review**: You paste the prompt into Gemini CLI and get feedback
6. **Cleanup**: Removes temporary files when done

## Example Workflow

```bash
# 1. Run the review script with your plan
python3 review_plan.py "I will fix the database connection issue by updating the connection string and adding retry logic"

# 2. The script will:
#    - Create a review prompt
#    - Copy it to clipboard
#    - Show instructions

# 3. In another terminal, run:
gemini

# 4. Paste the review prompt (Cmd+V on macOS)

# 5. Review Gemini's feedback

# 6. Press Enter in the review script to finish
```

## Review Format

The script structures the review prompt to ask Gemini for:

- **Feasibility**: Is the plan technically sound?
- **Risks**: What potential issues exist?
- **Improvements**: Suggestions for better approaches
- **Missing Steps**: Important steps that might be missing
- **Overall Assessment**: Approve/Modify/Alternative recommendation

## Exit Codes

- `0`: Review completed successfully
- `1`: Error in input or setup

## Tips

- Keep plans concise but specific
- Include technical details for better review
- Use debug mode to see the full review prompt
- The clipboard copy feature works on macOS, Linux, and Windows 