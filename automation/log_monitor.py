#!/usr/bin/env python3
"""
Server Log Monitor for Upscale Bot
──────────────────────────────────
Fetches logs from remote server using credentials from .env
Runs continuously in background for real-time monitoring.
"""

import asyncio
import logging
import json
import os
import subprocess
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import time
import re
from dotenv import load_dotenv
import signal
import sys

# Load environment variables
load_dotenv()

@dataclass
class LogEntry:
    timestamp: str
    level: str
    service: str
    message: str
    process_id: str = ""
    raw_line: str = ""

class RemoteLogMonitor:
    def __init__(self):
        # Load from environment variables
        self.server_host = os.getenv('BOT_SERVER')
        self.server_user = os.getenv('BOT_SERVER_USER') 
        self.server_password = os.getenv('BOT_SERVER_PASSWORD')
        self.service_name = "upscale-bot.service"
        
        # Validate required environment variables
        if not all([self.server_host, self.server_user]):
            raise ValueError("BOT_SERVER and BOT_SERVER_USER must be set in .env file")
        
        # File paths (using logs directory)
        self.log_file = Path("logs/server_logs.jsonl")
        self.status_file = Path("logs/log_monitor_status.json")
        self.pid_file = Path("logs/log_monitor.pid")
        self.running = False
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/log_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.pid_file.exists():
            self.pid_file.unlink()
        sys.exit(0)

    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse a systemd journal log line into a LogEntry."""
        # Handle different log formats from your server logs
        patterns = [
            # Your server format: Jun 20 18:04:30 telegrambotsfarm python[95498]: 2025-06-20 18:04:30  ERROR     root │ message
            r'(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \w+ python\[(\d+)\]: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+\w+\s+│\s+(.+)',
            # Standard systemd format
            r'(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \w+ \w+\[(\d+)\]: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)',
            # ISO format
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2}) \w+ \w+\[(\d+)\]: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)',
            # Simple format
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()
                if len(groups) == 5:  # Pattern with PID
                    timestamp, pid, log_time, level, message = groups
                    return LogEntry(
                        timestamp=log_time,
                        level=level,
                        service=self.service_name,
                        message=message,
                        process_id=pid,
                        raw_line=line
                    )
                elif len(groups) == 3:  # Simple pattern
                    timestamp, level, message = groups
                    return LogEntry(
                        timestamp=timestamp,
                        level=level,
                        service=self.service_name,
                        message=message,
                        raw_line=line
                    )
        
        # If no pattern matches, create a generic entry
        return LogEntry(
            timestamp=datetime.datetime.now().isoformat(),
            level="INFO",
            service=self.service_name,
            message=line.strip(),
            raw_line=line
        )

    def build_ssh_command(self, remote_command: str) -> List[str]:
        """Build SSH command with password handling if needed."""
        base_cmd = ["ssh"]
        
        # Add SSH options for better automation
        base_cmd.extend([
            "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=no"
        ])
        
        # If password is provided, use sshpass
        if self.server_password:
            base_cmd = ["sshpass", "-p", self.server_password] + base_cmd
        
        base_cmd.append(f"{self.server_user}@{self.server_host}")
        base_cmd.append(remote_command)
        
        return base_cmd

    async def test_connection(self) -> bool:
        """Test SSH connection to the server."""
        try:
            cmd = self.build_ssh_command("echo 'Connection test successful'")
            self.logger.debug(f"Testing SSH with command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.logger.info("✅ SSH connection successful")
                self.logger.debug(f"SSH test output: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"❌ SSH connection failed (exit code: {result.returncode})")
                self.logger.error(f"STDERR: {result.stderr}")
                if result.stdout:
                    self.logger.debug(f"STDOUT: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ SSH connection timeout (>15 seconds)")
            return False
        except FileNotFoundError as e:
            if 'sshpass' in str(e):
                self.logger.warning("⚠️  sshpass not found. Install with: brew install hudochenkov/sshpass/sshpass")
                self.logger.info("Or use SSH keys instead of password authentication")
            else:
                self.logger.error(f"❌ Command not found: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ SSH connection error: {e}")
            if hasattr(e, '__traceback__'):
                import traceback
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return False

    async def fetch_logs(self, lines: int = 100) -> List[LogEntry]:
        """Fetch recent logs from the remote server."""
        try:
            remote_cmd = f"sudo journalctl -u {self.service_name} -n {lines} --no-pager -o short-iso"
            cmd = self.build_ssh_command(remote_cmd)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to fetch logs: {result.stderr}")
                return []
            
            logs = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    entry = self.parse_log_line(line)
                    if entry:
                        logs.append(entry)
            
            return logs
            
        except subprocess.TimeoutExpired:
            self.logger.error("SSH command timed out")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching logs: {e}")
            return []

    async def stream_logs_continuously(self):
        """Stream logs in real-time and store them locally."""
        self.logger.info(f"🚀 Starting continuous log stream from {self.server_host}")
        self.running = True
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        remote_cmd = f"sudo journalctl -u {self.service_name} -f --no-pager -o short-iso"
        
        while self.running:
            try:
                cmd = self.build_ssh_command(remote_cmd)
                
                self.logger.info("🔗 Connecting to server for log streaming...")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                self.logger.info("✅ Connected! Streaming logs...")
                
                while self.running and process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        entry = self.parse_log_line(line)
                        if entry:
                            await self.store_log_entry(entry)
                            # Show important logs in console
                            if entry.level in ['ERROR', 'WARNING']:
                                self.logger.info(f"📋 [{entry.level}] {entry.message[:100]}...")
                    
                    await asyncio.sleep(0.1)
                
                if process.poll() is None:
                    process.terminate()
                    
            except KeyboardInterrupt:
                self.logger.info("❌ Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error during streaming: {e}")
                self.logger.info("🔄 Reconnecting in 10 seconds...")
                await asyncio.sleep(10)
                
        self.running = False
        if self.pid_file.exists():
            self.pid_file.unlink()

    async def store_log_entry(self, entry: LogEntry):
        """Store a log entry to the local file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(asdict(entry)) + '\n')
            
            # Update status
            status = {
                "last_update": datetime.datetime.now().isoformat(),
                "last_entry": asdict(entry),
                "running": self.running,
                "server": self.server_host,
                "service": self.service_name
            }
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error storing log entry: {e}")

    def get_recent_logs(self, minutes: int = 10, level_filter: str = None) -> List[LogEntry]:
        """Get recent logs from the local store."""
        if not self.log_file.exists():
            return []
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        recent_logs = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry_dict = json.loads(line.strip())
                        entry = LogEntry(**entry_dict)
                        
                        # Parse timestamp
                        try:
                            entry_time = datetime.datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                            if entry_time.replace(tzinfo=None) > cutoff_time:
                                if level_filter is None or entry.level.upper() == level_filter.upper():
                                    recent_logs.append(entry)
                        except ValueError:
                            # If timestamp parsing fails, include it anyway
                            if level_filter is None or entry.level.upper() == level_filter.upper():
                                recent_logs.append(entry)
                                
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error reading logs: {e}")
            
        return recent_logs[-100:]  # Return last 100 entries

    def is_running(self) -> bool:
        """Check if the monitor is currently running."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # Process doesn't exist, clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False

async def main():
    parser = argparse.ArgumentParser(description='Monitor upscale bot logs')
    parser.add_argument('--mode', choices=['stream', 'fetch', 'status', 'stop'], default='fetch',
                        help='Mode: stream (continuous), fetch (one-time), status (check), stop (shutdown)')
    parser.add_argument('--lines', type=int, default=100, help='Number of lines to fetch')
    parser.add_argument('--background', action='store_true', help='Run in background')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    
    try:
        monitor = RemoteLogMonitor()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please ensure BOT_SERVER and BOT_SERVER_USER are set in your .env file")
        return
    
    if args.mode == 'status':
        if monitor.is_running():
            print("✅ Log monitor is running")
            if monitor.status_file.exists():
                with open(monitor.status_file, 'r') as f:
                    status = json.load(f)
                print(f"📡 Server: {status.get('server')}")
                print(f"🔄 Last update: {status.get('last_update')}")
        else:
            print("❌ Log monitor is not running")
    
    elif args.mode == 'stop':
        if monitor.is_running():
            with open(monitor.pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print("🛑 Stop signal sent to log monitor")
        else:
            print("❌ Log monitor is not running")
    
    elif args.mode == 'stream':
        if monitor.is_running():
            print("⚠️  Log monitor is already running")
            return
        
        # Test connection first
        if not await monitor.test_connection():
            print("❌ Cannot connect to server. Please check your credentials.")
            return
        
        if args.background:
            print("🔄 Starting log monitor in background...")
            print("Use --mode status to check status")
            print("Use --mode stop to stop the monitor")
        
        await monitor.stream_logs_continuously()
    
    elif args.mode == 'fetch':
        if not await monitor.test_connection():
            print("❌ Cannot connect to server")
            return
            
        logs = await monitor.fetch_logs(args.lines)
        print(f"📋 Fetched {len(logs)} log entries:")
        for log in logs[-20:]:  # Show last 20
            print(f"[{log.timestamp}] {log.level}: {log.message}")

if __name__ == "__main__":
    asyncio.run(main())