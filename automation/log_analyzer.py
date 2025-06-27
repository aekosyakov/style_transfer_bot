#!/usr/bin/env python3
"""
Log Analyzer for Cursor Integration
──────────────────────────────────
Analyzes server logs and provides insights for the AI agent.
Simple and robust - no fragile pattern matching.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class LogAnalyzer:
    def analyze_logs_from_file(self, log_file: Path = Path("logs/server_logs.jsonl")) -> Dict:
        """Analyze logs from the stored log file."""
        if not log_file.exists():
            return {"error": "Log file not found", "suggestions": ["Run log_monitor.py first to collect logs"]}
        
        analysis = {
            "total_entries": 0,
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "recent_errors": [],
            "recent_warnings": [],
            "error_summary": {},
            "recommendations": []
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        analysis["total_entries"] += 1
                        
                        # Extract log level and message
                        message = entry.get("message", "")
                        timestamp = entry.get("timestamp", "")
                        
                        # Determine level from the actual message content
                        level = "INFO"  # default
                        if "ERROR" in message:
                            level = "ERROR"
                            analysis["error_count"] += 1
                            
                            # Add to recent errors (keep last 10)
                            if len(analysis["recent_errors"]) < 10:
                                analysis["recent_errors"].append({
                                    "timestamp": timestamp,
                                    "message": message
                                })
                            
                            # Categorize errors by type (simple keyword matching)
                            error_type = "UNKNOWN"
                            if "FLUX" in message:
                                error_type = "FLUX_RESTORE"
                            elif "SUPIR" in message:
                                error_type = "SUPIR"
                            elif "DDColor" in message:
                                error_type = "DDCOLOR"
                            elif "CodeFormer" in message:
                                error_type = "CODEFORMER"
                            elif "Magic" in message:
                                error_type = "MAGIC"
                            elif "Real-ESRGAN" in message:
                                error_type = "REALESRGAN"
                            
                            if error_type not in analysis["error_summary"]:
                                analysis["error_summary"][error_type] = 0
                            analysis["error_summary"][error_type] += 1
                            
                        elif "WARNING" in message:
                            level = "WARNING"
                            analysis["warning_count"] += 1
                            
                            # Add to recent warnings (keep last 5)
                            if len(analysis["recent_warnings"]) < 5:
                                analysis["recent_warnings"].append({
                                    "timestamp": timestamp,
                                    "message": message
                                })
                        else:
                            analysis["info_count"] += 1
                    
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            analysis["error"] = f"Error reading log file: {e}"
            
        # Generate simple recommendations
        analysis["recommendations"] = self.generate_recommendations(analysis)
        
        return analysis
    
    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate simple recommendations based on actual errors found."""
        recommendations = []
        
        # Overall health check
        if analysis["error_count"] == 0 and analysis["warning_count"] == 0:
            recommendations.append("✅ No errors or warnings found - bot is running smoothly")
            return recommendations
        
        if analysis["error_count"] > 0:
            recommendations.append(f"🔴 Found {analysis['error_count']} errors in logs")
            
            # Specific recommendations based on error types
            for error_type, count in analysis["error_summary"].items():
                if count > 0:
                    if error_type in ["FLUX_RESTORE", "SUPIR", "DDCOLOR", "CODEFORMER"]:
                        recommendations.append(f"  • {error_type}: {count} errors - Check model references and API parameters")
                    elif error_type == "MAGIC":
                        recommendations.append(f"  • {error_type}: {count} errors - Check Magic API status")
                    elif error_type == "REALESRGAN":
                        recommendations.append(f"  • {error_type}: {count} errors - Check Replicate API status")
                    else:
                        recommendations.append(f"  • {error_type}: {count} errors - Review recent changes")
        
        if analysis["warning_count"] > 0:
            recommendations.append(f"🟡 Found {analysis['warning_count']} warnings in logs")
        
        # Show most recent error if available
        if analysis["recent_errors"]:
            latest_error = analysis["recent_errors"][-1]
            recommendations.append(f"🔍 Most recent error: {latest_error['message'][:100]}...")
        
        return recommendations
    
    def show_recent_logs(self, log_file: Path = Path("logs/server_logs.jsonl"), count: int = 20, errors_only: bool = False) -> None:
        """Show recent log entries in a clean, readable format."""
        if not log_file.exists():
            print("❌ Log file not found. Run log_monitor.py first to collect logs.")
            return
        
        try:
            # Read last N lines from file
            entries = []
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Parse last N entries
            for line in lines[-count:]:
                try:
                    entry = json.loads(line.strip())
                    message = entry.get("message", "")
                    timestamp = entry.get("timestamp", "")
                    
                    # Determine level from message content
                    level = "INFO"
                    if "ERROR" in message:
                        level = "ERROR"
                    elif "WARNING" in message:
                        level = "WARNING"
                    
                    # Filter if errors_only is requested
                    if errors_only and level == "INFO":
                        continue
                    
                    entries.append({
                        "timestamp": timestamp,
                        "level": level,
                        "message": message
                    })
                except json.JSONDecodeError:
                    continue
            
            # Display entries
            if not entries:
                if errors_only:
                    print("✅ No recent errors or warnings found!")
                else:
                    print("ℹ️ No recent log entries found.")
                return
            
            print(f"📋 Recent {'errors/warnings' if errors_only else 'log entries'} (last {len(entries)}):")
            print("=" * 80)
            
            for entry in entries:
                # Format timestamp (show only time part)
                timestamp = entry["timestamp"]
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        time_str = timestamp[:10] + "..."
                else:
                    time_str = "Unknown"
                
                # Format level with colors/emojis
                level = entry["level"]
                if level == "ERROR":
                    level_display = "🔴 ERROR"
                elif level == "WARNING":
                    level_display = "🟡 WARN "
                else:
                    level_display = "🔵 INFO "
                
                # Clean and shorten message
                message = entry["message"]
                
                # Extract key information from the message
                if "callback:" in message:
                    # Extract callback information
                    parts = message.split("callback:")
                    if len(parts) > 1:
                        callback_info = parts[1].strip()
                        message = f"💬 Callback: {callback_info}"
                elif "HTTP Request:" in message:
                    # Shorten HTTP requests
                    if "200 OK" in message:
                        message = "🌐 API Request: ✅ Success"
                    elif "404 Not Found" in message:
                        message = "🌐 API Request: ❌ 404 Not Found"
                    else:
                        message = "🌐 API Request: " + message.split("HTTP Request:")[-1].strip()
                elif "Update" in message and "is handled" in message:
                    # Shorten telegram update messages
                    message = "📨 Telegram update processed"
                elif any(model in message for model in ["SUPIR", "DDColor", "CodeFormer", "FLUX", "Magic", "Real-ESRGAN"]):
                    # Highlight model-related messages
                    for model in ["SUPIR", "DDColor", "CodeFormer", "FLUX", "Magic", "Real-ESRGAN"]:
                        if model in message:
                            message = f"🤖 {model}: " + message.split(model)[-1].strip()
                            break
                
                # Limit message length
                if len(message) > 100:
                    message = message[:97] + "..."
                
                print(f"{time_str} {level_display} {message}")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error reading log file: {e}")

def main():
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description='Analyze server logs')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--log-file', default='logs/server_logs.jsonl', help='Log file to analyze')
    parser.add_argument('--recent', type=int, metavar='N', help='Show last N log entries in readable format')
    parser.add_argument('--errors-only', action='store_true', help='Show only errors and warnings')
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        
    analyzer = LogAnalyzer()
    
    if args.recent:
        analyzer.show_recent_logs(Path(args.log_file), args.recent, args.errors_only)
    else:
        analysis = analyzer.analyze_logs_from_file(Path(args.log_file))
        print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    main()
