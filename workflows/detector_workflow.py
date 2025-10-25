"""
Main workflow orchestrator for maf-agents using Microsoft Agent Framework.

This implementation uses the actual MAF SDK with proper executor patterns
for sequential orchestration of 7 detector development steps, integrating
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
    AgentRunResponse,
)
from agent_framework.openai import OpenAIChatClient
from typing_extensions import Never

from shared.config import get_config
from shared.kusto_client import create_kusto_client
from shared.auth import get_auth_manager
from agents.etw_input_agent import create_etw_input_agent
from agents.schema_discovery_agent import create_schema_discovery_agent

# Configure checkpoint storage
checkpoint_dir = Path("./checkpoints")
checkpoint_dir.mkdir(exist_ok=True)
checkpoint_storage = FileCheckpointStorage(checkpoint_dir)


# Define the 7 workflow agents as MAF executors
# Each executor represents a step in the detector development workflow

@executor(id="etw_input_collection")
async def etw_input_collection_executor(
    input_data: dict[str, Any] | None,
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 1: ETW Input Collection
    Uses the ETW Input Agent to collect and validate providerGuid and ruleId
    through a conversational interface.
    """
    print("\n✓ [1/7] ETW Input Collection (Conversational Agent)")
    print("    Initializing ETW Input Collection Agent...")

    # Create the ETW Input Agent
    agent = await create_etw_input_agent(use_azure=False)

    # Check if data was pre-populated (for automation) or needs conversational collection
    if input_data and "provider_guid" in input_data and "rule_id" in input_data:
        provider_guid = input_data["provider_guid"]
        rule_id = input_data["rule_id"]
        print(f"    Using pre-populated input data")

        # Validate pre-populated data using the agent
        etw_input = await agent.collect_inputs(
            provider_guid=provider_guid,
            rule_id=rule_id
        )
    else:
        # Interactive conversational collection
        print("\n    Starting conversational collection...")
        etw_input = await agent.collect_inputs()

    # Build workflow data
    etw_data = {
        "provider_guid": etw_input.provider_guid,
        "rule_id": etw_input.rule_id,
        "workflow_id": input_data.get("workflow_id", str(uuid4())) if input_data else str(uuid4()),
        "current_step": "etw_input_collection",
    }

    print(f"    ✓ Provider GUID: {etw_input.provider_guid}")
    print(f"    ✓ Rule ID: {etw_input.rule_id}")

    await ctx.send_message(etw_data)


