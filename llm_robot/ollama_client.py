import requests
import base64
import tempfile
import os

class OllamaClient:
    def __init__(self, model: str = "gemma3:1b", host: str = "http://127.0.0.1:11434"):
        self.model = model
        self.base_url = host.rstrip("/")

    def send_message(self, text: str) -> str:
        try:
            # Use generate API for simple prompt-response (non-stream)
            url = f"{self.base_url}/api/generate"
            payload = {"model": self.model, "prompt": text, "stream": False}
            r = requests.post(url, json=payload, timeout=120)  # 타임아웃을 120초로 증가
            r.raise_for_status()
            data = r.json()
            return data.get("response", "")
        except Exception as e:
            return f"Error (ollama): {e}"

    def send_message_with_image(self, text: str, image_b64: str) -> str:
        """Gemma3의 이미지 경로 태그 기능을 활용한 멀티모달 처리"""
        try:
            # base64 이미지를 임시 파일로 저장
            image_data = base64.b64decode(image_b64)
            
            # 임시 디렉토리에 이미지 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_image_path = temp_file.name
            
            try:
                # Gemma3의 이미지 경로 태그를 사용한 프롬프트 생성
                image_prompt = f"""<image>{temp_image_path}</image>

{text}

위 이미지를 분석하고 사용자의 질문에 답해주세요."""
                
                # 일반 generate API 사용 (Gemma3는 이미지 경로 태그를 인식함)
                url = f"{self.base_url}/api/generate"
                payload = {
                    "model": self.model,
                    "prompt": image_prompt,
                    "stream": False
                }
                
                response = requests.post(url, json=payload, timeout=180)  # 3분 타임아웃
                response.raise_for_status()
                data = response.json()
                
                return data.get("response", "이미지 분석에 실패했습니다.")
                
            finally:
                # 임시 파일 정리
                try:
                    os.unlink(temp_image_path)
                except Exception:
                    pass  # 파일 삭제 실패는 무시
                    
        except Exception as e:
            print(f"Gemma3 멀티모달 처리 오류: {e}")
            # 실패 시 텍스트만 처리
            return self.send_message(text + "\n\n[참고: 이미지 처리 중 오류가 발생해 텍스트만 분석했습니다]")
