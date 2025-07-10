from datetime import datetime, timedelta
# Assume client is an authenticated AgentsClient for your project
# Define a threshold – e.g., delete any artifact older than 7 days
threshold_date = datetime.utcnow() - timedelta(days=7)
 
# 1. Clean up agents
for agent in client.list_agents():
    if agent.created_on < threshold_date and agent.name != "keep-me":  # adjust condition as needed
        client.delete_agent(agent.id)
        print(f"Deleted old agent: {agent.name}")
 
# 2. Clean up threads
for thread in client.threads.list():
    if thread.created_on < threshold_date:
        client.threads.delete(thread.id)
        print(f"Deleted old thread: {thread.id}")
 
# 3. Clean up vector stores (if any)
for vs in client.vector_stores.list():
    if vs.created_on < threshold_date:
        client.vector_stores.delete(vs.id)
        print(f"Deleted vector store: {vs.name}")
 
# 4. Clean up files
for file in client.files.list():
    if file.created_on < threshold_date:
        client.files.delete(file_id=file.id)
        print(f"Deleted file: {file.id}")