import google.generativeai as genai
import json
import logging
from typing import Dict, List, Any
from src.utils.config import Config
from src.utils.logger import logger

class LLMClient:
    """Client for interacting with the Gemini API."""

    def __init__(self):
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.model = None

    async def plan_action(self, goal: str, history: List[Dict], tools: Dict[str, str]) -> Dict[str, Any]:
        """
        Generates the next action based on the goal and history.
        
        Returns:
            A dictionary containing the action:
            {
                "action": "tool_use" | "finish" | "fail",
                "tool_name": "name_of_tool" (if action is tool_use),
                "tool_args": { ... } (if action is tool_use),
                "reasoning": "Silent reasoning string"
            }
        """
        if not self.model:
             return {"action": "fail", "reasoning": "LLM client not initialized."}

        # Construct the prompt
        prompt = self._construct_prompt(goal, history, tools)
        
        try:
            # Generate content
            response = await self.model.generate_content_async(prompt)
            text = response.text
            
            # Parse JSON from response (expecting markdown code block or raw json)
            # Simple heuristic cleaning
            clean_text = text.replace("```json", "").replace("```", "").strip()
            
            try:
                action_plan = json.loads(clean_text)
                return action_plan
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response: {text}")
                return {"action": "fail", "reasoning": "Invalid JSON response from LLM."}

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {"action": "fail", "reasoning": str(e)}

    def _construct_prompt(self, goal: str, history: List[Dict], tools: Dict[str, str]) -> str:
        tool_desc = "\n".join([f"- {name}: {desc}" for name, desc in tools.items()])
        
        history_str = ""
        for entry in history[-5:]: # Keep context manageable
            history_str += f"- {entry.get('action')} -> {entry.get('result')} (Status: {entry.get('status')})\n"

        prompt = f"""
You are an autonomous agent. Your goal is: "{goal}"

Available Tools:
{tool_desc}

Recent History:
{history_str}

Decide the next step. You must respond with a valid JSON object only. No other text.
The JSON schema is:
{{
  "action": "tool_use" or "finish" or "fail",
  "tool_name": "name_of_tool_to_use",
  "tool_args": {{ "arg_name": "arg_value" }},
  "reasoning": "Brief explanation of why this action is chosen."
}}

If the goal is achieved, set action to "finish".
If the goal is impossible, set action to "fail".
If you need to perform an action, set action to "tool_use" and specify the tool and arguments.
"""
        return prompt

# Global LLM client
llm_client = LLMClient()
