import os
from dotenv import load_dotenv
# from azure.ai.projects.models import FileSearchTool, FilePurpose
from helpers import function_to_schema
from sqlFunctions import try_query
#from agentHelpers import send_and_run, wait_on_run, call_function
from clientHelper import ClientHelper

load_dotenv()

client = ClientHelper(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),    
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
)

# Which API? openai.beta, azure-project, SK?

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
      You are an SQL expert who translates user requests into SQL queries. The database schema is provided to you. 
      Use only table and column names contained in that schema. Always use the TABLE_SCHEMA name as prefix for the table name.
      You may only generate SELECT statements. Do not generate DLETE, INSERT or UPDATE statements.
      If you cannot generate a query, you can ask the user for more information or clarification. 
      If you can generate a query, call the try_query function with the query as an argument. 
      If the function responds with an error message, try correcting the original query or ask the user for more information. Otherwise, return the query to the user.
      """,
    model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"), 
    tools=[
      {"type": "file_search"},
      function_to_schema(try_query)],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},    
    temperature=1,
    top_p=1    
)
# Or should I add the store to the thread?

thread = client.beta.threads.create()
completed = False
# msg = "List names of all customers."
# msg = "Which customers placed orders in the last two months?"
msg = "Which customer ordered product with id 'XYZ'?"
# msg = "Delete all customers"
agent = sql_agent
run = client.send_and_run(agent.id, thread.id, msg)
while True:
  run = client.wait_on_run(run)
  match run.status:
    case "completed":
      msg = client.beta.threads.messages.list(thread_id=thread.id, order="desc").data[0].content[0].text.value
      user_input = input(f"{msg}:> ")
      if user_input == "":
        break
      run = client.send_and_run(agent.id, thread.id, user_input)
    case "requires_action":
      run = client.call_function(run)
    case 'failed':
      print(f"Failed: {run.last_error.message}")
      break
    case _:
      print(f"Unexpected action: {run.status}")
      break

# What happens if I do not do that?
client.beta.vector_stores.delete(vector_store.id)
client.beta.assistants.delete(sql_agent.id)
client.beta.threads.delete(thread.id)

print(f"Query: {client.query}")
print("Done")
