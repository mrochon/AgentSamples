import os
import time
import os, time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from helpers import function_to_schema
from dotenv import load_dotenv
from helpers import function_to_schema
from sqlFunctions import get_tables, get_columns, get_tables_for_column, try_query
from IPython.display import clear_output

project_client = AIProjectClient(
    subscription_id = os.environ["SUBSCRIPTION_ID"],
    resource_group_name =os.environ["RG_NAME"],
    project_name=os.environ["PROJECT_NAME"],
    credential=DefaultAzureCredential(),
    endpoint=os.environ["PROJECT_ENDPOINT"],
)

with project_client:
    user_functions = {get_tables, get_columns, get_tables_for_column, try_query}
    sql_agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="sql_agent",
        instructions=f"""
   You are an SQL expert who translates user requests into SQL queries. You must use the database schema to make sure you only use table and column names known to the database.
   You have the following functions available to get more information or to test the query:
   get_tables - returns names of all tables in the database
   get_columns - returns names of all columns in the tables you must provide to the function
   get_tables_for_column - takes a column name as an argument and returns the names of all tables that contain a column with this or a similar name
   try_query - takes an SQL query as an argument and returns the first 10 rows of the result or an error message. If the response to the query is an error message, 
      use it to modify the query and try again. If the response is table data you can stop.
   If none of the above functions is suitable and you need additional information, respond with a request for that information starting with "Please provide".
""",
        tools=FunctionTool(functions=user_functions).definitions,
    )
    
    # Create a thread for communication
    thread = project_client.agents.threads.create()
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="List names and ages of all customers."
    )
    run = project_client.agents.runs.create(thread_id=thread.id, agent_id=sql_agent.id)
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)  

        if run.status == "requires_action":
          tool_calls = run.required_action.submit_tool_outputs.tool_calls
          tool_outputs = []
          for tool_call in tool_calls:
              if not tool_call.function:
                  print(f"Tool call {tool_call.id} has no function defined.")
                  continue
              func = tool_call.function
              match func.name:
                case "get_tables":
                  tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables()})
                case "get_columns":
                  tool_outputs.append({"tool_call_id": tool_call.id, "output": get_columns(func.arguments["tables"])})
                case "get_tables_for_column":
                  tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables_for_column(func.arguments["columnName"])})            
                case "try_query":
                  tool_outputs.append({"tool_call_id": tool_call.id, "output": try_query(func.arguments["query"])})
                case _:
                  print(f"Unknown function: {func.name}")
          project_client.agents.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)            

    print(f"Run completed with status: {run.status}")
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message['role']}, Content: {message['content']}")

    # Delete the agent after use
    project_client.agents.delete_agent(sql_agent.id)  
    print("Deleted agent")
# End of code