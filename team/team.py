# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

# Based on https://github.com/Azure/azure-sdk-for-python/tree/7f1ed2154441a0177c3017061af9931ed7fb2504/sdk/ai/azure-ai-agents/samples/agents_multiagent

import os
import json
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from utils.agent_team import AgentTeam, _create_task
from utils.agent_trace_configurator import AgentTraceConfigurator

endpoint="https://ai-msivara2297ai516397953488.services.ai.azure.com/api/projects/ai-brand-summary"
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

with project_client:
    agents_client = project_client.agents

    AgentTraceConfigurator(agents_client=agents_client).setup_tracing()
    with agents_client:
        while True:
            # user_input = "What were the sales at Athleta US Online last week?"
            config_name = input("Config name or Enter to quit: ")
            if not config_name:
                break
            config_dir = os.path.join(os.getcwd(), "configs")
            agent_team = AgentTeam(project_client, os.path.join(config_dir, f"{config_name}.yaml"))            
            user_prompt = input(f"Run-specific data (e.g., '{agent_team.get_prompt_example()}') or Enter to quit: ")
            if not user_prompt:
                break    
            agent_team.build_team()
            result = agent_team.process_request(request=f"Context: {user_prompt}")
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{config_name}.json")
            with open(output_path, "w") as f:
                f.write(result)
            print(f"Result saved to {output_path}")
            agent_team.dismantle_team()

        print("All done.")
