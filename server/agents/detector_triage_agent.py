"""
Detector Triage Agent using Microsoft Agent Framework.

This module implements a conversational agent that helps users understand
and articulate what type of detector they want to create through guided
conversation and requirement gathering.
"""

import asyncio
from typing import Callable, Any
from agent_framework import ChatAgent, ChatMessage
from agent_framework.azure import AzureOpenAIChatClient

from shared.models import DetectorTriageData


class DetectorTriageAgent:
    """
    Detector Triage & Ideation Agent using Microsoft Agent Framework.

    This agent provides a conversational interface for understanding what
    security behavior the user wants to detect before diving into technical
    implementation details.
    """

    def __init__(self, input_queue: asyncio.Queue = None, broadcast_func: Callable = None, workflow_id: str = None):
        """
        Initialize the Detector Triage Agent using Azure OpenAI.

        Args:
            input_queue: Asyncio queue for receiving user input from WebSocket
            broadcast_func: Function to broadcast agent messages via WebSocket
            workflow_id: Workflow ID for message context
        """
        chat_client = AzureOpenAIChatClient()

        self.input_queue = input_queue
        self.broadcast_func = broadcast_func
        self.workflow_id = workflow_id

        self.agent = ChatAgent(
            chat_client=chat_client,
            name="Detector Triage Agent",
            instructions="""You are a security detection expert helping users create ETW (Event Tracing for Windows) detectors.

Your role is to have a natural conversation to understand:
1. **What they want to detect**: What security threat, suspicious behavior, or system event are they concerned about?
2. **The use case**: Why is this detection important? What's the business/security goal?
3. **Expected behavior**: What specific actions, events, or patterns should trigger this detector?
4. **Known details**: Do they already know the ETW provider, event IDs, or specific fields?
5. **Detector characteristics**:
   - Severity (High/Medium/Low)
   - Frequency (How often might this trigger?)
   - False positive tolerance

Ask clarifying questions to gather complete requirements. Be conversational and helpful.

Once you have enough information to create a clear detector specification, summarize what you've learned and confirm with the user.

Examples of good detector ideas:
- "Detect when PowerShell is executed with suspicious command-line arguments"
- "Alert on failed authentication attempts from the same user exceeding threshold"
- "Monitor for registry modifications to Windows Defender settings"
- "Detect unusual process creation chains (e.g., Office spawning cmd.exe)"
"""
        )

    async def gather_requirements(
        self,
        max_turns: int = 10
    ) -> DetectorTriageData:
        """
        Gather detector requirements through conversational interaction.

        Args:
            max_turns: Maximum number of conversation turns (default: 10)

        Returns:
            DetectorTriageData containing the gathered requirements and summary

        Raises:
            ValueError: If requirements gathering fails or is incomplete
        """
        print("\n✓ Starting conversational triage with WebSocket support")

        triage_prompt = "Hello! I'm here to help you create a new ETW detector. Tell me - what security concern or system behavior would you like to detect?"

        conversation_history = []
        requirements_complete = False
        turn_count = 0

        # Initial agent response
        response = await self.agent.run(triage_prompt)
        agent_message = response.text
        print(f"🤖 Agent: {agent_message}\n")
        conversation_history.append({"role": "assistant", "content": agent_message})

        # Broadcast agent message via WebSocket
        if self.broadcast_func and self.workflow_id:
            await self.broadcast_func(self.workflow_id, {
                "type": "agent_message",
                "message": agent_message,
                "step_number": 1,
            })

        # Conversation loop
        detector_summary = ""
        while not requirements_complete and turn_count < max_turns:
            # Get user input from queue (WebSocket)
            try:
                user_input = await asyncio.wait_for(self.input_queue.get(), timeout=300.0)  # 5 minute timeout
                print(f"You: {user_input}")
            except asyncio.TimeoutError:
                print("⚠️  Timeout waiting for user input")
                break

            if not user_input or not user_input.strip():
                continue

            user_input = user_input.strip()
            conversation_history.append({"role": "user", "content": user_input})

            # Check if user wants to proceed or is done
            if user_input.lower() in ['done', 'proceed', 'yes', 'ready', 'continue']:
                # Ask agent to summarize - agent maintains conversation context internally
                summary_prompt = "Based on our conversation, please provide a concise summary of the detector we're creating. Include: 1) What we're detecting, 2) Why it's important, 3) Expected trigger conditions, 4) Any technical details mentioned."
                conversation_history.append({"role": "user", "content": summary_prompt})

                # Get summary - just pass the new prompt, agent remembers context
                summary_response = await self.agent.run(summary_prompt)
                detector_summary = summary_response.text
                conversation_history.append({"role": "assistant", "content": detector_summary})

                print(f"\n🤖 Agent Summary:")
                print("="*70)
                print(f"{detector_summary}")
                print("="*70)

                # Broadcast summary
                if self.broadcast_func and self.workflow_id:
                    await self.broadcast_func(self.workflow_id, {
                        "type": "agent_message",
                        "message": detector_summary,
                        "step_number": 1,
                    })

                # Mark as complete (no terminal confirmation needed for WebSocket mode)
                requirements_complete = True
            else:
                # Continue conversation - agent maintains context, just pass new user input
                response = await self.agent.run(user_input)
                agent_message = response.text
                print(f"\n🤖 Agent: {agent_message}\n")
                conversation_history.append({"role": "assistant", "content": agent_message})

                # Broadcast agent response
                if self.broadcast_func and self.workflow_id:
                    await self.broadcast_func(self.workflow_id, {
                        "type": "agent_message",
                        "message": agent_message,
                        "step_number": 1,
                    })

            turn_count += 1

        if not requirements_complete:
            print("\n⚠️  Maximum conversation turns reached. Using gathered information...")
            # Get final summary - agent remembers all context
            summary_prompt = "Based on our conversation so far, provide a brief summary of what we're trying to detect."
            conversation_history.append({"role": "user", "content": summary_prompt})
            summary_response = await self.agent.run(summary_prompt)
            detector_summary = summary_response.text
            conversation_history.append({"role": "assistant", "content": detector_summary})

        # Build and return triage data
        return DetectorTriageData(
            summary=detector_summary,
            conversation_history=conversation_history,
            requirements_complete=requirements_complete
        )


async def create_detector_triage_agent(
    input_queue: asyncio.Queue = None,
    broadcast_func: Callable = None,
    workflow_id: str = None
) -> DetectorTriageAgent:
    """
    Factory function to create a Detector Triage Agent.

    Args:
        input_queue: Asyncio queue for receiving user input from WebSocket
        broadcast_func: Function to broadcast agent messages via WebSocket
        workflow_id: Workflow ID for message context

    Returns:
        DetectorTriageAgent instance configured with Azure OpenAI and WebSocket support
    """
    return DetectorTriageAgent(input_queue=input_queue, broadcast_func=broadcast_func, workflow_id=workflow_id)
