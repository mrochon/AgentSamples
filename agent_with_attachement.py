import os
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FileSearchTool, FilePurpose, ListSortOrder, MessageAttachment
from azure.identity import DefaultAzureCredential

def pre_process_xls():
    import pandas as pd

    # Define paths
    output_dir = "uploads"
    data_dir_path = "data"
    sales_order_files = ["financial_sample.xlsx"]
    output_dir_path = os.path.join(data_dir_path, output_dir)

    # Ensure output directory exists
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    # Prefix the data directory path to each file
    sales_order_files = [os.path.join(data_dir_path, curr_file) for curr_file in sales_order_files]

    # Store the uploaded file IDs to be used later when enabling File Search
    markdown_file_paths = []

    for curr_file in sales_order_files:
        try:
            # Check if the file exists
            if not os.path.exists(curr_file):
                raise FileNotFoundError(f"The file '{curr_file}' does not exist.")
            df = pd.read_excel(curr_file)
            print(f"Workbook '{curr_file}' successfully loaded.")
            base_name = os.path.splitext(os.path.basename(curr_file))[0]
            md_tbl_str = df.to_markdown(index=False, tablefmt="pipe")
            output_file = os.path.join(output_dir_path, f"{base_name}.md")
            markdown_file_paths.append(output_file)
            with open(output_file, "w") as f:
                f.write(md_tbl_str)
            print(f"Markdown file '{output_file}' successfully written.")
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An error occurred while processing the Excel file '{curr_file}': {e}")
        return markdown_file_paths

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

    # Create agent
    model = os.getenv("MODEL_DEPLOYMENT_NAME")
    print(f"Using model: {model}")
    agent = agents_client.create_agent(
        model=model,
        name="my-agent",
        instructions="You are helpful agent searching for information in the uploaded files.",
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = agents_client.threads.create()
    print(f"Created thread, thread ID: {thread.id}")

    # Create a message with the file search attachment
    # Notice that vector store is created temporarily when using attachments with a default expiration policy of seven days.
    attachment = MessageAttachment(file_id=file.id, tools=FileSearchTool().definitions)
    message = agents_client.messages.create(
        thread_id=thread.id, role="user", content="Which countries is Velo sold?", attachments=[attachment]
    )
    print(f"Created message, message ID: {message.id}")

    run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Created run, run ID: {run.id}")
    if(run.status == "completed"):
        print("Run succeeded")
    else:
        print(f"Run failed with status: {run.last_error.message}")

    messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)

    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role}: {last_text.text.value}")
            
    agents_client.delete_agent(agent.id)
    
    
    print("Deleted agent")