# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

# Based on https://github.com/Azure/azure-sdk-for-python/tree/7f1ed2154441a0177c3017061af9931ed7fb2504/sdk/ai/azure-ai-agents/samples/agents_multiagent
"""
DESCRIPTION:
    This sample demonstrates how to use multiple agents using AgentTeam with traces.

    The team consists of
        • one leader agent - automatically created by AgentTeam from the
          configuration in `utils/agent_team_config.yaml`
        • two worker agents - `Coder` and `Reviewer`, defined in the code below

    IMPORTANT - leader-agent model configuration
        `utils/agent_team_config.yaml` contains the key  TEAM_LEADER_MODEL.
        Its value must be the name of a **deployed** model in your Azure AI
        project (e.g. "gpt-4o-mini").
        If this model deployment is not available, AgentTeam cannot instantiate
        the leader agent and the sample will fail.

USAGE:
    python sample_agents_agent_team.py

    Before running the sample:

    1. pip install azure-ai-projects azure-ai-agents azure-identity
    2. Ensure `utils/agent_team_config.yaml` is present and TEAM_LEADER_MODEL points
       to a valid model deployment.
    3. Set these environment variables with your own values:
         PROJECT_ENDPOINT - The Azure AI Project endpoint, as found in the Overview
                            page of your Azure AI Foundry portal.
         MODEL_DEPLOYMENT_NAME - The model deployment name used for the worker agents.
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from utils.agent_team import AgentTeam, _create_task
from utils.agent_trace_configurator import AgentTraceConfigurator
from dotenv import load_dotenv
from pathlib import Path
# Calculate .env path based on the source directory of this module
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

endpoint=os.environ["PROJECT_ENDPOINT"],
project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

with project_client:
    agents_client = project_client.agents

    agents_client.enable_auto_function_calls({_create_task})

    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

    if model_deployment_name is not None:
        AgentTraceConfigurator(agents_client=agents_client).setup_tracing()
        with agents_client:
            agent_team = AgentTeam("finance_team", project_client)
            agent_team.build_team()


            print("A team of agents specialized in software engineering is available for requests.")
            while True:
                user_input = input("Input (type 'quit' or 'exit' to exit): ")
                if user_input.lower() == "quit":
                    break
                elif user_input.lower() == "exit":
                    break
                agent_team.process_request(request=user_input)

            agent_team.dismantle_team()
    else:
        print("Error: Please define the environment variable MODEL_DEPLOYMENT_NAME.")