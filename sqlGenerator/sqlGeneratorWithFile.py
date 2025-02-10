import os
from openai import AzureOpenAI
from IPython.display import clear_output
import json
import time
from dotenv import load_dotenv
from azure.ai.projects.models import FileSearchTool, FilePurpose

def send_and_run(client, assistant_id, thread_id, content):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )
    return client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    
def wait_on_run(run):
    start_time = time.time()
    status = run.status
    while status not in ["completed", "cancelled", "expired", "failed", "requires_action"]:
        run = client.beta.threads.runs.retrieve(thread_id=run.thread_id,run_id=run.id)
        # print("Elapsed time: {} minutes {} seconds".format(int((time.time() - start_time) // 60), int((time.time() - start_time) % 60)))
        status = run.status
        if(status == "queued"):
                  time.sleep(5)
        # print(f'Status: {status}')
        if(status == "failed"):
          print(run.last_error.message)
        # clear_output(wait=True)
    return run


load_dotenv()

# print(os.getenv("AZURE_OPENAI_ENDPOINT"))
# print(os.getenv("AZURE_OPENAI_API_KEY"))
# print(os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"))
# exit()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),    
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
)

vector_store = client.beta.vector_stores.create(name="DB Schema")
file_paths = ["sqlGenerator/Schema.json"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
print(file_batch.status)
print(file_batch.file_counts)

sql_agent = client.beta.assistants.create(
    name="SQL Expert",
    instructions=f"""
      You are an SQL expert who translates user requests into SQL queries. The database schema is provided to you. You must respond with one of the following
      1. An SQL SELECT statement. Do not include any descriptive information, just plain SQL statement.
      2. Request for more information from the user. To ask the user for more information, start the response with 'User input required:'
      Make sure you only use table and column names contained in that schema.
      """,
    model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"), 
    tools=[{"type": "file_search"}],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},    
    temperature=1,
    top_p=1    
)

thread = client.beta.threads.create()
completed = False
msg = "List names of all customers."
agent = sql_agent
run = send_and_run(client, agent.id, thread.id, msg)
while True:
  run = wait_on_run(run)
  match run.status:
    case "completed":
      msg = client.beta.threads.messages.list(thread_id=thread.id, order="desc").data[0].content[0].text.value
      if msg.startswith("User input required:"):
        print(msg)
        user_input = input(f"{msg}:> ")
        run = send_and_run(client, agent.id, thread.id, user_input)
      else:
        print(msg)
        break
    case 'failed':
      print(f"Failed: {run.last_error.message}")
      break
    case _:
      print(f"Unexpected action: {run.status}")
      break
    
print("Done")
