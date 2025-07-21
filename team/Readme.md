## Multi-agent conversation

[Based on Azure AI sample](https://github.com/Azure/azure-sdk-for-python/tree/7f1ed2154441a0177c3017061af9931ed7fb2504/sdk/ai/azure-ai-agents/samples/agents_multiagent)

### Objective

This sample creates a number of agents and facilitates exchange of messages between with the objective of answering a user query.

### Operation

The application creates the agents based definitions contained n the agent_team_config.yaml file. One of these agents is designated as team leader.
Once the agents are created, the application requests user input. It is passed the leader agent, whose system prompt typically directs it to
determine which of the other agents is best suited to resolve the query (the leader agent is informed of what the other agents do). The request is then roted to the other agent (_create_task).
Its response is routed back to the leader agent, who may ask another agent to examine both it and the original user query. The conversation continues
until the leader agent decides, based on its system prompts that a conclusion has been reached. At that stage, it respond to the user.

Individual agents may be equiped with their own tools, for example ability to call functions, execute own code (interpretter tool) or search vector files.

### Agent definition

Agents are defined in the agents_team.yaml file. Each definition specifies agent name and their initial system prompt. At run-time, these prompts
are augmented with additional information. The leader's prompt is extended with the names and system prompts of all the other agent prompts. Furthermore,
the leader's prompt is extended with additional instructions depending on whether the agent the leader is currently invoking is allowed or not to delegate it's task to tother agents.
Lastly, the leader's definition includes instructions to determine at which stage it should terminate its interactions with other agents and consider the user requested as
completed. 

### Function definition

Currently, only functions are supported as tools for agents. All functions are defined in the functions.py file. They are also imported to
the agent_tem.py file. Functions must include their own documentations to enable agents to discover when and how to use them.

