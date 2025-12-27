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
    
    secrets_content = generate_streamlit_secrets(json_file)
    
    if secrets_content:
        # Luu vao file de tranh loi encoding
        output_file = "streamlit_secrets.toml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(secrets_content)
        
        print(f"[SUCCESS] Da tao file: {output_file}")
        print("")
        print("=" * 80)
        print("[HUONG DAN]:")
        print("=" * 80)
        print(f"1. Mo file '{output_file}' bang Notepad hoac VS Code")
        print("2. Copy TOAN BO noi dung trong file")
        print("3. Vao Streamlit Cloud -> App Settings -> Secrets")
        print("4. Paste noi dung vao va Save")
        print("")
        print("[LUU Y QUAN TRONG]:")
        print("- Copy TOAN BO noi dung tu [gcp_service_account] den het")
        print("- Dam bao private_key duoc boc trong \"\"\"...\"\"\"")
        print("- KHONG them hoac xoa bat ky ky tu nao")
        print("- Giu nguyen format cua private key")
        print("=" * 80)
    else:
        sys.exit(1)

