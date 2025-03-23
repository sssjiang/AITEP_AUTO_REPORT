# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with the Bing grounding tool from
    the Azure Agents service using a synchronous client.

USAGE:
    python sample_agents_bing_grounding.py

    Before running the sample:

    pip install azure-ai-projects azure-identity

    Set these environment variables with your own values:
    1) PROJECT_CONNECTION_STRING - The project connection string, as found in the overview page of your
       Azure AI Foundry project.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in 
       the "Models + endpoints" tab in your Azure AI Foundry project.
    3) BING_CONNECTION_NAME - The connection name of the Bing connection, as found in the 
       "Connected resources" tab in your Azure AI Foundry project.
"""
import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole, BingGroundingTool
from azure.identity import DefaultAzureCredential
from azure.identity import ClientSecretCredential
# 使用示例
import configparser
# 读取配置文件
config = configparser.ConfigParser()
config.read('api.ini')
print(config.sections())
client_id = config['azure']['client_id']
tenant_id = config['azure']['tenant_id']
value = config['azure']['value']
project_connet_string = config['azure']['project_connet_string']
# 去掉project_connet_string前后的引号
project_connet_string = project_connet_string[1:-1]

# 使用用户名和密码登录
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=value
)

project_client = AIProjectClient.from_connection_string(
    credential=credential,
    conn_str=project_connet_string
)

# [START create_agent_with_bing_grounding_tool]
bing_connection = project_client.connections.get(connection_name="groundsearch")


conn_id = bing_connection.id

print(conn_id)

# Initialize agent bing tool and add the connection id
bing = BingGroundingTool(connection_id=conn_id)

# Create agent with the bing tool and process assistant run
with project_client:
    agent = project_client.agents.create_agent(
        model="gpt-35-turbo",
        name="my-assistant",
        instructions="You are a helpful assistant",
        tools=bing.definitions,
        # headers={"x-ms-enable-preview": "true"},
    )
    # [END create_agent_with_bing_grounding_tool]

    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role=MessageRole.USER,
        content="dose Tioconazole can cause the human cancer toxicity, search in web?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Delete the assistant when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    # Print the Agent's response message with optional citation
    response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
        MessageRole.AGENT
    )
    if response_message:
        for text_message in response_message.text_messages:
            print(f"Agent response: {text_message.text.value}")
        for annotation in response_message.url_citation_annotations:
            print(f"URL Citation: [{annotation.url_citation.title}]({annotation.url_citation.url})")