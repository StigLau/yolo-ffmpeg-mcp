"""Process monitoring tools - timeout management and zombie process detection."""
import json
import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..server_deps import timing_decorator

logger = logging.getLogger(__name__)


def register(mcp, deps):
    file_manager = deps.file_manager
    timeout_manager = deps.timeout_manager
    config = deps.config

    # Import processing time utilities
    try:
        from ..timeout_manager import ProcessingTimeEstimator, calculate_operation_timeout
    except ImportError:
        from timeout_manager import ProcessingTimeEstimator, calculate_operation_timeout

    @mcp.tool()
    @timing_decorator
    async def estimate_processing_time(
        description: str,
        execution_mode: str = "full",
        quality: str = "standard",
        custom_resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Predict operation duration before execution.

        Args:
            description: Natural language description of desired video
            execution_mode: "full", "plan_only", or "preview"
            quality: "draft", "standard", or "high"
            custom_resolution: Override resolution
        """
        try:
            estimation = ProcessingTimeEstimator.estimate_processing_time(
                description, execution_mode, quality, custom_resolution
            )

            timeout_recommendation = calculate_operation_timeout(
                description,
                execution_mode=execution_mode,
                quality=quality,
                custom_resolution=custom_resolution
            )

            estimation["timeout_recommendation"] = timeout_recommendation
            estimation["timeout_minutes"] = timeout_recommendation / 60

            return {"success": True, **estimation}

        except Exception as e:
            return {"success": False, "error": f"Failed to estimate processing time: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def get_operation_status(operation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get real-time status of running operations.

        Args:
            operation_id: Specific operation to check (optional, shows all if not provided)
        """
        try:
            if operation_id:
                status = timeout_manager.get_operation_status(operation_id)
                return {"success": True, "operation_id": operation_id, "status": status, "found": status is not None}
            else:
                active_operations = timeout_manager.get_active_operations()
                return {
                    "success": True,
                    "active_operations": active_operations,
                    "active_count": len(active_operations),
                    "system_health": "healthy" if len(active_operations) < 3 else "busy"
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to get operation status: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def scan_zombie_processes() -> Dict[str, Any]:
        """Detect potential zombie processes from video operations."""
        try:
            import getpass

            ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)

            if ps_result.returncode != 0:
                return {"success": False, "error": "Failed to get process list"}

            lines = ps_result.stdout.strip().split('\n')[1:]

            python_spawn_processes = []
            ffmpeg_processes = []
            video_related_processes = []
            suspicious_pids = []

            current_user = getpass.getuser()

            for line in lines:
                try:
                    parts = line.split(None, 10)
                    if len(parts) < 11:
                        continue

                    user, pid, cpu_pct, mem_pct, vsz, rss, tty, stat, started, time_used, command = parts

                    if user != current_user:
                        continue

                    pid = int(pid)
                    cpu_pct = float(cpu_pct)

                    process_age_hours = None
                    try:
                        if ':' in started:
                            process_age_hours = 0
                        elif len(started) == 6:
                            day = int(started[:2])
                            month_str = started[2:5]
                            month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                       'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                            if month_str in month_map:
                                year = int('20' + started[5:])
                                process_date = datetime(year, month_map[month_str], day)
                                age_delta = datetime.now() - process_date
                                process_age_hours = age_delta.total_seconds() / 3600
                    except Exception:
                        process_age_hours = None

                    command_lower = command.lower()

                    if 'python' in command_lower and 'spawn_main' in command_lower:
                        process_info = {
                            'pid': pid, 'cpu_percent': cpu_pct, 'memory_percent': float(mem_pct),
                            'started': started, 'age_hours': process_age_hours,
                            'time_used': time_used, 'command': command, 'status': stat
                        }
                        python_spawn_processes.append(process_info)
                        if (process_age_hours and process_age_hours > 24) or cpu_pct > 5.0:
                            suspicious_pids.append({
                                'pid': pid,
                                'reason': f'Long-running spawn process ({process_age_hours:.1f}h old, {cpu_pct}% CPU)' if process_age_hours else f'High CPU spawn ({cpu_pct}%)',
                                'priority': 'high' if process_age_hours and process_age_hours > 48 else 'medium',
                                'safety_level': 'safe_to_kill',
                                'type': 'python_spawn_zombie'
                            })

                    elif 'ffmpeg' in command_lower:
                        process_info = {
                            'pid': pid, 'cpu_percent': cpu_pct, 'memory_percent': float(mem_pct),
                            'started': started, 'age_hours': process_age_hours,
                            'time_used': time_used,
                            'command': command[:100] + '...' if len(command) > 100 else command,
                            'status': stat
                        }
                        ffmpeg_processes.append(process_info)
                        if process_age_hours and process_age_hours > 2:
                            suspicious_pids.append({
                                'pid': pid, 'reason': f'Long-running FFMPEG process ({process_age_hours:.1f}h)',
                                'priority': 'high', 'safety_level': 'safe_to_kill', 'type': 'ffmpeg_hung'
                            })

                    elif any(keyword in command_lower for keyword in ['uvicorn', 'mcp', 'video', 'audio', 'youtube']):
                        safety_level = 'safe_to_kill'
                        process_type = 'unknown'
                        if 'uvicorn' in command_lower and ('mcp' in command_lower or ':809' in command_lower):
                            process_type = 'mcp_server'
                            safety_level = 'do_not_kill'
                        elif 'uvicorn' in command_lower:
                            process_type = 'web_server'
                            safety_level = 'caution'
                        elif any(k in command_lower for k in ['video', 'audio', 'youtube']):
                            process_type = 'media_processing'

                        process_info = {
                            'pid': pid, 'cpu_percent': cpu_pct, 'memory_percent': float(mem_pct),
                            'started': started, 'age_hours': process_age_hours,
                            'time_used': time_used,
                            'command': command[:100] + '...' if len(command) > 100 else command,
                            'status': stat, 'type': process_type, 'safety_level': safety_level
                        }
                        video_related_processes.append(process_info)

                        if (safety_level == 'safe_to_kill' and process_age_hours and process_age_hours > 4):
                            suspicious_pids.append({
                                'pid': pid, 'reason': f'Long-running {process_type} ({process_age_hours:.1f}h)',
                                'priority': 'medium', 'safety_level': safety_level, 'type': process_type
                            })

                except (ValueError, IndexError):
                    continue

            suspicious_count = len(suspicious_pids)
            if suspicious_count > 5:
                health = "critical"
            elif suspicious_count > 2:
                health = "warning"
            elif len(python_spawn_processes) > 10:
                health = "concerning"
            else:
                health = "healthy"

            return {
                "success": True,
                "python_spawn_processes": python_spawn_processes,
                "ffmpeg_processes": ffmpeg_processes,
                "video_related_processes": video_related_processes,
                "suspicious_processes": suspicious_pids,
                "summary": {
                    "total_spawn_processes": len(python_spawn_processes),
                    "total_ffmpeg_processes": len(ffmpeg_processes),
                    "total_video_processes": len(video_related_processes),
                    "suspicious_count": suspicious_count,
                    "system_health": health
                },
                "recommendations": {
                    "safe_to_kill": {
                        "processes": [p for p in suspicious_pids if p.get('safety_level') == 'safe_to_kill'],
                        "kill_commands": [f"kill {p['pid']}" for p in suspicious_pids if p.get('safety_level') == 'safe_to_kill']
                    },
                    "caution_required": {
                        "processes": [p for p in suspicious_pids if p.get('safety_level') == 'caution'],
                        "warning": "Verify they're not needed before killing."
                    },
                    "do_not_kill": {
                        "processes": [p for p in suspicious_pids if p.get('safety_level') == 'do_not_kill'],
                        "warning": "Critical services - DO NOT KILL"
                    }
                }
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Process scan timed out"}
        except Exception as e:
            return {"success": False, "error": f"Failed to scan processes: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def kill_zombie_processes(pids: List[int], force: bool = False) -> Dict[str, Any]:
        """Kill specified zombie processes with safety checks.

        Args:
            pids: List of process IDs to kill
            force: Use SIGKILL (-9) instead of SIGTERM (default: False)
        """
        try:
            if not pids:
                return {"success": False, "error": "No PIDs provided to kill"}

            scan_result = await scan_zombie_processes()
            if not scan_result.get('success'):
                return {"success": False, "error": "Could not scan processes for safety verification"}

            safe_to_kill_pids = set()
            protected_pids = set()
            process_info = {}

            for proc_list, default_safety in [
                (scan_result.get('python_spawn_processes', []), 'safe_to_kill'),
                (scan_result.get('ffmpeg_processes', []), 'safe_to_kill'),
                (scan_result.get('video_related_processes', []), None)
            ]:
                for proc in proc_list:
                    p = int(proc['pid'])
                    safety = proc.get('safety_level', default_safety)
                    process_info[p] = {'type': proc.get('type', 'unknown'), 'safety_level': safety, 'command': proc.get('command', '')}
                    if safety == 'safe_to_kill':
                        safe_to_kill_pids.add(p)
                    elif safety in ['do_not_kill', 'caution']:
                        protected_pids.add(p)

            kill_results = []
            safety_violations = []

            for pid in pids:
                if pid in protected_pids:
                    safety_violations.append({'pid': pid, 'reason': f'Protected: {process_info[pid]["type"]}'})
                elif pid not in safe_to_kill_pids:
                    check = subprocess.run(['ps', '-p', str(pid)], capture_output=True, text=True, timeout=5)
                    if check.returncode != 0:
                        kill_results.append({'pid': pid, 'status': 'already_dead'})
                    else:
                        safety_violations.append({'pid': pid, 'reason': 'Not classified as safe to kill'})
                else:
                    try:
                        signal_type = '-9' if force else '-15'
                        result = subprocess.run(['kill', signal_type, str(pid)], capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            kill_results.append({'pid': pid, 'status': 'killed', 'signal': 'SIGKILL' if force else 'SIGTERM'})
                        else:
                            kill_results.append({'pid': pid, 'status': 'failed', 'error': result.stderr.strip()})
                    except Exception as e:
                        kill_results.append({'pid': pid, 'status': 'error', 'error': str(e)})

            return {
                "success": len(safety_violations) == 0,
                "kill_results": kill_results,
                "safety_violations": safety_violations,
                "summary": {
                    "requested_pids": len(pids),
                    "successful_kills": len([r for r in kill_results if r['status'] == 'killed']),
                    "blocked_for_safety": len(safety_violations),
                    "signal_used": 'SIGKILL (-9)' if force else 'SIGTERM (-15)'
                }
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to kill processes: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def kill_all_safe_zombies(force: bool = False) -> Dict[str, Any]:
        """Automatically kill all safe zombie processes.

        Args:
            force: Use SIGKILL (-9) instead of SIGTERM (default: False)
        """
        try:
            scan_data = await scan_zombie_processes()
            if not scan_data.get('success'):
                return {"success": False, "error": "Could not scan for zombie processes"}

            safe_processes = scan_data.get('recommendations', {}).get('safe_to_kill', {}).get('processes', [])
            safe_pids = [int(p['pid']) for p in safe_processes]

            if not safe_pids:
                return {
                    "success": True,
                    "message": "No safe zombie processes found to kill",
                    "scan_summary": scan_data.get('summary', {})
                }

            kill_data = await kill_zombie_processes(safe_pids, force)

            return {
                "success": kill_data.get('success', False),
                "scan_summary": scan_data.get('summary', {}),
                "kill_summary": kill_data.get('summary', {}),
                "kill_results": kill_data.get('kill_results', []),
                "processes_found": len(safe_pids)
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to auto-kill zombies: {str(e)}"}

    @mcp.tool()
    async def cleanup_partial_operations() -> Dict[str, Any]:
        """Clean up partial operations and hung processes."""
        try:
            result = await timeout_manager.cleanup_partial_operations()
            temp_cleanup = await mcp.call_tool('cleanup_temp_files', {})
            process_scan = await scan_zombie_processes()

            return {
                "success": True,
                "operation_cleanup": result,
                "temp_file_cleanup": temp_cleanup,
                "process_scan": process_scan
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to cleanup partial operations: {str(e)}"}
