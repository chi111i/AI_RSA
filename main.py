import os
import json
import subprocess
import re
from openai import OpenAI
import sys

def write_and_run_code(code, filename='ai_run.py', timeout=60):
    # 写入代码到文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    
    # 检查语法是否正确
    try:
        compile(code, filename, 'exec')
    except SyntaxError as e:
        return False, str(e)
    
    # 运行代码并捕获输出
    try:
        result = subprocess.run(['myenv/bin/python', filename], capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        if result.returncode == 0:
            output = result.stdout
            # 检查输出是否为乱码
            if is_garbled(output):
                return False, f"解密结果为乱码: {output}"
            return True, output
        else:
            # 检查是否是缺少模块的错误
            if "ModuleNotFoundError" in result.stderr:
                missing_module = re.search(r"No module named '(\w+)'", result.stderr).group(1)
                print(f"\n检测到缺少模块：{missing_module}，正在安装...")
                install_result = subprocess.run(['myenv/bin/python', '-m', 'pip', 'install', missing_module], capture_output=True, text=True, encoding='utf-8')
                if install_result.returncode == 0:
                    print(f"\n模块 {missing_module} 安装成功，重新运行代码...")
                    return write_and_run_code(code, filename, timeout)
                else:
                    return False, f"模块 {missing_module} 安装失败：{install_result.stderr}"
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "运行超时"
    except Exception as e:
        return False, str(e)

def is_garbled(text):
    # 检查文本是否为乱码的简单逻辑
    # 这里假设如果文本中有超过一定比例的不可打印字符，则认为是乱码
    non_printable_ratio = len(re.findall(r'[^\x20-\x7E]', text)) / len(text)
    return non_printable_ratio > 0.1

def get_fixed_code(error_message, original_code):
    # 请求AI修复代码
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "你是一个CTF密码学专家。只返回代码，不要Markdown语法标记，不要解释。"
            },
            {
                "role": "user",
                "content": f"这段代码运行出错，错误信息是：{error_message}\n原代码：\n{original_code}\n请修复这段代码。只返回代码，不要Markdown语法标记。"
            }
        ],
        temperature=0.7,
        max_tokens=4000,
        model=model_name
    )
    response_content = response.choices[0].message.content

# 去掉 Markdown 语法标记
    response_content = response_content.replace("```python", "").replace("```", "").strip()

    return response_content

def run_rsa_ctf_tool(n=None, p=None, q=None, e=None, cipher_text=None, timeout=20):
    command = ['myenv/bin/python', 'RsaCtfTool/RsaCtfTool.py']
    
    if n:
        command.extend(['-n', str(n)])
    if p:
        command.extend(['-p', str(p)])
    if q:
        command.extend(['-q', str(q)])
    if e:
        command.extend(['-e', str(e)])
    if cipher_text:
        command.extend(['--decrypt', str(cipher_text)])
    
    print(f"\n运行 RsaCtfTool 命令：{' '.join(command)}")
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', timeout=timeout)
        if result.returncode == 0:
            return True, result.stdout + result.stderr
        return False, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "运行超时"
    except Exception as e:
        return False, str(e)

def get_rsa_parameters(requirement):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "你是一个CTF密码学专家,请从以下需求中提取 所有已知的RSA 参数(如n,e,c,p,q,n1,n2,q1,q2等等)。只返回 JSON 格式的数据,不要Markdown语法标记,不要解释。"
            },
            {
                "role": "user",
                "content": requirement
            }
        ],
        temperature=0.7,
        max_tokens=4000,
        model=model_name
    )
    return json.loads(response.choices[0].message.content)

