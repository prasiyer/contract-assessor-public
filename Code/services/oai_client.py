

from urllib import response
from openai import AzureOpenAI
import os
import pandas as pd
from datetime import datetime

from config import TOKEN_USAGE_FILE_PATH

from dotenv import load_dotenv
load_dotenv()

# Deployment options
oai_deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4.1-mini")
oai_deployment41 = os.getenv("DEPLOYMENT_NAME", "gpt-4.1")
oai_deployment_o4m = os.getenv("DEPLOYMENT_NAME", "o4-mini")

oai_deployment_emb3_small = os.getenv("DEPLOYMENT_NAME", "text-embedding-3-small")
oai_deployment_emb3_large = os.getenv("DEPLOYMENT_NAME", "text-embedding-3-large")

# api_version options
api_version = "2025-01-01-preview"
api_version_o4m = "2024-12-01-preview"
api_version_other = "2024-12-01-preview"


# api_key options
oai_key = os.getenv("AZURE_OPENAI_API_KEY")
oai_key_o4m = os.getenv("AZURE_OPENAI_O4M_API_KEY")

oai_key_text_embedding3 = os.getenv("AZURE_OPENAI_TEXT_EMBEDDING3_KEY")

# endpoint options
oai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
oai_endpoint_o4m = os.getenv("AZURE_OPENAI_O4M_ENDPOINT")

# model_id options -- gpt-4.1-mini, gpt-4.1, o4-mini
model_id = "gpt-4.1-mini"

# Aug-21: import the token_usage csv
# token_usage_file = "/home/vp899/projects/oai_pilot/oai_pilot/Output/oai_token_usage.csv"
token_usage_file = TOKEN_USAGE_FILE_PATH
token_usage_df = pd.read_csv(token_usage_file)

current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

class oai_client:
    def __init__(
        self,
        model_id: str = None,
    ):
        #self.oai_endpoint = oai_endpoint if oai_endpoint is not None else globals()["oai_endpoint"]
        #self.oai_api_key = oai_api_key if oai_api_key is not None else globals()["oai_api_key"]
        #self.oai_deployment = oai_deployment if oai_deployment is not None else globals()["oai_deployment"]
        #self.api_version = api_version if api_version is not None else globals()["api_version"]
        self.model_id = model_id if model_id is not None else globals()["model_id"]
        # model_id options -- gpt-4.1-mini, gpt-4.1, o4-mini
        if self.model_id == "o4-mini":
            self.oai_endpoint = oai_endpoint_o4m
            self.oai_api_key = oai_key_o4m
            self.oai_deployment = oai_deployment_o4m
            self.api_version = api_version_o4m
        # else if model_id contains embedding, then use oai_key_text_embedding3 as api_key, oai_deployment_emb3_large as deployment if model_id = text-embedding-3-large, api_version_other as api_version
        elif "embedding" in self.model_id:
            self.oai_endpoint = oai_endpoint
            self.oai_api_key = oai_key_text_embedding3
            if self.model_id == "text-embedding-3-small":
                self.oai_deployment = oai_deployment_emb3_small
            else:
                self.oai_deployment = oai_deployment_emb3_large
            self.api_version = api_version_other
        else:
            self.oai_endpoint = oai_endpoint
            self.oai_api_key = oai_key
            self.oai_deployment = oai_deployment
            self.api_version = api_version
        


        self.oai_azure_client = AzureOpenAI(azure_endpoint=self.oai_endpoint,api_key=self.oai_api_key, api_version=self.api_version,)

    ## get_client method is not needed as we are initializing the client in the constructor

    def get_client(self) -> AzureOpenAI:
        oai_client = AzureOpenAI(
            azure_endpoint=self.oai_endpoint,
            api_key=self.oai_api_key,
            # api_version="2025-01-01-preview",
            api_version=self.api_version,
        )
        return oai_client
    def get_response(self, oai_prompt: list, max_tokens_parameter = 1400 ) -> str:

        """
        Sends a request to the OpenAI API with the provided prompt and returns the response.

        Args:
            oai_prompt (list): A list of dictionaries representing the messages to be sent to the OpenAI API.
            max_tokens_parameter (int): The maximum number of tokens to generate in the response. Default is 1400.
        Returns:
            str: The content of the response from the OpenAI API.
            token_usage: The token usage information from the response.


        """

        if self.model_id == "o4-mini":
            oai_response = self.oai_azure_client.chat.completions.create(model = self.oai_deployment, messages= oai_prompt,)

        else:
            oai_response = self.oai_azure_client.chat.completions.create(
                model=self.oai_deployment,
                messages=oai_prompt,
                # max_tokens=1400,
                max_tokens=max_tokens_parameter,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )
        # Aug-21: Add tokens used to token usage df
        return oai_response.choices[0].message.content, oai_response.usage

    def get_response_with_token_tracking(self, oai_prompt: list, max_tokens_parameter = 1400, doc_name = "NA", doc_type = "NA", operation = "NA", page_number = -1, tools = None) -> str:
        """
        Sends a request to the OpenAI API with the provided prompt and returns the response.
        Args:
            oai_prompt (list): A list of dictionaries representing the messages to be sent to the OpenAI API.
            max_tokens_parameter (int): The maximum number of tokens to generate in the response. Default is 1400.
            doc_name (str): The name of the document being processed. Default is "NA".
            doc_type (str): The type of the document being processed. Default is "NA".
            operation (str): The operation being performed (e.g., "completion", "embedding"). Default is "NA".
            page_number (int): The page number of the document being processed. Default is -1.
        Returns:
            str: The content of the response from the OpenAI API.
            token_usage: The token usage information from the response.

        """
        

        if self.model_id == "o4-mini":
            oai_response = self.oai_azure_client.chat.completions.create(model = self.oai_deployment, messages= oai_prompt,)

        else:
            chat_completion_params = dict(
                model=self.oai_deployment,
                messages=oai_prompt,
                # max_tokens=1400,
                max_tokens=max_tokens_parameter,
                temperature=0.3,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,)
            if tools:
                chat_completion_params["tools"] = tools
                chat_completion_params["tool_choice"] = "auto"
            oai_response = self.oai_azure_client.chat.completions.create(**chat_completion_params)         
                
        # Aug-21: Add tokens used to token usage df
        token_usage = oai_response.usage
        token_usage_df.loc[len(token_usage_df)] = [current_time, doc_name, doc_type, operation, page_number, token_usage.prompt_tokens, token_usage.completion_tokens, token_usage.total_tokens, self.model_id]
        token_usage_df.to_csv(token_usage_file, index=False)

        # return oai_response.choices[0].message.content, oai_response.choices[0].message.tool_calls
        return oai_response.choices[0].message.content, token_usage, oai_response.choices[0].message.tool_calls

    def get_embedding(self, input_text, doc_name = "NA", doc_type = "NA", operation = "embedding", page_number = -1) -> list:
        embedding_response = self.oai_azure_client.embeddings.create(input=input_text, model=self.oai_deployment)
        #embedding_response = response.data[0].embedding
        # embedding_response = response
        for item in embedding_response.data:
            # print(f"Embedding for input {item.index}: {item.embedding[:5]}...")  # Print first 5 dimensions for brevity
            token_usage = embedding_response.usage
            token_usage_df.loc[len(token_usage_df)] = [current_time, doc_name, doc_type, operation, page_number, token_usage.prompt_tokens, 0, token_usage.total_tokens, self.model_id]
        token_usage_df.to_csv(token_usage_file, index=False)
        return embedding_response