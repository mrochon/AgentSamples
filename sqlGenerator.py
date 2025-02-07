import os
from openai import AzureOpenAI
from IPython.display import clear_output
import json
import time
from helpers import function_to_schema
from dotenv import load_dotenv
from helpers import function_to_schema
from sqlFunctions import get_tables, get_columns, try_query

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
        time.sleep(5)
        run = client.beta.threads.runs.retrieve(thread_id=run.thread_id,run_id=run.id)
        print("Elapsed time: {} minutes {} seconds".format(int((time.time() - start_time) // 60), int((time.time() - start_time) % 60)))
        status = run.status
        print(f'Status: {status}')
        if(status == "failed"):
          print(run.last_error.message)
        clear_output(wait=True)
    return run


def call_function(run):
    tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
    name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    print("Waiting for custom Function:", name)
    print("Function arguments:")
    print(arguments)
    tool_outputs = []
    match name:
      case "get_tables":
        tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables()})
      case "get_columns":
        tool_outputs.append({"tool_call_id": tool_call.id, "output": get_columns(arguments["tables"])})
      case "try_query":
        tool_outputs.append({"tool_call_id": tool_call.id, "output": try_query(arguments["query"])})        
      case _:
        print("Unknown function")
    return client.beta.threads.runs.submit_tool_outputs(
        thread_id=run.thread_id,
        run_id=run.id,
        tool_outputs= tool_outputs,
)

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

sql_agent = client.beta.assistants.create(
    name="SQL Expert",
    instructions=f"""
   You are an SQL expert who translates user requests into SQL queries. You must use the database schema to make sure you only use table and column names known to the database.
   You have the following functions available to get more information or to test the query:
   get_tables - returns names of all tables in the database
   get_columns - returns names of all columns in the tables you must provide to the function
   try_query - takes an SQL query as an argument and returns the first 10 rows of the result or an error message. If the response to the query is an error message, 
      use it to modify the query and try again. If the response is table data you can stop.
""",
    tools=[
        {'type': 'function', 'function': {'name': 'get_tables', 'description': 'Get list of tables for the database.'}}, 
        function_to_schema(get_columns), 
        function_to_schema(try_query)],
    model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"), 
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
      if msg.startswith("Please provide"):
        print(msg)
        user_input = input(f"{msg}:> ")
        run = send_and_run(client, agent.id, thread.id, user_input)
      else:
        print(msg)
        break
    case "requires_action":
      run = call_function(run)
    case _:
      print(f"Unexpected action: {run.status}")
      break
print("Done")
