import os
import asyncio
import json
import time
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from helpers import function_to_schema
from openai import AzureOpenAI
from accessSql import SQL

load_dotenv()

async def main() -> None:
    from azure.identity.aio import DefaultAzureCredential
    token = await DefaultAzureCredential(
            exclude_interactive_browser_credential=True).get_token("https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),    
        # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview",
        azure_ad_token = token.token
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
    sql = SQL()
    token = await DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")

    sql_agent = client.beta.assistants.create(
        name="SQL Expert",
          instructions="""
        You are an SQL expert who translates user requests into SQL queries. The database schema is provided to you. 
        Use only table and column names contained in that schema. Always use the value of the TABLE_SCHEMA column in the schema as prefix for the table name.
        You may only generate SELECT statements. Do not generate DLETE, INSERT or UPDATE statements.
        You must always include 'TOP 3' in the query.
        If you cannot generate a query, you can ask the user for more information or clarification. 
        If you can generate a query, call the execute function with the query statement as argument. 
        If the function responds with an error message, try correcting the original query or ask the user for more information. Otherwise, return the query to the user.
              """,
        model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"), 
        tools=[
          {"type": "file_search"}, function_to_schema(SQL.execute)],
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},    
        temperature=1,
        top_p=1  
    )

    print("Creating thread...")
    thread = client.beta.threads.create()
    thread_id = thread.id
    await sql.open()
    try:
        is_complete: bool = False
        user_input = input("User:> ")
        if not user_input or user_input.isspace():
          is_complete = True
        else:
          client.beta.threads.messages.create(
              thread_id=thread_id,
              role="user",
              content=user_input
          )
          run = client.beta.threads.runs.create(
              thread_id=thread_id,
              assistant_id=sql_agent.id
          )
        while not is_complete:
          status = run.status
          while status not in ["completed", "cancelled", "expired", "failed", "requires_action"]:
              run = client.beta.threads.runs.retrieve(thread_id=run.thread_id, run_id=run.id)
              status = run.status
              if status == "queued":
                  time.sleep(5)
              if status == "failed":
                  print(run.last_error.message)
          match run.status:
            case "completed":
              msg = client.beta.threads.messages.list(thread_id=thread_id, order="desc").data[0].content[0].text.value
              user_input = input(f"{msg}\n:> ")
              if user_input == "":
                break
              client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input
                )
              run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=sql_agent.id
              )
            case "requires_action":
              tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
              name = tool_call.function.name
              arguments = json.loads(tool_call.function.arguments)
              print("Calling Function:", name)
              tool_outputs = []
              if name == "execute":
                tool_outputs.append({"tool_call_id": tool_call.id, "output": sql.execute(arguments["query"])})
              else:
                raise ValueError(f"Unknown function: {name}")
              run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=run.thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs,
              )
            case 'failed':
              print(f"Failed: {run.last_error.message}")
              break
            case _:
              print(f"Unexpected action: {run.status}")
              break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleaning up resources...")
        if sql_agent is not None:
          client.beta.vector_stores.delete(vector_store.id)
          client.beta.assistants.delete(sql_agent.id)
          client.beta.threads.delete(thread.id)
        await sql.close()


if __name__ == "__main__":
    asyncio.run(main())
print("Done")
