#!/usr/bin/env python
"""
创建GitHub仓库并推送代码
"""
import os
import subprocess
import requests

def create_github_repo(token, repo_name, description):
    """使用GitHub API创建仓库"""
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"GitHub仓库创建成功: {response.json()['html_url']}")
        return response.json()['clone_url']
    else:
        print(f"创建仓库失败: {response.status_code} - {response.text}")
        return None

def git_push(repo_url):
    """推送代码到GitHub"""
    try:
        # 添加远程仓库
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        
        # 添加所有文件
        subprocess.run(["git", "add", "."], check=True)
        
        # 提交
        subprocess.run(["git", "commit", "-m", "Initial commit - 600MW发电机组热力平衡项目"], check=True)
        
        # 推送到主分支
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        
        print("代码推送成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git操作失败: {e}")
        return False

if __name__ == "__main__":
    # GitHub Token - 请在使用前设置环境变量 GITHUB_TOKEN
    TOKEN = os.environ.get("GITHUB_TOKEN", "")
    REPO_NAME = "660mw-heat-balance"
    DESCRIPTION = "600MW发电机组热力平衡项目 - 热力系统仿真软件"
    
    print(f"尝试创建GitHub仓库: {REPO_NAME}")
    
    # 创建仓库
    repo_url = create_github_repo(TOKEN, REPO_NAME, DESCRIPTION)
    
    if repo_url:
        print(f"仓库URL: {repo_url}")
        # 推送代码
        git_push(repo_url)
    else:
        print("无法创建仓库，请手动在GitHub上创建后继续")
