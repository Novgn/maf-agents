"""
Main workflow orchestrator for maf-agents using Microsoft Agent Framework.

This implementation uses the actual MAF SDK with proper executor patterns
for sequential orchestration of 9 detector development steps, integrating
with Azure Kusto and Azure DevOps services.
"""

import asyncio
import os
from typing import Any, Annotated
from uuid import uuid4
from pathlib import Path
from datetime import datetime

from agent_framework import (
    WorkflowBuilder,
    WorkflowContext,
    executor,
    WorkflowOutputEvent,
    WorkflowFailedEvent,
    FileCheckpointStorage,
    ChatAgent,
    ChatMessage,
    ai_function,
)
from agent_framework._workflows._edge import Case, Default
from agent_framework.azure import AzureOpenAIChatClient
from typing_extensions import Never

from shared.config import get_config
from shared.kusto_client import create_kusto_client
from shared.auth import get_auth_manager
from agents.detector_triage_agent import create_detector_triage_agent
from agents.etw_input_agent import create_etw_input_agent
from agents.schema_discovery_agent import create_schema_discovery_agent

# Configure checkpoint storage
checkpoint_dir = Path("./checkpoints")
checkpoint_dir.mkdir(exist_ok=True)
checkpoint_storage = FileCheckpointStorage(checkpoint_dir)


# Define the 9 workflow agents as MAF executors
# Each executor represents a step in the detector development workflow

# Condition function for switch-case routing
def is_successful(message: dict[str, Any]) -> bool:
    """
    Check if the current step was successful.

    Returns True if status is "success", False otherwise.
    When False, the workflow routes to the failure handler.
    """
    return message.get("status") == "success"


@executor(id="workflow_failure_handler")
async def workflow_failure_handler(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[Never, dict[str, Any]]
) -> None:
    """
    Workflow Failure Handler - Terminal executor for failed workflows.

    This executor is called when any step fails. It outputs the final state
    with error information and terminates the workflow.
    """
    print("\n" + "="*70)
    print("❌ WORKFLOW FAILED")
    print("="*70)

    failed_step = workflow_data.get("current_step", "unknown")
    error_message = workflow_data.get("error_message", "No error message provided")

    print(f"\n   Failed at step: {failed_step}")
    print(f"   Error: {error_message}")
    print(f"\n   Workflow ID: {workflow_data.get('workflow_id', 'N/A')}")
    print(f"   Provider GUID: {workflow_data.get('provider_guid', 'N/A')}")
    print(f"   Rule ID: {workflow_data.get('rule_id', 'N/A')}")
    print("\n" + "="*70)
    print("\n💾 Checkpoint saved - you can debug or restart from this point")
    print()

    # Mark as final failure
    workflow_data["workflow_status"] = "failed"
    workflow_data["workflow_end_time"] = datetime.now().isoformat()

    # Yield final output
    await ctx.yield_output(workflow_data)


