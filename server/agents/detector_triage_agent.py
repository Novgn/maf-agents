"""
Detector Triage Agent using Microsoft Agent Framework.

This module implements a conversational agent that helps users understand
and articulate what type of detector they want to create through guided
conversation and requirement gathering.
"""

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

    def __init__(self):
        """Initialize the Detector Triage Agent using Azure OpenAI."""
        chat_client = AzureOpenAIChatClient()

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
        print("\n")
        triage_prompt = "Hello! I'm here to help you create a new ETW detector. Tell me - what security concern or system behavior would you like to detect?"

        conversation_history = []
        requirements_complete = False
        turn_count = 0

        # Initial agent response
        response = await self.agent.run(triage_prompt)
        print(f"🤖 Agent: {response.text}\n")
        conversation_history.append({"role": "assistant", "content": response.text})

        # Conversation loop
        detector_summary = ""
        while not requirements_complete and turn_count < max_turns:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

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

                # Confirm
                confirm = input("\nIs this correct? (yes/no): ").strip().lower()
                if confirm in ['y', 'yes']:
                    requirements_complete = True
                else:
                    refine_msg = "Let's refine the requirements. What would you like to adjust?"
                    print(f"\n🤖 Agent: {refine_msg}\n")
                    conversation_history.append({"role": "assistant", "content": refine_msg})
                    # Continue the loop to get user refinements
            else:
                # Continue conversation - agent maintains context, just pass new user input
                response = await self.agent.run(user_input)
                print(f"\n🤖 Agent: {response.text}\n")
                conversation_history.append({"role": "assistant", "content": response.text})

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


async def create_detector_triage_agent() -> DetectorTriageAgent:
    """
    Factory function to create a Detector Triage Agent.

    Returns:
        DetectorTriageAgent instance configured with Azure OpenAI
    """
    return DetectorTriageAgent()
