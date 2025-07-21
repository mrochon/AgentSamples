import os
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FileSearchTool, FilePurpose, ListSortOrder
from azure.ai.agents.models import  MessageRole, CodeInterpreterTool
from azure.identity import DefaultAzureCredential
from pathlib import Path
# Based on https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-agents/samples/agents_files_images_inputs/sample_agents_with_code_interpreter_file_attachment.py

    
def ask_agent(agents_client, thread, agent, question):
    message = agents_client.messages.create(
        thread_id=thread.id, role="user", content=question
    )
    print(f"Created message, message ID: {message.id}")

    run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Created run, run ID: {run.id}")
    if run.status == "completed":
        print("Run succeeded")
    else:
        print(f"Run failed with status: {getattr(run.last_error, 'message', 'Unknown error')}")

asset_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./data/uploads/financial_sample.md"))
try:
    # Initialize the Azure AI Project client
    project_client = AIProjectClient(
        subscription_id = os.environ["SUBSCRIPTION_ID"],
        resource_group_name =os.environ["RG_NAME"],
        project_name=os.environ["PROJECT_NAME"],
        credential=DefaultAzureCredential(),
        endpoint=os.environ["PROJECT_ENDPOINT"],
    )
    print("Azure AI Studio client created successfully.")
except Exception as e:
    print(f"Error creating the project client: {e}")

with project_client:
    agents_client = project_client.agents
    # Upload a file and wait for it to be processed
    file = agents_client.files.upload_and_poll(file_path=asset_file_path, purpose=FilePurpose.AGENTS)
    print(f"Uploaded file, file ID: {file.id}")

    # Create a vector store with no file and wait for it to be processed
    vector_store = agents_client.vector_stores.create_and_poll(file_ids=[file.id], name="sample_vector_store")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    # Create a file search tool
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])

    model = os.getenv("MODEL_DEPLOYMENT_NAME")
    print(f"Using model: {model}")
    agent = agents_client.create_agent(
        model=model,
        name="my-agent",
        instructions="You are helpful agent with a file to search for information.",
        tools=file_search_tool.definitions + CodeInterpreterTool().definitions,
        tool_resources=file_search_tool.resources,
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = agents_client.threads.create()
    print(f"Created thread, thread ID: {thread.id}")

    ask_agent(agents_client, thread, agent, "In which countries is Velo sold?")
    ask_agent(agents_client, thread, agent, "How many units of Veli were sold in each country? Respond with a table listing country name and approximate number of total units sold")
    ask_agent(agents_client, thread, agent, "Create bar chart of Velo units sold by country and provide file to me?")

    messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
               
    # last_msg = agents_client.messages.get_last_message_text_by_role(thread_id=thread.id, role=MessageRole.AGENT)
    # if last_msg:
    #     print(f"Last Message: {last_msg.text.value}")
    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role}: {last_text.text.value}")   
        # Save every image file in the message
        # for img in msg.image_contents:
        #     file_id = img.image_file.file_id
        #     file_name = f"{file_id}_image_file.png"
        #     agents_client.files.save(file_id=file_id, file_name=file_name)
        #     print(f"Saved image file to: {Path.cwd() / file_name}")
        for ann in msg.file_path_annotations:
            file_id = ann.file_path.file_id
            file_name = ann.text if ann.text else f"{file_id}_file"
            download_path = f"{Path.cwd()}/output"
            agents_client.files.save(file_id=file_id, file_name=file_name, target_dir=download_path)
            print(f"Downloaded file to: {download_path}")
   
    agents_client.files.delete(file.id)
    print("Deleted file")         
    agents_client.delete_agent(agent.id)
    print("Deleted agent")