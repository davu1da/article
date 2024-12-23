from django.conf import settings
from openai import OpenAI
import json
def parse_suggestions_to_json(suggestions_str):
    # 去除字符串两端的空白字符
    suggestions_str = suggestions_str.strip()
    # 使用换行符分割字符串
    suggestions_list = [line.strip() for line in suggestions_str.split('\n') if line.strip()]
    
    # 初始化一个空列表来存储建议
    suggestions = []
    for suggestion in suggestions_list:
        # 尝试使用多种分隔符分割序号和建议内容
        parts = suggestion.split('. ', 1)
        if len(parts) == 2:
            suggestions.append(parts[1].strip())
        else:
            # 如果没有找到合适的分隔符，直接添加整个行作为建议
            suggestions.append(suggestion.strip())
    
    # 将列表转换为JSON格式
    return json.dumps(suggestions, ensure_ascii=False)

default_suggust = parse_suggestions_to_json("暂时无法获取搜索建议，请直接输入关键词进行搜索。") 
def get_search_suggestion(keyword=''):
    try:
        client = OpenAI(
            api_key = settings.KIMI_API_KEY,
            base_url = "https://api.moonshot.cn/v1",
        )
    except Exception as e:
        return "暂时无法获取搜索建议，请直接输入关键词进行搜索。" 
    
    if not keyword:
        # 默认的搜索建议提示
        system_message = "你是一个学术搜索助手，请给出一些学术文献搜索的建议。"
        user_message = "请给出3-5条简短的文献搜索建议，每条建议不超过20字。"
    else:
        system_message = "你是一个学术搜索助手，请根据用户的搜索关键词给出相关的搜索建议。"
        user_message = f"关键词是：{keyword}。请给出3-5条相关的搜索建议，每条建议不超过20字。"
    
    try:
        completion = client.chat.completions.create(
            model = "moonshot-v1-8k",
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature = 0.3,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "暂时无法获取搜索建议，请直接输入关键词进行搜索。" 
    
# def get_search_suggestion_2(request, keyword):
#     # # 提取suggestionurl中的q里面的内容参数，并提取出q中的内容
#     # keyword = suggestionurl.split('q=')[1]
#     # if keyword == '':
#     #     print('空')
#     # print(keyword)
#     # try:
#     #     client = OpenAI(
#     #         api_key = settings.KIMI_API_KEY,
#     #         base_url = "https://api.moonshot.cn/v1",
#     #     )
#     # except Exception as e:
#     #     return "暂时无法获取搜索建议，请直接输入关键词进行搜索。" 
    
#     # if not keyword:
#     #     # 默认的搜索建议提示
#     #     system_message = "你是一个学术搜索助手，请给出一些学术文献搜索的建议。"
#     #     user_message = "请给出3-5条简短的文献搜索建议，每条建议不超过20字。"
#     # else:
#     #     system_message = "你是一个学术搜索助手，请根据用户的搜索关键词给出相关的搜索建议。"
#     #     user_message = f"关键词是：{keyword}。请给出3-5条相关的搜索建议，每条建议不超过20字。"
    
#     # try:
#     #     completion = client.chat.completions.create(
#     #         model = "moonshot-v1-8k",
#     #         messages = [
#     #             {"role": "system", "content": system_message},
#     #             {"role": "user", "content": user_message}
#     #         ],
#     #         temperature = 0.3,
#     #     )
#     #     return completion.choices[0].message.content
#     # except Exception as e:
#     #     return "暂时无法获取搜索建议，请直接输入关键词进行搜索。" 
#     try:
#         client = OpenAI(
#             api_key = settings.KIMI_API_KEY,
#             base_url = "https://api.moonshot.cn/v1",
#         )
#     except Exception as e:
#         return default_suggust
    
#     if not keyword:
#         # 默认的搜索建议提示
#         system_message = "你是一个学术搜索助手，请给出一些学术文献搜索的建议。"
#         user_message = "请给出3-5条简短的文献搜索建议，每条建议不超过20字。"
#     else:
#         system_message = "你是一个学术搜索助手，请根据用户的搜索关键词给出相关的论文搜索建议。"
#         user_message = f"关键词是：{keyword}。请给出3-5条相关的搜索建议，每条建议不超过20字。"
    
#     try:
#         completion = client.chat.completions.create(
#             model = "moonshot-v1-8k",
#             messages = [
#                 {"role": "system", "content": system_message},
#                 {"role": "user", "content": user_message}
#             ],
#             temperature = 0.3,
#         )
#         print(completion.choices[0].message.content)
#         suggestions_str = completion.choices[0].message.content
#         return parse_suggestions_to_json(suggestions_str)
#     except Exception as e:
#         return default_suggust
    

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_search_suggestion_2(request, keyword):
    client = OpenAI(
        api_key=settings.KIMI_API_KEY,
        base_url="https://api.moonshot.cn/v1",
    )

    if not keyword:
        system_message = "你是一个学术搜索助手，请给出一些学术文献搜索的建议。"
        user_message = "请给出3-5条简短的文献搜索建议，每条建议不超过20字。"
    else:
        system_message = "你是一个学术搜索助手，请根据用户的搜索关键词给出相关的论文搜索建议。"
        user_message = f"关键词是：{keyword}。请给出3-5条相关的搜索建议，每条建议不超过20字。"

    try:
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            timeout=10  # 设置请求的超时时间为 10 秒
        )

        # 处理 completion 对象为类实例的情况
        if hasattr(completion, 'choices') and len(completion.choices) > 0:
            suggestions_str = completion.choices[0].message.content
        elif isinstance(completion, dict) and 'choices' in completion and len(completion['choices']) > 0:
            suggestions_str = completion['choices'][0]['message']['content']
        else:
            return JsonResponse({"suggestions": []}, status=500)

        # 解析建议内容
        suggestions_list = suggestions_str.strip().split('\n')
        suggestions = [{"suggestion": suggestion.strip()} for suggestion in suggestions_list]

        return JsonResponse({"suggestions": suggestions})
    except Exception as e:
        print(f"Error fetching search suggestions: {e}")
        return JsonResponse({"suggestions": []}, status=500)
# 示例用法
# if __name__ == '__main__':
#     suggestions_str = "1. 建议一\n2. 建议二\n3. 建议三"
#     json_suggestions = parse_suggestions_to_json(suggestions_str)
#     print(json_suggestions)