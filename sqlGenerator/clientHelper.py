import json
import time
from openai import AzureOpenAI
from sqlFunctions import get_tables, get_columns, get_tables_for_column, try_query

class ClientHelper(AzureOpenAI):
    def __init__(self, azure_endpoint, api_key, api_version):
        super().__init__(
            azure_endpoint=azure_endpoint,    
            api_key=api_key,
            api_version=api_version,
        )
        self.call_function_count = 0
        self._query = ""
        
    @property
    def query(self):
        return self._query

    def send_and_run(self, assistant_id, thread_id, content):
        self.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )
        return self.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

    def wait_on_run(self, run):
        status = run.status
        while status not in ["completed", "cancelled", "expired", "failed", "requires_action"]:
            run = self.beta.threads.runs.retrieve(thread_id=run.thread_id, run_id=run.id)
            status = run.status
            if status == "queued":
                time.sleep(5)
            if status == "failed":
                print(run.last_error.message)
        return run

    def call_function(self, run):
        tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print("Calling Function:", name)
        tool_outputs = []
        match name:
            case "get_tables":
                tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables()})
            case "get_columns":
                tool_outputs.append({"tool_call_id": tool_call.id, "output": get_columns(arguments["tables"])})
            case "get_tables_for_column":
                tool_outputs.append({"tool_call_id": tool_call.id, "output": get_tables_for_column(arguments["columnName"])})
            case "try_query":
                if self.call_function_count < 3:
                    self._query = arguments["query"]
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": try_query(arguments["query"])})
                    self.call_function_count += 1
                else:
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": "Done"})
            case _:
                print("Unknown function")
        return self.beta.threads.runs.submit_tool_outputs(
            thread_id=run.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs,
        )