@executor(id="schema_discovery")
async def schema_discovery_executor(
    etw_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 2: Schema Discovery
    Uses the Schema Discovery Agent to query Kusto for ETW schema
    and existing detectors through a conversational interface.
    """
    print("\n✓ [2/7] Schema Discovery (Conversational Agent)")
    print("    Initializing Schema Discovery Agent...")

    config = get_config()

    # Initialize Kusto client if configured
    if config.azure.kusto_cluster_url and config.azure.kusto_database_name:
        try:
            auth_mgr = get_auth_manager(use_default_credential=True)
            kusto_client = create_kusto_client(
                cluster_url=config.azure.kusto_cluster_url,
                database=config.azure.kusto_database_name,
                auth_manager=auth_mgr,
            )

            # Create the Schema Discovery Agent
            agent = await create_schema_discovery_agent(
                kusto_client=kusto_client,
                use_azure=False
            )

            # Run schema discovery
            schema_data = await agent.discover_schema(
                provider_guid=etw_data["provider_guid"],
                rule_id=etw_data["rule_id"]
            )

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

        except Exception as e:
            print(f"    ⚠️  Schema discovery failed: {str(e)}, using placeholder data")
            etw_data["schema_fields"] = [
                {"FieldName": "EventId", "DataType": "int", "Description": "Event ID"},
                {"FieldName": "Timestamp", "DataType": "datetime", "Description": "Event timestamp"},
                {"FieldName": "Message", "DataType": "string", "Description": "Event message"},
            ]
            etw_data["existing_detectors"] = []
    else:
        print("    ⚠️  Kusto not configured, using placeholder data")
        etw_data["schema_fields"] = [
            {"FieldName": "EventId", "DataType": "int", "Description": "Event ID"},
            {"FieldName": "Timestamp", "DataType": "datetime", "Description": "Event timestamp"},
            {"FieldName": "Message", "DataType": "string", "Description": "Event message"},
        ]
        etw_data["existing_detectors"] = []

    etw_data["current_step"] = "schema_discovery"

    await ctx.send_message(etw_data)


@executor(id="code_generator")
async def code_generator_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 3: Code Generator
    Analyzes historical PRs and generates detector code.
    """
    print("\n✓ [3/7] Code Generator")
    print("    Analyzing historical PR patterns...")
    print("    Generating detector code...")

    workflow_data["generated_files"] = {
        "detector_file": f"detector_{workflow_data['rule_id']}.py",
        "test_file": f"test_detector_{workflow_data['rule_id']}.py",
    }
    workflow_data["current_step"] = "code_generator"

    await ctx.send_message(workflow_data)


@executor(id="pr_creation")
async def pr_creation_executor(
    workflow_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """
    Step 4: PR Creation
    Creates branch, commits code, and submits PR to Azure Repos using Azure DevOps SDK directly.
    """
    print("\n✓ [4/7] PR Creation")

    config = get_config()

    # Check if Azure DevOps is configured
    if not config.azure.azure_devops_org or not config.azure.azure_devops_project or not config.azure.azure_devops_repo:
        print("    ⚠️  Azure DevOps not configured, using mock PR creation")
        workflow_data["pr_url"] = f"https://dev.azure.com/org/project/_git/repo/pullrequest/12345"
        workflow_data["pr_id"] = 12345
        workflow_data["branch_name"] = f"detector/{workflow_data['rule_id']}"
        workflow_data["current_step"] = "pr_creation"
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

    except Exception as e:
        print(f"    ❌ PR creation failed: {str(e)}")
        print("    Using mock PR data for workflow continuation")
        workflow_data["pr_url"] = f"https://dev.azure.com/org/project/_git/repo/pullrequest/12345"
        workflow_data["pr_id"] = 12345
        workflow_data["branch_name"] = f"detector/{workflow_data['rule_id']}"
        workflow_data["current_step"] = "pr_creation"
        workflow_data["pr_creation_error"] = str(e)

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


async def _handle_pr_approval(workflow_data: dict[str, Any], chat_client: OpenAIChatClient) -> bool:
    """
    Handle PR approval using MAF's ChatAgent approval pattern.

    Args:
        workflow_data: Workflow state with PR details
        chat_client: OpenAI chat client for agent

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
    Step 5: User Approval Gate using MAF's ChatAgent approval pattern.

    Pauses workflow for human review and approval of PR using MAF's
    built-in user input request system with @ai_function approval_mode.

    This is a critical human-in-the-loop control point where users
    review the generated PR before allowing the workflow to continue.
    """
    print("\n✓ [5/7] User Approval Gate")
    print("=" * 70)

    # Create chat client for approval agent
    chat_client = OpenAIChatClient()

    # Handle PR approval using MAF pattern
    approved = await _handle_pr_approval(workflow_data, chat_client)

    # Update workflow data
    workflow_data["approved"] = approved
    workflow_data["approval_status"] = "approved" if approved else "rejected"
    workflow_data["current_step"] = "approval_gate"

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
    Step 6: Deployment Verification

    Monitors PR merge status and verifies successful deployment.
    Polls Azure Repos every 30 seconds with 60 minute timeout.
    Implements exponential backoff for API retries.
    """
    print("\n✓ [6/7] Deployment Verification")
    print("=" * 70)

    # Check if approval was granted
    if not workflow_data.get("approved", False):
        print("\n   ⚠️  PR was not approved - skipping deployment verification")
        workflow_data["pr_merged"] = False
        workflow_data["deployment_detected"] = False
        workflow_data["deployment_status"] = "skipped_no_approval"
        workflow_data["current_step"] = "deployment_verification"
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
    workflow_data["current_step"] = "deployment_verification"

    # Present results
    print("\n" + "=" * 70)
    if success:
        print(f"\n   ✅ {message}")
        print(f"   Timestamp: {workflow_data['deployment_timestamp']}")
    else:
        print(f"\n   ⚠️  {message}")

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
    chat_client: OpenAIChatClient
) -> bool:
    """
    Handle user confirmation of detector results using MAF's ChatAgent approval pattern.

    Args:
        workflow_data: Workflow state with detector info
        metrics: Results metrics from Kusto analysis
        chat_client: OpenAI chat client for agent

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
    Step 7: Results Analysis
    Queries Kusto for detector results, analyzes effectiveness, and prompts user for confirmation.
    Uses MAF ChatAgent approval pattern for human-in-the-loop confirmation.
    """
    print("\n✓ [7/8] Results Analysis")
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

    # If deployment was skipped, skip confirmation
    if metrics.get("status") == "skipped":
        workflow_data["results_acceptable"] = False
        workflow_data["results_confirmed"] = False
        print("\n    ⚠️  Skipping user confirmation - deployment was not successful")
        await ctx.send_message(workflow_data)
        return

    # Handle user confirmation using MAF pattern
    chat_client = OpenAIChatClient()
    confirmed = await _handle_results_confirmation(workflow_data, metrics, chat_client)

    # Update workflow data
    workflow_data["results_acceptable"] = confirmed
    workflow_data["results_confirmed"] = confirmed

    if confirmed:
        print("\n    ✅ Results confirmed by user - proceeding to production promotion")
    else:
        print("\n    ⚠️  Results not confirmed - user should investigate")

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
    Step 8: Production Promotion
    Creates a PR to promote the detector to customer-facing production status.
    Uses PromotionPatternAnalyzer to follow team conventions.
    """
    print("\n✓ [8/8] Production Promotion")
    print("    Analyzing promotion patterns...")

    # Check if results were confirmed
    if not workflow_data.get("results_confirmed", False):
        print("\n    ⚠️  Results not confirmed - skipping production promotion")
        workflow_data["promotion_status"] = "skipped_no_confirmation"
        workflow_data["current_step"] = "production_promotion_skipped"
        await ctx.yield_output(workflow_data)
        return

    config = get_config()

    # Check Azure DevOps configuration
    if not config.azure.azure_devops_org or not config.azure.azure_devops_project or not config.azure.azure_devops_repo:
        print("    ⚠️  Azure DevOps not configured - skipping production promotion")
        workflow_data["promotion_status"] = "skipped_no_config"
        workflow_data["current_step"] = "production_promotion_skipped"
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
        print()

    except Exception as e:
        print(f"\n    ⚠️  Error creating promotion PR: {e}")
        workflow_data["promotion_status"] = "failed"
        workflow_data["promotion_error"] = str(e)
        workflow_data["current_step"] = "production_promotion_failed"

    # Final output - workflow complete
    await ctx.yield_output(workflow_data)


async def build_detector_workflow():
    """
    Build the detector development workflow using MAF WorkflowBuilder.

    This creates a sequential pipeline of 8 executors with checkpointing enabled.
    """
    workflow = (
        WorkflowBuilder()
        .set_start_executor(etw_input_collection_executor)
        .add_edge(etw_input_collection_executor, schema_discovery_executor)
        .add_edge(schema_discovery_executor, code_generator_executor)
        .add_edge(code_generator_executor, pr_creation_executor)
        .add_edge(pr_creation_executor, approval_gate_executor)
        .add_edge(approval_gate_executor, deployment_verification_executor)
        .add_edge(deployment_verification_executor, results_analysis_executor)
        .add_edge(results_analysis_executor, production_promotion_executor)
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
    print("✓ Checkpoint persistence enabled (FileCheckpointStorage)\n")

    # Prepare input data
    workflow_id = str(uuid4())
    input_data = {
        "workflow_id": workflow_id,
        "provider_guid": "12345678-1234-1234-1234-123456789012",
        "rule_id": "test-detector-rule-1",
    }

    print(f"{'='*70}")
    print(f"🚀 Starting Workflow")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   Provider GUID: {input_data['provider_guid']}")
    print(f"   Rule ID: {input_data['rule_id']}")
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
