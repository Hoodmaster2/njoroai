import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from src.persistence.database import db
from src.tools.registry import registry
from src.agent.llm_client import llm_client
from src.utils.logger import logger

class AgentSignals(QObject):
    """Signals for the agent thread."""
    log_updated = pyqtSignal(dict) # Journal entry
    status_changed = pyqtSignal(str) # Status message
    confirmation_required = pyqtSignal(dict) # Confirmation details
    goal_updated = pyqtSignal(dict) # Goal status

class AgentThread(QThread):
    """
    Main agent loop running in a separate thread.
    Executes the Sense -> Plan -> Act -> Evaluate cycle.
    """
    
    def __init__(self):
        super().__init__()
        self.signals = AgentSignals()
        self.is_running = False
        self._loop = None

    def run(self):
        """Entry point for QThread."""
        self.is_running = True
        self.signals.status_changed.emit("Agent Started")
        
        # Create a new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self.agent_cycle())
        except Exception as e:
            logger.error(f"Agent loop crashed: {e}")
            self.signals.status_changed.emit(f"Error: {e}")
        finally:
            self._loop.close()
            self.is_running = False
            self.signals.status_changed.emit("Agent Stopped")

    def stop(self):
        """Stops the agent loop safely."""
        self.is_running = False

    async def agent_cycle(self):
        """Continuous agent loop."""
        while self.is_running:
            # 1. SENSE: Get active goal
            goal = self._get_active_goal()
            if not goal:
                self.signals.status_changed.emit("Idle - No Active Goal")
                await asyncio.sleep(2)
                continue

            self.signals.status_changed.emit(f"Planning for Goal: {goal['id']}")
            
            # Get recent history
            history = self._get_recent_history(goal['id'])
            
            # Get available tools
            tools = registry.get_all_tools()

            # 2. PLAN: Call LLM
            plan = await llm_client.plan_action(goal['description'], history, tools)
            
            if plan.get("action") == "finish":
                self._update_goal_status(goal['id'], "completed")
                self._log_journal(goal['id'], "Finished", "None", "Goal Completed", "success")
                self.signals.status_changed.emit("Goal Completed")
                continue # Or stop?
            
            if plan.get("action") == "fail":
                self._update_goal_status(goal['id'], "failed")
                self._log_journal(goal['id'], "Failed", "None", plan.get("reasoning", "Unknown"), "failed")
                self.signals.status_changed.emit("Goal Failed")
                continue

            # 3. ACT: Execute Tool
            if plan.get("action") == "tool_use":
                tool_name = plan.get("tool_name")
                tool_args = plan.get("tool_args", {})
                
                # Confirmation Check
                if self._requires_confirmation(tool_name):
                    approved = self._check_confirmation(goal['id'], tool_name, tool_args)
                    if not approved:
                        # Pause and wait for user
                        self.signals.status_changed.emit("Waiting for Approval")
                        self.signals.confirmation_required.emit({
                            "goal_id": goal['id'],
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "reasoning": plan.get("reasoning")
                        })
                        self.is_running = False # Stop loop to wait for user
                        break
                
                # Execute
                self.signals.status_changed.emit(f"Executing {tool_name}...")
                try:
                    result = await registry.execute(tool_name, **tool_args)
                    status = "success"
                except Exception as e:
                    result = f"Error: {e}"
                    status = "error"

                # 4. EVALUATE: Log result
                self._log_journal(goal['id'], f"Used {tool_name}", tool_name, str(result), status)
            
            # Throttle slightly
            await asyncio.sleep(1)

    def _get_active_goal(self):
        return db.fetch_one("SELECT * FROM goals WHERE status = 'active' ORDER BY created_at DESC LIMIT 1")

    def _get_recent_history(self, goal_id):
        rows = db.fetch_all("SELECT * FROM journal WHERE goal_id = ? ORDER BY timestamp DESC LIMIT 10", (goal_id,))
        # Convert to list of dicts and reverse to chronological order
        history = [dict(row) for row in rows]
        return history[::-1]

    def _update_goal_status(self, goal_id, status):
        db.execute_query("UPDATE goals SET status = ? WHERE id = ?", (status, goal_id))
        self.signals.goal_updated.emit({"id": goal_id, "status": status})

    def _log_journal(self, goal_id, action, tool_used, result, status):
        db.execute_query(
            "INSERT INTO journal (goal_id, action, tool_used, result, status) VALUES (?, ?, ?, ?, ?)",
            (goal_id, action, tool_used, str(result), status)
        )
        # Emit signal for UI update
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": action,
            "tool": tool_used,
            "result": str(result)[:100] + "..." if len(str(result)) > 100 else str(result),
            "status": status
        }
        self.signals.log_updated.emit(entry)

    def _requires_confirmation(self, tool_name):
        # All tools except read-only ones require confirmation for safety in this version
        # Or maybe just high-risk ones. Let's say all write/exec tools.
        safe_tools = ["read_file", "list_files", "web_get"]
        return tool_name not in safe_tools

    def _check_confirmation(self, goal_id, tool_name, tool_args):
        # Generate hash
        action_desc = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
        action_hash = hashlib.sha256(action_desc.encode()).hexdigest()
        
        # Check DB
        row = db.fetch_one("SELECT approved, expiry FROM confirmations WHERE action_hash = ?", (action_hash,))
        
        if row:
            if row['approved']:
                # Check expiry (if we implement expiry logic)
                # For now, assume permanent until restart if persisted? 
                # Prompt says "confirmation state persisting across application restarts"
                # But also "expiry DATETIME". 
                expiry = datetime.strptime(row['expiry'], "%Y-%m-%d %H:%M:%S") if row['expiry'] else None
                if expiry and datetime.now() > expiry:
                    return False
                return True
            else:
                return False # Explicitly rejected previously
        
        return False # Not found
