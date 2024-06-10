import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

MAX_API_RETRY = 10
LLM_MIN_RETRY_SLEEP = 5
LLM_MAX_TOKENS = 4096
LLM_TEMPERATURE = 0.7

@retry(wait=wait_random_exponential(min=LLM_MIN_RETRY_SLEEP, max=60), stop=stop_after_attempt(MAX_API_RETRY))
def completion_with_backoff(client: openai.Client, **kwargs)-> openai.types.Completion:
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as e:
        print(e)

def chat_auto_complete(client: openai.Client, item: dict, model: str):
    message = [{"role": "system", "content": item['system']}]
    ans_info = []
    try:
        for prompt in item['prompts']:
            message.append({"role": "user", "content": prompt})
            answer = completion_with_backoff(client,
                                             messages=message,
                                             model=model,
                                             temperature=LLM_TEMPERATURE,
                                             max_tokens=LLM_MAX_TOKENS)
            ans_info.append(str(answer.usage))
            answer = answer.choices[0].message.content
            message.append({"role": "assistant", "content": str(answer)})
    except Exception as e:
        print(e)
        pass
    if len(message) == 1:
        return None, ans_info
    else:
        item['messages'] = message
        return item, ans_info