#!/usr/bin/env python3
"""
使用GitHub API上传项目文件到仓库
"""
import os
import base64
import requests
from pathlib import Path

GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"
REPO_OWNER = "JamesFeiPF"
REPO_NAME = "660mw-heat-balance"
REPO_BRANCH = "main"

def verify_token():
    """验证Token是否有效"""
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"✓ Token验证成功！用户: {user.get('login', 'Unknown')}")
        return True
    else:
        print(f"✗ Token验证失败: {response.status_code} - {response.text}")
        return False

def check_repo_exists():
    """检查仓库是否存在"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"✓ 仓库已存在: https://github.com/{REPO_OWNER}/{REPO_NAME}")
        return True
    elif response.status_code == 404:
        print(f"✗ 仓库不存在，需要创建")
        return False
    else:
        print(f"✗ 检查仓库失败: {response.status_code}")
        return False

def get_file_sha(path):
    """获取文件在GitHub上的SHA值（如果存在）"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers, params={"ref": REPO_BRANCH})
    if response.status_code == 200:
        return response.json().get('sha')
    return None

def upload_file(file_path, repo_path):
    """上传单个文件到GitHub"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{repo_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"  ✗ 读取文件失败 {file_path}: {e}")
        return False

    data = {
        "message": f"Add {repo_path}",
        "content": content,
        "branch": REPO_BRANCH
    }

    sha = get_file_sha(repo_path)
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        return True
    else:
        print(f"  ✗ 上传失败 {repo_path}: {response.status_code} - {response.text[:200]}")
        return False

def upload_directory(local_dir, repo_path="", exclude_dirs=None):
    """递归上传目录"""
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', '.env'}

    success_count = 0
    fail_count = 0

    for root, dirs, files in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file in exclude_dirs:
                continue

            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            repo_file_path = os.path.join(repo_path, relative_path).replace(os.sep, '/')

            print(f"上传: {repo_file_path}", end=" ... ")
            if upload_file(local_path, repo_file_path):
                print("✓")
                success_count += 1
            else:
                print("✗")
                fail_count += 1

    return success_count, fail_count

def create_initial_commit():
    """创建初始提交（如果需要）"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/README.md"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    content = base64.b64encode("# 660MW Heat Balance\n\n600MW发电机组热力平衡项目\n".encode()).decode('utf-8')

    data = {
        "message": "Initial commit - 600MW发电机组热力平衡项目",
        "content": content,
        "branch": REPO_BRANCH
    }

    response = requests.put(url, headers=headers, json=data)
    return response.status_code in [200, 201]

def main():
    print("=" * 60)
    print("GitHub 文件上传工具")
    print("=" * 60)

    # 1. 验证Token
    print("\n[1/4] 验证GitHub Token...")
    if not verify_token():
        return

    # 2. 检查仓库
    print("\n[2/4] 检查目标仓库...")
    repo_exists = check_repo_exists()

    # 3. 上传文件
    print("\n[3/4] 上传项目文件...")

    project_root = Path(__file__).parent
    total_success = 0
    total_fail = 0

    # 上传根目录文件
    print("\n  上传根目录文件...")
    for item in os.listdir(project_root):
        item_path = project_root / item
        if item_path.is_file() and item not in ['create_github_repo.py', '.gitignore']:
            print(f"  上传: {item}", end=" ... ")
            if upload_file(str(item_path), item):
                print("✓")
                total_success += 1
            else:
                print("✗")
                total_fail += 1

    # 上传后端代码
    print("\n  上传后端代码 (mhflow_backend/)...")
    backend_path = project_root / "mhflow_backend"
    if backend_path.exists():
        success, fail = upload_directory(backend_path, "mhflow_backend")
        total_success += success
        total_fail += fail

    # 上传前端代码
    print("\n  上传前端代码 (mhflow_frontend/)...")
    frontend_path = project_root / "mhflow_frontend"
    if frontend_path.exists():
        success, fail = upload_directory(frontend_path, "mhflow_frontend")
        total_success += success
        total_fail += fail

    # 4. 验证结果
    print("\n[4/4] 上传完成！")
    print(f"\n{'=' * 60}")
    print(f"总计: 成功 {total_success} 个文件, 失败 {total_fail} 个文件")
    print(f"仓库地址: https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
