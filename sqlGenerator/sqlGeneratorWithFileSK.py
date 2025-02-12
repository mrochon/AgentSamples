# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel


def get_filepath_for_filename(filename: str) -> str:
    base_directory = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_directory, filename)


filenames = [
    "schema.json",
]

from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
class SQLPlugin:
    """A sample Menu Plugin used for the concept sample."""

    @kernel_function(description="Executes a query.")
    def try_query(self, query) -> Annotated[str, "Returns results of the query execution."]:
        print(f"Executing try_query: {query}")
        return """
        John, Smith, 123 Main St, Springfield, IL, 62701
        Jown, Doe, 456 Elm St, Chicago, IL, 60601
        """

AGENT_NAME = "SQLGenerator"
AGENT_INSTRUCTIONS = """
      You are an SQL expert who translates user requests into SQL queries. The provided file contains the database schema. 
      Use only table and column names contained in that schema. Always use the TABLE_SCHEMA name as prefix for the table name.
      You may only generate SELECT statements. Do not generate DLETE, INSERT or UPDATE statements.
      If you cannot generate a query, you can ask the user for more information or clarification. 
      If you can generate a query, call the try_query function with the query as an argument. 
      If the function responds with an error message, try correcting the original query or ask the user for more information. Otherwise, return the query to the user.
            """

# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=input))
    print(f"# {AuthorRole.USER}: '{input}'")
    async for content in agent.invoke(thread_id=thread_id):
        print(f"# {content.role}: {content.content}")
        if len(content.items) > 0:
            for item in content.items:
                if isinstance(item, AnnotationContent):
                    print(f"\n`{item.quote}` => {item.file_id}")
                    response_content = await agent.client.files.content(item.file_id)
                    print(response_content.text)

async def main():
    kernel = Kernel()
    sql = SQLPlugin()
    kernel.add_function("try_query", sql.try_query)
    service_id = "agent"    
    agent = await AzureAssistantAgent.create(
        kernel=kernel,
        service_id=service_id,
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        enable_code_interpreter=True,
        code_interpreter_filenames=[get_filepath_for_filename(filename) for filename in filenames], 
        temperature=1.0,
        top_p=1.0
    )
    thread_id = await agent.create_thread()
    userQueries = [
        "List names of all customers.",
        "Which customers placed orders in the last two months?",
        "Which customer ordered product with id 'XYZ'?",
        "Delete all customers",
    ]
    try:
        for userQuery in userQueries:
            await invoke_agent(agent, thread_id=thread_id, input=userQuery)
    finally:
        if agent is not None:
            [await agent.delete_file(file_id) for file_id in agent.code_interpreter_file_ids]
            await agent.delete_thread(thread_id)
            await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())