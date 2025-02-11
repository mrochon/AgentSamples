import json
import time
from sqlFunctions import get_tables, get_columns, get_tables_for_column, try_query

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
    
def wait_on_run(client, run):
    #start_time = time.time()
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

def call_function(client, run):
    if not hasattr(call_function, "count"):
      call_function.count = 0
    tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
    name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    print("Calling Function:", name)
    # print("Function arguments:")
    # print(arguments)
    tool_outputs = []
    match name:
      case "get_tables":
        tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables()})
      case "get_columns":
        tool_outputs.append({"tool_call_id": tool_call.id, "output": get_columns(arguments["tables"])})
      case "get_tables_for_column":
        tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables_for_column(arguments["columnName"])})            
      case "try_query":
        if(call_function.count < 3):
          tool_outputs.append({"tool_call_id": tool_call.id, "output": try_query(arguments["query"])})
          call_function.count += 1
        else:
          tool_outputs.append({"tool_call_id": tool_call.id, "output": "Done"})
      case _:
        print("Unknown function")
    return client.beta.threads.runs.submit_tool_outputs(
        thread_id=run.thread_id,
        run_id=run.id,
        tool_outputs= tool_outputs,
)