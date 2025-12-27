"""
Script để tạo nội dung Streamlit Secrets từ file Google Service Account JSON.
Chạy script này để tạo nội dung cần paste vào Streamlit Cloud Secrets.
"""

import json
import sys

def generate_streamlit_secrets(json_file_path):
    """
    Đọc file JSON và tạo format TOML cho Streamlit Secrets
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Tạo nội dung TOML
        toml_content = "[gcp_service_account]\n"
        
        for key, value in data.items():
            if key == "private_key":
                # Private key cần format đặc biệt với triple quotes
                toml_content += f'{key} = """{value}"""\n'
            else:
                # Các field khác dùng quotes đơn
                toml_content += f'{key} = "{value}"\n'
        
        return toml_content
    
    except FileNotFoundError:
        print(f"[ERROR] Khong tim thay file '{json_file_path}'")
        return None
    except json.JSONDecodeError:
        print(f"[ERROR] File '{json_file_path}' khong phai la JSON hop le")
        return None
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None

if __name__ == "__main__":
    # Tìm file JSON trong thư mục hiện tại
    import glob
    
    json_files = glob.glob("api-agent-*.json")
    
    if not json_files:
        print("[ERROR] Khong tim thay file api-agent-*.json trong thu muc hien tai")
        print("Vui long dam bao file credentials co trong thu muc nay.")
        sys.exit(1)
    
    json_file = json_files[0]
    print(f"[INFO] Dang doc file: {json_file}")
    print("=" * 80)
    
    secrets_content = generate_streamlit_secrets(json_file)
    
    if secrets_content:
        print("\n[SUCCESS] Noi dung Streamlit Secrets (copy toan bo phan duoi day):")
        print("=" * 80)
        print(secrets_content)
        print("=" * 80)
        print("\n[HUONG DAN]:")
        print("1. Copy toan bo noi dung tu [gcp_service_account] den het")
        print("2. Vao Streamlit Cloud -> App Settings -> Secrets")
        print("3. Paste noi dung vao va Save")
        print("\n[LUU Y]:")
        print("- Dam bao private_key duoc boc trong \"\"\"...\"\"\"")
        print("- Khong them hoac xoa bat ky ky tu nao")
        print("- Giu nguyen format cua private key")
    else:
        sys.exit(1)