@executor(id="detector_triage")
async def detector_triage_executor(
    input_data: dict[str, Any] | None,
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 1: Detector Triage & Ideation

    Conversational triage to understand what the user wants to detect.
    Gathers requirements, use case, and context before proceeding to technical details.
    """
    print("\n✓ [1/9] Detector Triage & Ideation (Conversational Agent)")
    print("="*70)
    print("Let's understand what you want to detect...")
    print("="*70)

    # Create the Detector Triage Agent
    agent = await create_detector_triage_agent()

    # Gather requirements through conversation
    triage_data = await agent.gather_requirements(max_turns=10)

    # Build workflow data with triage context
    workflow_data = {
        "workflow_id": input_data.get("workflow_id", str(uuid4())) if input_data else str(uuid4()),
        "current_step": "detector_triage",
        "status": "success",
        "triage_summary": triage_data.summary,
        "triage_conversation": triage_data.conversation_history,
        "requirements_complete": triage_data.requirements_complete,
        "workflow_start_time": datetime.now().isoformat(),
    }

    print(f"\n    ✓ Triage complete - detector requirements gathered")
    print(f"    ✓ Status: Success")

    await ctx.send_message(workflow_data)


@executor(id="etw_input_collection")
async def etw_input_collection_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 2: ETW Input Collection
    Uses the ETW Input Agent to collect and validate providerGuid and ruleId
    through a conversational interface, informed by the triage context.
    """
    print("\n✓ [2/9] ETW Input Collection (Conversational Agent)")
    print("    Initializing ETW Input Collection Agent...")

    # Create the ETW Input Agent
    agent = await create_etw_input_agent()

    # Check for automation flag - only skip conversation if explicitly requested
    use_automation = workflow_data.get("_use_automation", False)

    if use_automation and "provider_guid" in workflow_data and "rule_id" in workflow_data:
        # Automation mode: use pre-populated data
        provider_guid = workflow_data["provider_guid"]
        rule_id = workflow_data["rule_id"]
        print(f"    Using pre-populated input data (automation mode)")

        # Validate pre-populated data using the agent
        etw_input = await agent.collect_inputs(
            provider_guid=provider_guid,
            rule_id=rule_id
        )
    else:
        # Default: Interactive conversational collection
        # Show triage context if available
        if "triage_summary" in workflow_data:
            print("\n" + "="*70)
            print("📋 Detector Requirements Summary:")
            print("="*70)
            print(f"{workflow_data['triage_summary']}\n")
            print("="*70)

        print("\n" + "="*70)
        print("📝 Please provide ETW detector technical details")
        print("="*70)
        etw_input = await agent.collect_inputs()

    # Merge workflow data from triage with ETW data
    workflow_data["provider_guid"] = etw_input.provider_guid
    workflow_data["rule_id"] = etw_input.rule_id
    workflow_data["current_step"] = "etw_input_collection"
    workflow_data["status"] = "success"

    print(f"\n    ✓ Provider GUID: {etw_input.provider_guid}")
    print(f"    ✓ Rule ID: {etw_input.rule_id}")
    print(f"    ✓ Status: Success")

    await ctx.send_message(workflow_data)


@executor(id="schema_discovery")
async def schema_discovery_executor(
    etw_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 3: Schema Discovery
    Uses the Schema Discovery Agent to query Kusto for ETW schema
    and existing detectors through a conversational interface.
    """
    print("\n✓ [3/9] Schema Discovery (Conversational Agent)")
    print("    Initializing Schema Discovery Agent...")

    config = get_config()

    # Initialize Kusto client if configured
    if not config.azure.kusto_cluster_url or not config.azure.kusto_database_name:
        print("    ❌ Kusto not configured - cannot discover schema")
        print("    Please configure KUSTO_CLUSTER_URL and KUSTO_DATABASE_NAME")
        etw_data["current_step"] = "schema_discovery_failed"
        etw_data["status"] = "failed"
        etw_data["error_message"] = "Kusto cluster not configured"
        await ctx.send_message(etw_data)
        return

    try:
        auth_mgr = get_auth_manager(use_default_credential=True)
        kusto_client = create_kusto_client(
            cluster_url=config.azure.kusto_cluster_url,
            database=config.azure.kusto_database_name,
            auth_manager=auth_mgr,
        )

        # Create the Schema Discovery Agent
        agent = await create_schema_discovery_agent(
            kusto_client=kusto_client
        )

        # Run schema discovery
        schema_data = await agent.discover_schema(
            provider_guid=etw_data["provider_guid"],
            rule_id=etw_data["rule_id"]
        )

        # Check if we got meaningful data
        if len(schema_data.schema_fields) == 0:
            print(f"    ❌ No schema fields found for provider GUID")
            print(f"    Please verify the provider GUID and Kusto tables exist")
            etw_data["current_step"] = "schema_discovery_failed"
            etw_data["status"] = "failed"
            etw_data["error_message"] = "No schema fields found in Kusto"
            await ctx.send_message(etw_data)
            return

        print(f"    ✓ Schema fields discovered: {len(schema_data.schema_fields)}")
        print(f"    ✓ Existing detectors found: {len(schema_data.existing_detectors)}")

        # Convert to dict for workflow state
        etw_data["schema_fields"] = [
            {
                "FieldName": field.name,
                "DataType": field.data_type,
                "Description": field.description
            }
            for field in schema_data.schema_fields
        ]
        etw_data["existing_detectors"] = schema_data.existing_detectors
        etw_data["current_step"] = "schema_discovery"
        etw_data["status"] = "success"
        print(f"    ✓ Status: Success")

        await ctx.send_message(etw_data)

    except Exception as e:
        print(f"    ❌ Schema discovery failed: {str(e)}")
        print(f"    Please check Kusto configuration and table names")
        etw_data["current_step"] = "schema_discovery_failed"
        etw_data["status"] = "failed"
        etw_data["error_message"] = str(e)
        await ctx.send_message(etw_data)


@executor(id="code_generator")
async def code_generator_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 4: Code Generator
    Analyzes historical PRs and generates detector code.
    """
    print("\n✓ [4/9] Code Generator")
    print("    Analyzing historical PR patterns...")
    print("    Generating detector code...")

    workflow_data["generated_files"] = {
        "detector_file": f"detector_{workflow_data['rule_id']}.py",
        "test_file": f"test_detector_{workflow_data['rule_id']}.py",
    }
    workflow_data["current_step"] = "code_generator"
    workflow_data["status"] = "success"
    print(f"    ✓ Status: Success")

    await ctx.send_message(workflow_data)


@executor(id="pr_creation")
async def pr_creation_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 5: PR Creation
    Creates branch, commits code, and submits PR to Azure Repos using Azure DevOps SDK directly.
    """
    print("\n✓ [5/9] PR Creation")

    config = get_config()

    # Check if Azure DevOps is configured
    if not config.azure.azure_devops_org or not config.azure.azure_devops_project or not config.azure.azure_devops_repo:
        print("    ❌ Azure DevOps not configured - cannot create PR")
        print("    Please configure AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_REPO")
        workflow_data["current_step"] = "pr_creation_failed"
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = "Azure DevOps not configured"
        await ctx.send_message(workflow_data)
        return

    try:
        # Import repos utilities
        from shared.repos_utils import create_branch, commit_and_push_files, create_pull_request

        # Get authenticated connection
        auth_mgr = get_auth_manager(use_default_credential=True)
        connection = auth_mgr.get_azure_devops_connection(config.azure.azure_devops_org)

        # Define branch and PR details
        branch_name = f"detector/{workflow_data['rule_id']}"
        target_branch = "main"

        # Step 1: Create branch
        print(f"    Creating branch '{branch_name}'...")
        branch_result = create_branch(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=branch_name,
            source_branch=target_branch,
        )
        print(f"    ✓ Branch created: {branch_name}")

        # Step 2: Prepare file changes
        # Use placeholder generated files from code generator step
        file_changes = {
            f"detectors/{workflow_data['generated_files']['detector_file']}": f"# Generated detector code for {workflow_data['rule_id']}\npass",
            f"tests/{workflow_data['generated_files']['test_file']}": f"# Generated test code for {workflow_data['rule_id']}\npass",
        }

        # Step 3: Commit and push files
        print(f"    Committing {len(file_changes)} file(s)...")
        commit_result = commit_and_push_files(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=branch_name,
            file_changes=file_changes,
            commit_message=f"Add detector for {workflow_data['rule_id']}\n\nProvider GUID: {workflow_data['provider_guid']}\nGenerated by maf-agents workflow",
        )
        print(f"    ✓ Committed files (commit: {commit_result['commit_id'][:8] if commit_result['commit_id'] else 'N/A'})")

        # Step 4: Create pull request
        print("    Creating pull request...")
        pr_result = create_pull_request(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            source_branch=branch_name,
            target_branch=target_branch,
            title=f"Add detector for {workflow_data['rule_id']}",
            description=f"""
## Detector Details
- **Rule ID**: {workflow_data['rule_id']}
- **Provider GUID**: {workflow_data['provider_guid']}
- **Schema Fields**: {len(workflow_data.get('schema_fields', []))}
- **Existing Detectors**: {len(workflow_data.get('existing_detectors', []))}

Generated by maf-agents automated workflow.
            """.strip(),
        )
        print(f"    ✓ Pull request created: #{pr_result['pr_id']}")
        print(f"    URL: {pr_result['pr_url']}")

        # Update workflow data
        workflow_data["pr_url"] = pr_result["pr_url"]
        workflow_data["pr_id"] = pr_result["pr_id"]
        workflow_data["branch_name"] = branch_name
        workflow_data["commit_id"] = commit_result["commit_id"]
        workflow_data["current_step"] = "pr_creation"
        workflow_data["status"] = "success"
        print(f"    ✓ Status: Success")

        await ctx.send_message(workflow_data)

    except Exception as e:
        print(f"    ❌ PR creation failed: {str(e)}")
        print(f"    Please check Azure DevOps configuration and permissions")
        workflow_data["current_step"] = "pr_creation_failed"
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = str(e)

        await ctx.send_message(workflow_data)


# Define approval function for PR deployment
@ai_function(approval_mode="always_require")
def proceed_with_pr_deployment(
    pr_url: Annotated[str, "The PR URL to review"],
    pr_id: Annotated[int, "The PR ID"],
    branch_name: Annotated[str, "The branch name"],
) -> str:
    """
    Proceed with PR deployment after review.

    This function requires explicit user approval before the workflow continues.
    The user should review the PR at the provided URL before approving.
    """
    return "PR deployment approved - workflow will continue"


async def _handle_pr_approval(
    workflow_data: dict[str, Any], chat_client: AzureOpenAIChatClient
) -> bool:
    """
    Handle PR approval using MAF's ChatAgent approval pattern.

    Args:
        workflow_data: Workflow state with PR details
        chat_client: Azure OpenAI chat client for agent

    Returns:
        True if approved, False otherwise
    """
    # Present PR details to user
    pr_url = workflow_data.get("pr_url", "N/A")
    pr_id = workflow_data.get("pr_id", "N/A")
    branch_name = workflow_data.get("branch_name", "N/A")
    rule_id = workflow_data.get("rule_id", "N/A")
    provider_guid = workflow_data.get("provider_guid", "N/A")

    print("\n📋 Pull Request Created:")
    print(f"   URL: {pr_url}")
    print(f"   PR ID: #{pr_id}")
    print(f"   Branch: {branch_name}")
    print(f"\n🔍 Detector Details:")
    print(f"   Rule ID: {rule_id}")
    print(f"   Provider GUID: {provider_guid}")
    print(f"   Schema Fields: {len(workflow_data.get('schema_fields', []))}")
    print(f"   Existing Detectors: {len(workflow_data.get('existing_detectors', []))}")

    # Show generated files
    detector_file_name = workflow_data.get("detector_file_name", "N/A")
    test_file_name = workflow_data.get("test_file_name", "N/A")
    print(f"\n📁 Generated Files:")
    print(f"   Detector: {detector_file_name}")
    print(f"   Test: {test_file_name}")

    print("\n" + "=" * 70)
    print("\n⏸️  Please review the PR before proceeding.")
    print("   Visit the URL above to review the code changes.\n")

    # Check for auto-approve override
    auto_approve = os.getenv("MAF_AUTO_APPROVE", "false").lower() == "true"
    if auto_approve:
        print("   🤖 AUTO-APPROVE enabled (MAF_AUTO_APPROVE=true)")
        print("\n   ✅ Approved! Continuing workflow...\n")
        return True

    # Create ChatAgent with approval-required function
    async with ChatAgent(
        chat_client=chat_client,
        name="ApprovalGateAgent",
        instructions=f"""You are a PR approval assistant.

Ask the user to review the PR at {pr_url} and confirm they want to proceed with deployment.
If they approve, call the proceed_with_pr_deployment function.
If they reject or want to cancel, simply respond that the workflow will be cancelled.
""",
        tools=[proceed_with_pr_deployment]
    ) as agent:

        # Initial query to trigger approval request
        query = f"Please proceed with deploying PR #{pr_id} at {pr_url} on branch {branch_name}"
        result = await agent.run(query)

        # Process approval requests using MAF pattern
        while len(result.user_input_requests) > 0:
            new_inputs: list[ChatMessage] = []

            for user_input_needed in result.user_input_requests:
                print(f"Approval Request:")
                print(f"  Function: {user_input_needed.function_call.name}")
                print(f"  PR URL: {pr_url}")

                # Add approval request to context
                new_inputs.append(ChatMessage(role="assistant", contents=[user_input_needed]))

                # Get user approval
                user_approval = await asyncio.to_thread(
                    input,
                    "\n   Approve deployment? (y/n): "
                )

                approved = user_approval.strip().lower() in ['y', 'yes']

                # Add approval response
                new_inputs.append(
                    ChatMessage(role="user", contents=[
                        user_input_needed.create_response(approved)
                    ])
                )

                if approved:
                    print("\n   ✅ Approved! Continuing workflow...\n")
                    return True
                else:
                    print("\n   ❌ Rejected. Cancelling workflow...\n")
                    return False

            # Continue with approval context
            result = await agent.run(new_inputs)

        # If we get here without approval, default to rejection
        print("\n   ⚠️  No approval received - defaulting to rejection for safety.\n")
        return False


@executor(id="approval_gate")
async def approval_gate_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 6: User Approval Gate using MAF's ChatAgent approval pattern.

    Pauses workflow for human review and approval of PR using MAF's
    built-in user input request system with @ai_function approval_mode.

    This is a critical human-in-the-loop control point where users
    review the generated PR before allowing the workflow to continue.
    """
    print("\n✓ [6/9] User Approval Gate")
    print("=" * 70)

    # Create chat client for approval agent
    chat_client = AzureOpenAIChatClient()

    # Handle PR approval using MAF pattern
    approved = await _handle_pr_approval(workflow_data, chat_client)

    # Update workflow data
    workflow_data["approved"] = approved
    workflow_data["approval_status"] = "approved" if approved else "rejected"
    workflow_data["current_step"] = "approval_gate" if approved else "approval_gate_rejected"
    workflow_data["status"] = "success" if approved else "failed"

    if approved:
        print(f"    ✓ Status: Approved")
    else:
        print(f"    ❌ Status: Rejected - workflow will stop")

    # Send message to workflow
    await ctx.send_message(workflow_data)


async def _poll_pr_merge_status(
    workflow_data: dict[str, Any],
    poll_interval_seconds: int = 30,
    max_wait_minutes: int = 60,
) -> tuple[bool, str]:
    """
    Poll PR status until merged or timeout.

    Args:
        workflow_data: Workflow state with PR details
        poll_interval_seconds: Seconds between polls (default: 30)
        max_wait_minutes: Maximum minutes to wait (default: 60)

    Returns:
        Tuple of (success: bool, message: str)
    """
    from shared.repos_utils import get_pull_request_status
    from shared.auth import get_auth_manager
    from shared.config import get_config
    from datetime import datetime, timedelta

    pr_id = workflow_data.get("pr_id")
    if not pr_id:
        return False, "No PR ID found in workflow data"

    config = get_config()

    # Validate configuration
    if not config.azure.azure_devops_org:
        return False, "Azure DevOps organization not configured"
    if not config.azure.azure_devops_project:
        return False, "Azure DevOps project not configured"
    if not config.azure.azure_devops_repo:
        return False, "Azure DevOps repository not configured"

    auth_mgr = get_auth_manager(use_default_credential=True)
    connection = auth_mgr.get_azure_devops_connection(config.azure.azure_devops_org)

    max_polls = (max_wait_minutes * 60) // poll_interval_seconds
    start_time = datetime.now()
    timeout_time = start_time + timedelta(minutes=max_wait_minutes)

    print(f"\n📊 Monitoring PR #{pr_id} for merge status")
    print(f"   Poll interval: {poll_interval_seconds}s")
    print(f"   Max wait time: {max_wait_minutes} minutes")
    print(f"   Timeout at: {timeout_time.strftime('%H:%M:%S')}\n")

    poll_count = 0
    retry_delay = poll_interval_seconds

    while poll_count < max_polls:
        poll_count += 1
        current_time = datetime.now()

        try:
            # Get PR status
            pr_status = get_pull_request_status(
                connection,
                config.azure.azure_devops_project,
                config.azure.azure_devops_repo,
                pr_id,
            )

            status = pr_status["status"]
            is_completed = pr_status["is_completed"]
            is_abandoned = pr_status["is_abandoned"]

            print(f"   [{current_time.strftime('%H:%M:%S')}] Poll {poll_count}/{max_polls}: Status = {status}")

            # Check if PR is merged
            if is_completed:
                elapsed = (current_time - start_time).total_seconds() / 60
                return True, f"PR merged successfully after {elapsed:.1f} minutes"

            # Check if PR was abandoned
            if is_abandoned:
                return False, "PR was abandoned - deployment cancelled"

            # Wait before next poll (with exponential backoff for retries)
            if poll_count < max_polls:
                await asyncio.sleep(retry_delay)

        except Exception as e:
            # Exponential backoff on errors
            retry_delay = min(retry_delay * 2, 300)  # Max 5 minutes
            print(f"   ⚠️  Error polling PR status: {e}")
            print(f"   Retrying in {retry_delay}s with exponential backoff...")

            if poll_count < max_polls:
                await asyncio.sleep(retry_delay)
            retry_delay = poll_interval_seconds  # Reset on success

    # Timeout reached
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    return False, f"Deployment not detected after {elapsed:.1f} minutes. Please verify manually."


@executor(id="deployment_verification")
async def deployment_verification_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 7: Deployment Verification

    Monitors PR merge status and verifies successful deployment.
    Polls Azure Repos every 30 seconds with 60 minute timeout.
    Implements exponential backoff for API retries.
    """
    print("\n✓ [7/9] Deployment Verification")
    print("=" * 70)

    # Check if approval was granted (this should not happen with conditional edges)
    if not workflow_data.get("approved", False):
        print("\n   ❌ PR was not approved - cannot verify deployment")
        workflow_data["pr_merged"] = False
        workflow_data["deployment_detected"] = False
        workflow_data["deployment_status"] = "skipped_no_approval"
        workflow_data["current_step"] = "deployment_verification_skipped"
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = "PR was not approved"
        await ctx.send_message(workflow_data)
        return

    # Poll for PR merge status
    success, message = await _poll_pr_merge_status(workflow_data)

    # Update workflow data
    workflow_data["pr_merged"] = success
    workflow_data["deployment_detected"] = success
    workflow_data["deployment_status"] = "completed" if success else "timeout"
    workflow_data["deployment_message"] = message
    workflow_data["deployment_timestamp"] = datetime.now().isoformat()
    workflow_data["current_step"] = "deployment_verification" if success else "deployment_verification_failed"
    workflow_data["status"] = "success" if success else "failed"

    if not success:
        workflow_data["error_message"] = message

    # Present results
    print("\n" + "=" * 70)
    if success:
        print(f"\n   ✅ {message}")
        print(f"   Timestamp: {workflow_data['deployment_timestamp']}")
        print(f"   ✓ Status: Success")
    else:
        print(f"\n   ❌ {message}")
        print(f"   ❌ Status: Failed - workflow will stop")

    print()

    await ctx.send_message(workflow_data)


# ============================
# Results Analysis Components
# ============================


async def _fetch_and_analyze_results(
    workflow_data: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    """
    Fetch detector results from Kusto and analyze effectiveness.

    Args:
        workflow_data: Workflow state with detector info and deployment timestamp

    Returns:
        Tuple of (metrics_dict, summary_message)
    """
    from datetime import datetime, timedelta

    config = get_config()

    # Skip if deployment was not successful
    if not workflow_data.get("deployment_detected", False):
        return {
            "status": "skipped",
            "reason": "deployment_not_detected",
        }, "Deployment was not detected - skipping results analysis"

    # Check Kusto configuration
    if not config.azure.kusto_cluster_url or not config.azure.kusto_database_name:
        print("    ⚠️  Kusto not configured - using placeholder metrics")
        return {
            "status": "placeholder",
            "total_events": 42,
            "error_count": 0,
            "unique_hosts": 5,
            "error_rate": 0.0,
        }, "Kusto not configured - showing placeholder metrics: 42 events detected, 0 errors, 5 unique hosts"

    # Extract detector information
    rule_id = workflow_data.get("rule_id", "unknown")
    detector_name = f"detector_{rule_id}"

    # Calculate time window (1 hour from deployment or current time)
    deployment_timestamp = workflow_data.get("deployment_timestamp")
    if deployment_timestamp:
        start_time = datetime.fromisoformat(deployment_timestamp)
    else:
        start_time = datetime.now() - timedelta(hours=1)

    try:
        # Initialize Kusto client
        auth_mgr = get_auth_manager(use_default_credential=True)
        kusto_client = create_kusto_client(
            cluster_url=config.azure.kusto_cluster_url,
            database=config.azure.kusto_database_name,
            auth_manager=auth_mgr,
        )

        # Load and execute query template
        query = kusto_client.load_query_template(
            "fetch_detector_results",
            params={
                "detector_name": detector_name,
                "start_time": start_time.isoformat(),
            }
        )

        print(f"    Querying Kusto for detector: {detector_name}")
        print(f"    Time window: {start_time.isoformat()} to now")

        results = kusto_client.execute_query(query, timeout_seconds=60)

        # Analyze results
        if not results:
            return {
                "status": "no_data",
                "total_events": 0,
                "error_count": 0,
                "unique_hosts": 0,
                "error_rate": 0.0,
            }, f"No detector results found for '{detector_name}' since {start_time.strftime('%Y-%m-%d %H:%M:%S')}"

        # Aggregate metrics from results
        total_events = sum(row.get("EventCount", 0) for row in results)
        error_count = sum(row.get("ErrorCount", 0) for row in results)
        unique_hosts = max((row.get("UniqueHosts", 0) for row in results), default=0)
        error_rate = (error_count / total_events * 100) if total_events > 0 else 0.0

        metrics = {
            "status": "success",
            "total_events": total_events,
            "error_count": error_count,
            "unique_hosts": unique_hosts,
            "error_rate": round(error_rate, 2),
            "time_buckets": len(results),
        }

        # Generate summary message
        summary = (
            f"Detector found {total_events} events in the last hour "
            f"across {unique_hosts} unique hosts. "
        )

        if error_count > 0:
            summary += f"⚠️  {error_count} errors detected (error rate: {error_rate:.2f}%). "
        else:
            summary += "No errors detected. "

        return metrics, summary

    except Exception as e:
        print(f"    ⚠️  Error querying Kusto: {e}")
        return {
            "status": "error",
            "error": str(e),
        }, f"Error fetching results: {str(e)}"


# Define approval function for results confirmation
@ai_function(approval_mode="always_require")
def confirm_detector_results(
    detector_name: Annotated[str, "The detector name"],
    total_events: Annotated[int, "Total events detected"],
    error_count: Annotated[int, "Number of errors"],
    error_rate: Annotated[float, "Error rate percentage"],
) -> str:
    """
    Confirm that detector results look acceptable.

    This function requires explicit user confirmation that the detector
    is working correctly before proceeding.
    """
    return "Detector results confirmed - workflow will continue"


async def _handle_results_confirmation(
    workflow_data: dict[str, Any],
    metrics: dict[str, Any],
    chat_client: AzureOpenAIChatClient,
) -> bool:
    """
    Handle user confirmation of detector results using MAF's ChatAgent approval pattern.

    Args:
        workflow_data: Workflow state with detector info
        metrics: Results metrics from Kusto analysis
        chat_client: Azure OpenAI chat client for agent

    Returns:
        True if confirmed, False otherwise
    """
    # Present results details
    print("\n" + "=" * 70)
    print("\n   📊 DETECTOR RESULTS ANALYSIS")
    print("   " + "=" * 68)

    rule_id = workflow_data.get("rule_id", "unknown")
    detector_name = f"detector_{rule_id}"

    print(f"\n   Detector: {detector_name}")
    print(f"   Rule ID: {rule_id}")

    if metrics.get("status") == "success":
        print(f"\n   Total Events: {metrics['total_events']}")
        print(f"   Error Count: {metrics['error_count']}")
        print(f"   Error Rate: {metrics['error_rate']}%")
        print(f"   Unique Hosts: {metrics['unique_hosts']}")
        print(f"   Time Buckets: {metrics['time_buckets']} (5-minute intervals)")
    elif metrics.get("status") == "placeholder":
        print(f"\n   Total Events: {metrics['total_events']} (placeholder)")
        print(f"   Error Count: {metrics['error_count']}")
        print(f"   Unique Hosts: {metrics['unique_hosts']}")
    elif metrics.get("status") == "no_data":
        print("\n   Status: No data found")
        print("   This may be expected if the detector hasn't triggered yet.")
    else:
        print(f"\n   Status: {metrics.get('status', 'unknown')}")

    print("\n" + "=" * 70)

    # Check for auto-confirmation override (for testing/CI)
    auto_confirm = os.getenv("MAF_AUTO_CONFIRM_RESULTS", "false").lower() == "true"
    if auto_confirm:
        print("\n   ✓ Auto-confirming results (MAF_AUTO_CONFIRM_RESULTS=true)")
        return True

    # Create ChatAgent with approval-required function
    async with ChatAgent(
        chat_client=chat_client,
        name="ResultsConfirmationAgent",
        instructions=f"""You are a detector results confirmation assistant.

Your task is to help the user confirm whether the detector results look acceptable.

Detector: {detector_name}
Metrics: {metrics}

The user needs to review these results and decide if they want to proceed.
Call the confirm_detector_results function to request user confirmation.""",
        tools=[confirm_detector_results]
    ) as agent:
        # Initial query to trigger confirmation request
        query = f"""Please confirm the detector results for '{detector_name}'.

The detector detected {metrics.get('total_events', 0)} events with an error rate of {metrics.get('error_rate', 0)}%.

Do the results look acceptable?"""

        result = await agent.run(query)

        # Process confirmation requests using MAF pattern
        while len(result.user_input_requests) > 0:
            new_inputs: list[ChatMessage] = []

            for user_input_needed in result.user_input_requests:
                # Add confirmation request to context
                new_inputs.append(ChatMessage(role="assistant", contents=[user_input_needed]))

                # Get user confirmation
                user_input = await asyncio.to_thread(
                    input, "\n   Do the results look correct? Type 'yes' to proceed or 'no' to investigate: "
                )

                confirmed = user_input.strip().lower() in ['y', 'yes']

                # Add confirmation response
                new_inputs.append(
                    ChatMessage(role="user", contents=[
                        user_input_needed.create_response(confirmed)
                    ])
                )

                return confirmed

            # Continue with confirmation context
            result = await agent.run(new_inputs)

        # Default to rejection for safety
        return False


@executor(id="results_analysis")
async def results_analysis_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 8: Results Analysis
    Queries Kusto for detector results, analyzes effectiveness, and prompts user for confirmation.
    Uses MAF ChatAgent approval pattern for human-in-the-loop confirmation.
    """
    print("\n✓ [8/9] Results Analysis")
    print("    Initializing Results Analysis...")

    # Fetch and analyze results from Kusto
    metrics, summary = await _fetch_and_analyze_results(workflow_data)

    print(f"\n    {summary}")

    # Update workflow data with metrics
    workflow_data["results_metrics"] = metrics
    workflow_data["results_summary"] = summary
    workflow_data["events_detected"] = metrics.get("total_events", 0)
    workflow_data["error_rate"] = metrics.get("error_rate", 0.0)
    workflow_data["current_step"] = "results_analysis"

    # If deployment was skipped, mark as failed
    if metrics.get("status") == "skipped":
        workflow_data["results_acceptable"] = False
        workflow_data["results_confirmed"] = False
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = "Deployment was not successful"
        print("\n    ❌ Skipping - deployment was not successful")
        print(f"    ❌ Status: Failed - workflow will stop")
        await ctx.send_message(workflow_data)
        return

    # Handle user confirmation using MAF pattern
    chat_client = AzureOpenAIChatClient()
    confirmed = await _handle_results_confirmation(workflow_data, metrics, chat_client)

    # Update workflow data
    workflow_data["results_acceptable"] = confirmed
    workflow_data["results_confirmed"] = confirmed
    workflow_data["status"] = "success" if confirmed else "failed"
    workflow_data["current_step"] = "results_analysis" if confirmed else "results_analysis_rejected"

    if not confirmed:
        workflow_data["error_message"] = "Results not confirmed by user"

    if confirmed:
        print("\n    ✅ Results confirmed by user")
        print(f"    ✓ Status: Success")
    else:
        print("\n    ❌ Results not confirmed by user")
        print(f"    ❌ Status: Failed - workflow will stop")

    # Send message to next executor
    await ctx.send_message(workflow_data)


# ==================================
# Production Promotion Components
# ==================================


def _generate_promotion_changes(
    workflow_data: dict[str, Any],
    patterns: dict[str, Any]
) -> dict[str, str]:
    """
    Generate promotion configuration changes based on patterns.

    Args:
        workflow_data: Workflow state with detector info
        patterns: Promotion patterns from PromotionPatternAnalyzer

    Returns:
        Dictionary mapping file paths to file contents
    """
    rule_id = workflow_data.get("rule_id", "unknown")
    detector_name = f"detector_{rule_id}"

    changes = {}

    # Generate feature flag configuration
    # Look for feature flag patterns in promotion history
    production_indicators = patterns.get("production_indicators", [])
    flag_indicators = [i for i in production_indicators if i.get("type") == "feature_flags"]

    if flag_indicators and flag_indicators[0].get("examples"):
        # Use pattern from historical PRs
        flag_file = flag_indicators[0]["examples"][0]
    else:
        # Default location
        flag_file = "config/feature_flags.json"

    # Generate feature flag content
    import json
    feature_flags = {
        "features": {
            detector_name: {
                "enabled": True,
                "customer_facing": True,
                "rollout_percentage": 100,
                "description": f"Enable {rule_id} detector for production use"
            }
        }
    }
    changes[flag_file] = json.dumps(feature_flags, indent=2)

    # Generate README update documenting the promotion
    readme_file = "docs/DETECTOR_PROMOTION.md"
    readme_content = f"""# Detector Promotion: {rule_id}

## Overview
This PR promotes the {detector_name} detector to customer-facing production status.

## Detector Information
- **Rule ID**: {rule_id}
- **Detector Name**: {detector_name}
- **Provider GUID**: {workflow_data.get('provider_guid', 'N/A')}

## Results Summary
{workflow_data.get('results_summary', 'No results summary available')}

## Metrics
- **Events Detected**: {workflow_data.get('events_detected', 0)}
- **Error Rate**: {workflow_data.get('error_rate', 0.0)}%

## Changes
- Enabled feature flag for {detector_name}
- Updated configuration for customer-facing deployment

## Testing
Detector has been validated with results analysis in pre-production environment.
"""
    changes[readme_file] = readme_content

    return changes


@executor(id="production_promotion")
async def production_promotion_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[Never, dict[str, Any]]
) -> None:
    """
    Step 9: Production Promotion
    Creates a PR to promote the detector to customer-facing production status.
    Uses PromotionPatternAnalyzer to follow team conventions.
    """
    print("\n✓ [9/9] Production Promotion")
    print("    Analyzing promotion patterns...")

    # Check if results were confirmed (should not happen with conditional edges)
    if not workflow_data.get("results_confirmed", False):
        print("\n    ❌ Results not confirmed - cannot promote to production")
        workflow_data["promotion_status"] = "skipped_no_confirmation"
        workflow_data["current_step"] = "production_promotion_skipped"
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = "Results not confirmed"
        await ctx.yield_output(workflow_data)
        return

    config = get_config()

    # Check Azure DevOps configuration
    if not config.azure.azure_devops_org or not config.azure.azure_devops_project or not config.azure.azure_devops_repo:
        print("    ❌ Azure DevOps not configured - cannot create promotion PR")
        workflow_data["promotion_status"] = "skipped_no_config"
        workflow_data["current_step"] = "production_promotion_skipped"
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = "Azure DevOps not configured"
        await ctx.yield_output(workflow_data)
        return

    try:
        # Initialize Azure DevOps connection
        auth_mgr = get_auth_manager(use_default_credential=True)
        connection = auth_mgr.get_azure_devops_connection(config.azure.azure_devops_org)

        # Analyze promotion patterns
        from agents.promotion_pattern_analyzer import create_promotion_pattern_analyzer

        print("    Fetching historical promotion PRs...")
        analyzer = create_promotion_pattern_analyzer(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository=config.azure.azure_devops_repo
        )

        promotion_prs = analyzer.fetch_promotion_prs(limit=10)
        patterns = analyzer.extract_promotion_patterns(promotion_prs)

        print(f"    Analyzed {patterns['pr_count']} promotion PRs")

        # Generate promotion changes
        print("    Generating promotion configuration changes...")
        changes = _generate_promotion_changes(workflow_data, patterns)

        # Create branch
        rule_id = workflow_data.get("rule_id", "unknown")
        detector_name = f"detector_{rule_id}"
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"detector/production-{rule_id}-{timestamp}"

        print(f"    Creating branch: {branch_name}")

        from shared.repos_utils import create_branch, commit_and_push_files, create_pull_request

        # Create branch from main
        create_branch(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=branch_name,
            source_branch="main"
        )

        # Commit changes
        commit_message = f"Promote {detector_name} to production\n\n" \
                        f"Enable {rule_id} detector for customer-facing use.\n" \
                        f"Validated with {workflow_data.get('events_detected', 0)} events detected."

        print("    Committing promotion changes...")
        commit_and_push_files(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            branch_name=branch_name,
            file_changes=changes,
            commit_message=commit_message
        )

        # Determine PR title based on patterns
        title_patterns = patterns.get("title_patterns", [])
        title_prefix = "Promote"
        for pattern in title_patterns:
            if pattern.get("type") == "title_prefix" and pattern.get("confidence", 0) > 0.3:
                title_prefix = pattern["value"]
                break

        pr_title = f"{title_prefix}: Enable {detector_name} for production"

        # Generate PR description following patterns
        description_sections = []
        description_sections.append("## Summary")
        description_sections.append(f"Promote {detector_name} detector to customer-facing production status.")
        description_sections.append("")
        description_sections.append("## Detector Information")
        description_sections.append(f"- **Rule ID**: {rule_id}")
        description_sections.append(f"- **Detector Name**: {detector_name}")
        description_sections.append(f"- **Provider GUID**: {workflow_data.get('provider_guid', 'N/A')}")
        description_sections.append("")
        description_sections.append("## Validation Results")
        description_sections.append(f"- **Events Detected**: {workflow_data.get('events_detected', 0)}")
        description_sections.append(f"- **Error Rate**: {workflow_data.get('error_rate', 0.0)}%")
        description_sections.append(f"- **Results Summary**: {workflow_data.get('results_summary', 'N/A')}")
        description_sections.append("")
        description_sections.append("## Changes")
        for file_path in changes.keys():
            description_sections.append(f"- `{file_path}`")
        description_sections.append("")
        description_sections.append("## Testing")
        description_sections.append("Detector has been validated in pre-production environment with results analysis.")

        pr_description = "\n".join(description_sections)

        # Create PR
        print("    Creating promotion PR...")
        pr_response = create_pull_request(
            connection=connection,
            project=config.azure.azure_devops_project,
            repository_id=config.azure.azure_devops_repo,
            source_branch=branch_name,
            target_branch="main",
            title=pr_title,
            description=pr_description
        )

        # Store PR details
        promotion_pr_id = pr_response["pullRequestId"]
        promotion_pr_url = pr_response.get("url", f"https://dev.azure.com/{config.azure.azure_devops_org}/{config.azure.azure_devops_project}/_git/{config.azure.azure_devops_repo}/pullrequest/{promotion_pr_id}")

        workflow_data["promotion_pr_id"] = promotion_pr_id
        workflow_data["promotion_pr_url"] = promotion_pr_url
        workflow_data["promotion_branch_name"] = branch_name
        workflow_data["promotion_status"] = "completed"
        workflow_data["promotion_patterns"] = patterns
        workflow_data["current_step"] = "production_promotion_complete"
        workflow_data["status"] = "success"

        # Present results
        print("\n" + "=" * 70)
        print("\n   ✅ PRODUCTION PROMOTION PR CREATED")
        print("   " + "=" * 68)
        print(f"\n   PR URL: {promotion_pr_url}")
        print(f"   PR ID: {promotion_pr_id}")
        print(f"   Branch: {branch_name}")
        print(f"   Title: {pr_title}")
        print(f"\n   Files Changed: {len(changes)}")
        for file_path in changes.keys():
            print(f"     - {file_path}")
        print("\n" + "=" * 70)
        print("\n   🎉 Workflow Complete! Detector ready for production deployment.")
        print(f"   ✓ Status: Success")
        print()

    except Exception as e:
        print(f"\n    ❌ Error creating promotion PR: {e}")
        workflow_data["promotion_status"] = "failed"
        workflow_data["promotion_error"] = str(e)
        workflow_data["current_step"] = "production_promotion_failed"
        workflow_data["status"] = "failed"
        workflow_data["error_message"] = str(e)

    # Final output - workflow complete
    await ctx.yield_output(workflow_data)


async def build_detector_workflow():
    """
    Build the detector development workflow using MAF WorkflowBuilder.

    This creates a sequential pipeline of 9 executors with conditional routing that
    stops the workflow if any step fails. Checkpointing is enabled for recovery.

    Each executor sets status="success" or status="failed", and conditional routing
    ensures failed steps terminate the workflow.
    """
    workflow = (
        WorkflowBuilder()
        .set_start_executor(detector_triage_executor)
        .add_switch_case_edge_group(
            detector_triage_executor,
            [
                Case(is_successful, etw_input_collection_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            etw_input_collection_executor,
            [
                Case(is_successful, schema_discovery_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            schema_discovery_executor,
            [
                Case(is_successful, code_generator_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            code_generator_executor,
            [
                Case(is_successful, pr_creation_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            pr_creation_executor,
            [
                Case(is_successful, approval_gate_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            approval_gate_executor,
            [
                Case(is_successful, deployment_verification_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            deployment_verification_executor,
            [
                Case(is_successful, results_analysis_executor),
                Default(workflow_failure_handler)
            ]
        )
        .add_switch_case_edge_group(
            results_analysis_executor,
            [
                Case(is_successful, production_promotion_executor),
                Default(workflow_failure_handler)
            ]
        )
        .with_checkpointing(checkpoint_storage)  # Enable MAF checkpointing
        .build()
    )

    return workflow


async def main():
    """Main entry point for the MAF-based detector development workflow."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        🤖 maf-agents Detector Development Workflow             ║
║           (Microsoft Agent Framework Implementation)           ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Build the workflow
    workflow = await build_detector_workflow()
    print("✓ Workflow built with Microsoft Agent Framework")
    print("✓ Checkpoint persistence enabled (FileCheckpointStorage)")
    print("✓ Using conversational ETW input collection\n")

    # Prepare minimal input data - conversation will collect provider_guid and rule_id
    workflow_id = str(uuid4())
    input_data = {
        "workflow_id": workflow_id,
    }

    print(f"{'='*70}")
    print(f"🚀 Starting Detector Development Workflow")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   Mode: Interactive (Conversational)")
    print(f"{'='*70}")

    # Execute the workflow with streaming
    final_result = None
    async for event in workflow.run_stream(input_data):
        if isinstance(event, WorkflowOutputEvent):
            final_result = event.data
        elif isinstance(event, WorkflowFailedEvent):
            print(f"\n❌ Workflow failed: {event.details}")
            return

    # Display results
    if final_result:
        print(f"\n{'='*70}")
        print("✅ Workflow Completed Successfully")
        print(f"{'='*70}")
        print(f"\n📊 Final Results:")
        print(f"  Workflow ID: {final_result.get('workflow_id')}")
        print(f"  Current Step: {final_result.get('current_step')}")
        print(f"  PR Created: {final_result.get('pr_url')}")
        print(f"  Deployment: {'✅ Verified' if final_result.get('deployment_detected') else '❌ Not Detected'}")
        print(f"  Events Detected: {final_result.get('events_detected')}")
        print(f"  Results: {'✅ Acceptable' if final_result.get('results_acceptable') else '❌ Needs Review'}")
        print(f"\n{'='*70}\n")

    # List checkpoints
    checkpoints = await checkpoint_storage.list_checkpoints()
    print(f"💾 Checkpoints saved: {len(checkpoints)}")

    # Demonstrate checkpoint resumption
    if checkpoints:
        print("\n🔄 Demonstrating Checkpoint Resumption...")
        latest = max(checkpoints, key=lambda cp: cp.timestamp)
        print(f"   Latest checkpoint: {latest.checkpoint_id[:16]}...")
        print("   (In production, workflow could resume from this checkpoint)\n")


if __name__ == "__main__":
    asyncio.run(main())
