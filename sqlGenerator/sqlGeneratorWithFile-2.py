import os
import asyncio
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from helpers import function_to_schema
from AzureOpenAIExt import AzureOpenAIExt

load_dotenv()

async def main() -> None:
    token_provider = await DefaultAzureCredential(exclude_interactive_browser_credential=True).get_token("https://cognitiveservices.azure.com/.default") 
    token = token_provider.token  
    client = AzureOpenAIExt(token=token)

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
          {"type": "file_search"}, 
          {
            "type": "function",
            "function": {
                "name": "execute",
                "description": "Execute an SQL query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQl statement to execute"}
                    },
                    "required": ["query"]
                }
            }
        }],
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},    
        temperature=1,
        top_p=1  
    )

    print("Creating thread...")
    thread = client.beta.threads.create()
    thread_id = thread.id

    try:
        is_complete: bool = False
        user_input = input(f"Your query\n:> ")
        if not user_input or user_input.isspace():
          is_complete = True
        else:
          run = client.send_and_run(sql_agent.id, thread.id, user_input)        
        msg = "Please enter your query"
        while not is_complete:
          run = client.wait_for_run(run)
          match run.status:
            case "completed":
              msg = client.beta.threads.messages.list(thread_id=thread_id, order="desc").data[0].content[0].text.value
              user_input = input(f"{msg}\n:> ")
              if not user_input or user_input.isspace():
                break
              run = client.send_and_run(sql_agent.id, thread.id, user_input)
            case "requires_action":
              run = await client.call_function(run)
            case 'failed':
              print
              (f"Failed: {run.last_error.message}")
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
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
print("Done")