def save_rsa_parameters(params, filename='rsa_params.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(params, f)

def read_rsa_parameters(filename='rsa_params.json'):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_rsa_parameters_to_txt(params, filename='data.txt'):
    with open(filename, 'w', encoding='utf-8') as f:
        for key, value in params.items():
            f.write(f"{key}={value}\n")

def run_ctf_rsa_tools(filename='data.txt', timeout=60):
    command = ['myenv/bin/python', 'CTFRSAtools/main.py', filename]
    print(f"\n运行 CTFRSAtools 命令：{' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "运行超时"
    except Exception as e:
        return False, str(e)

def run_rsacracker(filename='data.txt', timeout=60):
    command = ['/home/chi11i/.cargo/bin/rsacracker', '<', filename]
    print(f"\n运行 rsacracker 命令：{' '.join(command)}")
    try:
        result = subprocess.run(' '.join(command), shell=True, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "运行超时"
    except Exception as e:
        return False, str(e)

token = "AI_KEY"
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

def read_data_txt(filename='data.txt'):
    params = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            key, value = line.strip().split('=')
            params[key] = value
    return params

def parse_input_to_json(input_data):
    params = {}
    for line in input_data.strip().split('\n'):
        key, value = line.split('=')
        params[key.strip()] = value.strip()
    return params

def main():
    print("请输入内容，结束后按 Ctrl+D (Linux/Mac) 或 Ctrl+Z (Windows) 并回车：")
    requirement = sys.stdin.read()
    
    online_mode = True  # 默认在线模式

    try:
        if online_mode:
            # 提取并保存 RSA 参数
            rsa_params = get_rsa_parameters(requirement)
            save_rsa_parameters(rsa_params)
            save_rsa_parameters_to_txt(rsa_params)
            
            # 从文件中读取 RSA 参数
            rsa_params = read_rsa_parameters()
            
            # 提取所有已知的RSA参数
            n = rsa_params.get('n')
            p = rsa_params.get('p')
            q = rsa_params.get('q')
            e = rsa_params.get('e')
            cipher_text = rsa_params.get('c')
            
            # 调用 rsacracker 进行解密
            print("\n尝试使用 rsacracker 进行解密...")
            success, output = run_rsacracker()
            
            if success:
                print("\nrsacracker 运行成功！输出结果：")
                print(output)
            else:
                print(f"\nrsacracker 运行失败,错误信息：\n{output}")
            
            # 调用 CTFRSAtools 进行解密
            print("\n尝试使用 CTFRSAtools 进行解密...")
            success, output = run_ctf_rsa_tools()
            
            if success:
                print("\nCTFRSAtools 运行成功！输出结果：")
                print(output)
            else:
                print(f"\nCTFRSAtools 运行失败,错误信息：\n{output}")
            
            # 调用 RsaCtfTool 进行解密
            print("\n尝试使用 RsaCtfTool 进行解密...")
            success, output = run_rsa_ctf_tool(n, p, q, e, cipher_text)
            
            if success:
                print("\nRsaCtfTool 运行成功！输出结果：")
                print(output)
            else:
                print(f"\nRsaCtfTool 运行失败,错误信息：\n{output}")
            
            # 尝试使用 AI 生成的代码进行解密...
            print("\n尝试使用 AI 生成的代码进行解密...")
            
            try:
                # 生成初始代码
                response = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个CTF密码学专家,请根据需求生成可执行的Python代码。只返回代码,不要Markdown语法标记,不要解释。"
                        },
                        {
                            "role": "user",
                            "content": requirement
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    model=model_name
                )
                
                code = response.choices[0].message.content
                
                max_attempts = 5
                attempt = 1
                
                while attempt <= max_attempts:
                    print(f"\n尝试运行第 {attempt} 次...")
                    success, output = write_and_run_code(code)
                    
                    if success:
                        print("\n运行成功！输出结果：")
                        print(output)
                        break
                    else:
                        print(f"\n运行失败,错误信息：\n{output}")
                        if attempt < max_attempts:
                            print("\n正在修复代码...")
                            code = get_fixed_code(output, code)
                            attempt += 1
                        else:
                            print("\n达到最大尝试次数,无法修复代码。")
                            break
            except Exception as e:
                print(f"\nAI 连接失败, 错误信息：{str(e)}")
                online_mode = False  # 切换到离线模式
    except Exception as e:
        print(f"\nAI 连接失败, 错误信息：{str(e)}")
        online_mode = False  # 切换到离线模式

    if not online_mode:
        print("\n直接使用输入的数据作为参数...")
        rsa_params = parse_input_to_json(requirement)
        save_rsa_parameters(rsa_params)
        save_rsa_parameters_to_txt(rsa_params)
        
        n = rsa_params.get('n')
        p = rsa_params.get('p')
        q = rsa_params.get('q')
        e = rsa_params.get('e')
        cipher_text = rsa_params.get('c')
        
        # 调用 rsacracker 进行解密
        print("\n尝试使用 rsacracker 进行解密...")
        success, output = run_rsacracker()
        
        if success:
            print("\nrsacracker 运行成功！输出结果：")
            print(output)
        else:
            print(f"\nrsacracker 运行失败,错误信息：\n{output}")
        
        # 调用 CTFRSAtools 进行解密
        print("\n尝试使用 CTFRSAtools 进行解密...")
        success, output = run_ctf_rsa_tools()
        
        if success:
            print("\nCTFRSAtools 运行成功！输出结果：")
            print(output)
        else:
            print(f"\nCTFRSAtools 运行失败,错误信息：\n{output}")
        
        # 调用 RsaCtfTool 进行解密
        print("\n尝试使用 RsaCtfTool 进行解密...")
        success, output = run_rsa_ctf_tool(n, p, q, e, cipher_text)
        
        if success:
            print("\nRsaCtfTool 运行成功！输出结果：")
            print(output)
        else:
            print(f"\nRsaCtfTool 运行失败,错误信息：\n{output}")

if __name__ == "__main__":
    main()
