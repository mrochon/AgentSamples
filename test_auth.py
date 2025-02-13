import os
import asyncio
from semantic_kernel.kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=os.environ["AZURE_PROJECTS_CONNECTION_STRING"]
        ) as client,
    ):
        kernel = Kernel()
        kernel.add_service(AzureChatCompletion())

        AGENT_NAME = "Host"
        AGENT_INSTRUCTIONS = "Answer questions about the menu."

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            # Optionally configure polling options
            # polling_options=RunPollingOptions(run_polling_interval=timedelta(seconds=1)),
        )

if __name__ == "__main__":
    asyncio.run(main())
print("Done")