from flask import Flask, request, render_template, jsonify
import atexit
import os
import json
import re
import datetime
import subprocess
import time
from gemini_client import GeminiClient
from apikey import GEMINI_API_KEY
from ollama_client import OllamaClient
from conversation_memory import ConversationMemory

# 옵션: vision, AIType
vision = False  # 이미지 입력 기능 활성화 여부
AIType = "gemini"  # "gemini" 또는 "chatgpt" 또는 "ollama"
Ollama = "gemma3:1b"

app = Flask(__name__)

# 대화 메모리 초기화
conversation_memory = ConversationMemory()

# Ollama 서버 시작 함수
def ensure_ollama_running():
    """Ollama 서버가 실행 중인지 확인하고, 아니면 시작합니다."""
    try:
        import requests
        # Ollama 서버 상태 체크
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("Ollama 서버가 이미 실행 중입니다.")
            return True
    except:
        pass
    
    try:
        print("Ollama 서버를 시작합니다...")
        # Ollama 서버를 백그라운드에서 시작
        subprocess.Popen(["ollama", "serve"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        # 서버 시작 대기
        time.sleep(3)
        
        # 다시 확인
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("Ollama 서버가 성공적으로 시작되었습니다.")
            return True
    except Exception as e:
        print(f"Ollama 서버 시작 실패: {e}")
    
    return False

# 동작 재실행 API: 최근 json 명령을 다시 실행
@app.route('/replay', methods=['POST'])
def replay_last_json():
    json_log_path = 'json_command_log.json'
    try:
        if not os.path.exists(json_log_path):
            return jsonify({'error': 'No command log'}), 400
        with open(json_log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        if not logs:
            return jsonify({'error': 'No command log'}), 400
        last = logs[-1]['json'] if 'json' in logs[-1] else None
        if not last:
            return jsonify({'error': 'No valid json'}), 400
        import json as jsonlib
        angles_data = jsonlib.loads(last)
        from dofbot_control import set_servo_angles
        import time
        if isinstance(angles_data, list):
            for step in angles_data:
                delay = step.pop('delay', None)
                set_servo_angles(jsonlib.dumps(step))
                if delay:
                    time.sleep(delay/1000.0)
        else:
            set_servo_angles(jsonlib.dumps(angles_data))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 긴급정지 API: 동작 중인 로봇을 즉시 멈춤
@app.route('/emergency_stop', methods=['POST'])
def emergency_stop():
    try:
        # 긴급정지를 별도 스레드에서 즉시 실행해 응답을 지연시키지 않음
        import threading
        from dofbot_control import emergency_stop as dofb_emergency_stop

        def _run_stop():
            try:
                dofb_emergency_stop()
            except Exception as _:
                # 백그라운드 예외는 무시 (로그만 필요 시 추가)
                pass

        threading.Thread(target=_run_stop, daemon=True).start()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 대화내역지우기 API: 경험 로그 삭제
@app.route('/clear_log', methods=['POST'])
def clear_log():
    log_path = 'experience_log.json'
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 옵션: vision, AIType
if AIType == "gemini":
    from gemini_client import GeminiClient
    from apikey import GEMINI_API_KEY
    ai_client = GeminiClient(GEMINI_API_KEY)
elif AIType == "chatgpt":
    from chatgpt_client import ChatGPTClient
    from apikey import OPENAI_API_KEY
    ai_client = ChatGPTClient(OPENAI_API_KEY)
elif AIType == "ollama":
    from ollama_client import OllamaClient
    ai_client = OllamaClient(model=Ollama)

# # 요청마다 접속 IP 출력
# @app.before_request
# def log_remote_addr():
#     ip = request.remote_addr
#     print(f"접속 IP: {ip}")

# 각도 수동 변경 API
@app.route('/angles', methods=['PATCH'])
def update_angles():
    try:
        data = request.get_json()
        # 예: {"motor": "base", "angle": 90}
        motor = data.get('motor')
        angle = data.get('angle')
        if motor not in ['base','motor1','motor2','motor3','grip_rotate','grip']:
            return jsonify({'error': 'Invalid motor'}), 400
        if not isinstance(angle, int) or not (0 <= angle <= 180):
            return jsonify({'error': 'Invalid angle'}), 400
        from dofbot_control import get_servo_angles, set_servo_angles
        angles = get_servo_angles()
        if angles is None:
            return jsonify({'error': 'Failed to read angles'}), 500
        angles[motor] = angle
        import json as jsonlib
        set_servo_angles(jsonlib.dumps(angles))
        return jsonify({'success': True, 'angles': angles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# 홈 자세 복귀 API
@app.route('/home', methods=['POST'])
def go_home():
    try:
        from dofbot_control import move_to_home_pose, get_servo_angles
        move_to_home_pose()
        angles = get_servo_angles()
        return jsonify({'success': True, 'angles': angles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/angles')
def angles():
    try:
        from dofbot_control import get_servo_angles
        angles = get_servo_angles()
        # 콘솔 출력 제거 (AI 관련 로그만 남김)
        return json.dumps(angles), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({}), 200, {'Content-Type': 'application/json'}

@app.route('/', methods=['GET', 'POST'])
def chat():
    # 로그 기록
    log_path = 'experience_log.json'
    json_log_path = 'json_command_log.json'
    experience_log = []
    gemini_reply = ''
    prompt = ''
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            try:
                experience_log = json.load(f)
            except Exception:
                experience_log = []
    if request.method == 'POST':
        prompt = request.form.get('prompt', '').strip()
        
        # 빈 입력 또는 너무 짧은 입력 처리
        if not prompt or len(prompt.strip()) == 0:
            return render_template('chat.html', messages=experience_log[-20:] if experience_log else [])
        
        # 너무 짧은 입력에 대한 처리 (1-2글자)
        if len(prompt.strip()) <= 2:
            short_responses = {
                '돼': '네! 알겠습니다! 😊',
                '줘': '무엇을 해드릴까요? 🤔',
                '해': '어떤 동작을 원하시나요? 😊',
                '응': '네! 😊',
                '아': '어떻게 도와드릴까요? 🤔'
            }
            if prompt.strip() in short_responses:
                ai_reply = short_responses[prompt.strip()]
                # 경험 로그에 저장하고 바로 반환
                experience_log.append({'role': 'user', 'content': prompt})
                experience_log.append({'role': 'bot', 'content': ai_reply})
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(experience_log, f, ensure_ascii=False, indent=2)
                return render_template('chat.html', messages=experience_log[-20:] if experience_log else [])
        
        keywords = ['움직여', '이동', '회전', '잡아', '놓아', '각도', '동작', '연속', 'delay', '천천히', '빠르게']
        home_keywords = ['홈자세', '원위치', '초기화', '기본자세']
        # 프롬프트 파일에서 system_prompt 읽기
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        # feedback_history, current_angles 치환 (예시)
        def safe_feedback(m):
            if isinstance(m, dict):
                role = m.get('role', 'user')
                content = m.get('content', str(m))
                return f"{role}: {content}"
            return str(m)
        # 메모리 기반 대화 맥락 구성
        conversation_context = conversation_memory.get_conversation_context()
        user_preferences = conversation_memory.get_user_preferences()
        personality = conversation_memory.memory_data["personality_traits"]
        
        # 피드백 히스토리를 최근 3개로 제한하고 중복 제거
        recent_feedback = []
        for m in experience_log[-3:]:
            feedback_str = safe_feedback(m)
            if feedback_str not in recent_feedback:
                recent_feedback.append(feedback_str)
        feedback_history = '\n'.join(recent_feedback) if recent_feedback else "없음"
        
        # 실제 각도 정보 가져오기
        try:
            from dofbot_control import get_servo_angles
            current_angles = get_servo_angles()
            if current_angles:
                angle_str = f"base:{current_angles.get('base', 90)}, motor1:{current_angles.get('motor1', 90)}, motor2:{current_angles.get('motor2', 90)}, motor3:{current_angles.get('motor3', 90)}, grip_rotate:{current_angles.get('grip_rotate', 90)}, grip:{current_angles.get('grip', 90)}"
            else:
                angle_str = "각도 정보를 가져올 수 없음"
        except:
            angle_str = "각도 정보를 가져올 수 없음"
        
        # 메모리 기반 정보를 시스템 프롬프트에 추가
        enhanced_feedback = f"""
기본 피드백: {feedback_history}

=== 학습된 대화 맥락 ===
{conversation_context}

=== 성격 특성 ===
친근함: {personality['friendliness_level']}/10
도움정도: {personality['helpfulness_level']}/10  
장난기: {personality['playfulness_level']}/10

=== 사용자 선호도 ===
소통 스타일: {user_preferences['communication_style']}
"""
        
        system_prompt = system_prompt.replace('{feedback_history}', enhanced_feedback)
        system_prompt = system_prompt.replace('{current_angles}', angle_str)
        
        # 사용자 정의 동작 학습 및 실행 체크
        # 입력 전처리: 공백 정리, 특수문자 처리
        cleaned_prompt = prompt.strip().replace(',', ' ').replace('?', '').replace('!', '')
        user_input_lower = cleaned_prompt.lower()
        
        # 이미지 관련 질문 감지
        vision_keywords = [
            '뭐가 보여', '뭐 보여', '뭐가보여', '뭐보여',
            '이미지', '사진', '그림', '화면',
            '앞에 뭐', '뭐가 있어', '보이는게', '보이는 것',
            '카메라', '시각', '눈으로', '보다', '관찰',
            '분석해줘', '설명해줘', '묘사해줘'
        ]
        
        is_vision_request = any(keyword in user_input_lower for keyword in vision_keywords)
        
        # vision이 비활성화된 상태에서 이미지 관련 질문이 들어올 경우
        if is_vision_request and not vision:
            ai_reply = "죄송해요, 현재 이미지를 볼 수 있는 기능이 비활성화되어 있어요. 😅 시각적인 정보는 제공드릴 수 없지만, 다른 질문이나 동작 명령은 도와드릴 수 있어요! 🤖"
        
        # 동작 정의 학습 패턴 감지 (예: "인사해달라고 하면 motor2를 45도...")
        elif "해달라고 하면" in user_input_lower or "하라고 하면" in user_input_lower:
            # 커스텀 동작 학습 로직
            parts = user_input_lower.split("하면")
            if len(parts) >= 2:
                trigger = parts[0].replace("해달라고", "").replace("하라고", "").strip()
                action_desc = parts[1].strip()
                
                if "motor" in action_desc:
                    # 간단한 동작 정의 (추후 더 정교하게 개선 가능)
                    if "motor2" in action_desc and "45" in action_desc:
                        json_cmd = '[{"base":90, "motor1":91, "motor2":45, "motor3":91, "grip_rotate":89, "grip":167, "delay":1000}, {"base":90, "motor1":91, "motor2":91, "motor3":91, "grip_rotate":89, "grip":167, "delay":500}]'
                        conversation_memory.learn_custom_action(trigger.strip(), action_desc, json_cmd)
        
        # 기본 인사 동작을 메모리에 미리 저장 (한 번만 실행)
        if not conversation_memory.get_custom_action("인사"):
            greeting_action = '[{"base":90, "motor1":91, "motor2":45, "motor3":91, "grip_rotate":89, "grip":167, "delay":1000}, {"base":90, "motor1":91, "motor2":91, "motor3":91, "grip_rotate":89, "grip":167, "delay":500}]'
            conversation_memory.learn_custom_action("인사", "motor2를 45도로 기울였다가 홈자세로 복귀", greeting_action)
        
        # 복합 명령 파싱 (연속, 반복 등)
        def parse_complex_command(input_text):
            """복합 명령을 파싱하여 JSON 배열을 생성합니다."""
            input_lower = input_text.lower()
            
            # 연속/반복 패턴 감지
            repeat_count = 1
            base_action = None
            
            # 숫자 추출 (두번, 세번, 2번, 3번 등)
            import re
            number_patterns = {
                '두번': 2, '세번': 3, '네번': 4, '다섯번': 5,
                '2번': 2, '3번': 3, '4번': 4, '5번': 5,
                '두 번': 2, '세 번': 3, '네 번': 4, '다섯 번': 5
            }
            
            for pattern, count in number_patterns.items():
                if pattern in input_lower:
                    repeat_count = count
                    break
            
            # 기본 동작 식별
            if '인사' in input_lower:
                base_action = {"base":90, "motor1":91, "motor2":45, "motor3":91, "grip_rotate":89, "grip":167, "delay":1000}
                home_action = {"base":90, "motor1":91, "motor2":91, "motor3":91, "grip_rotate":89, "grip":167, "delay":500}
                
                # 연속 인사 동작 생성
                actions = []
                for i in range(repeat_count):
                    actions.append(base_action.copy())
                    if i < repeat_count - 1:  # 마지막이 아니면 짧은 대기
                        actions.append({"base":90, "motor1":91, "motor2":91, "motor3":91, "grip_rotate":89, "grip":167, "delay":300})
                    else:  # 마지막엔 홈으로 복귀
                        actions.append(home_action.copy())
                
                return json.dumps(actions)
            
            return None
        
        # 복합 명령 먼저 체크
        complex_action = parse_complex_command(cleaned_prompt)
        
        if complex_action:
            # 복합 명령 실행
            if '두번' in user_input_lower or '2번' in user_input_lower:
                ai_reply = f"네! 연속으로 두 번 인사할게요! 👋👋\n\n{complex_action}"
            elif '세번' in user_input_lower or '3번' in user_input_lower:
                ai_reply = f"네! 연속으로 세 번 인사할게요! 👋👋👋\n\n{complex_action}"
            else:
                ai_reply = f"네! 연속으로 인사할게요! 👋\n\n{complex_action}"
        else:
            # 기본 커스텀 동작 실행 체크
            custom_action = conversation_memory.get_custom_action(cleaned_prompt)
            
            # 단순 인사 키워드 특별 처리
            greeting_keywords = ['인사해줄래', '인사해줘', '인사해봐', '인사 해줘', '인사 해봐']
            is_simple_greeting = any(keyword in user_input_lower for keyword in greeting_keywords) and not any(x in user_input_lower for x in ['연속', '두번', '세번', '반복'])
            
            if is_simple_greeting or custom_action:
                if is_simple_greeting:
                    # 단순 인사 동작 실행
                    greeting_action = '[{"base":90, "motor1":91, "motor2":45, "motor3":91, "grip_rotate":89, "grip":167, "delay":1000}, {"base":90, "motor1":91, "motor2":91, "motor3":91, "grip_rotate":89, "grip":167, "delay":500}]'
                    ai_reply = f"네! 인사할게요! 👋\n\n{greeting_action}"
                else:
                    # 커스텀 동작이 있으면 바로 실행
                    ai_reply = f"네! 명령을 실행할게요! 👋\n\n{custom_action}"
            else:
                # vision 옵션에 따라 이미지 입력 기능 활성화
                image_data = None
                if vision and 'image' in request.files:
                    image_file = request.files['image']
                    image_data = image_file.read()
                    import base64
                    image_b64 = base64.b64encode(image_data).decode('utf-8')
                    
                    # 이미지 관련 질문에 대한 더 적절한 프롬프트 생성
                    if is_vision_request:
                        enhanced_prompt = f"""사용자가 이미지에 대해 질문했습니다: "{prompt}"

이미지를 자세히 분석하고 다음 사항들을 포함하여 답변해주세요:
- 이미지에 보이는 주요 객체들
- 색상, 모양, 위치 등의 시각적 특징
- 전체적인 장면이나 상황
- 사용자의 질문에 직접적으로 답변

친근하고 자세하게 설명해주세요."""
                        final_prompt = enhanced_prompt
                    else:
                        final_prompt = system_prompt + "\n\n" + prompt
                    
                    # AI 클라이언트 호출
                    if AIType == "gemini":
                        ai_reply = ai_client.send_message_with_image(final_prompt, image_b64)
                    elif AIType == "chatgpt":
                        ai_reply = ai_client.send_message(system_prompt + "\n\n" + prompt)  # ChatGPT는 텍스트만 지원
                    elif AIType == "ollama":
                        ai_reply = ai_client.send_message_with_image(final_prompt, image_b64)  # Gemma3 이미지 처리
                    else:
                        ai_reply = "지원하지 않는 AIType입니다."
                        
                elif vision and is_vision_request:
                    # 이미지가 없지만 이미지 관련 질문인 경우
                    ai_reply = "이미지를 분석하려면 사진을 업로드해주세요! 📸 파일 선택 버튼을 클릭하여 이미지를 첨부하면 자세히 분석해드릴게요! 😊"
                else:
                    # 일반 텍스트 대화
                    if AIType == "gemini":
                        ai_reply = ai_client.send_message(system_prompt + "\n\n" + prompt)
                    elif AIType == "chatgpt":
                        ai_reply = ai_client.send_message(system_prompt + "\n\n" + prompt)
                    elif AIType == "ollama":
                        ai_reply = ai_client.send_message(system_prompt + "\n\n" + prompt)
                    else:
                        ai_reply = "지원하지 않는 AIType입니다."
        import re
        import datetime
        # 대화를 메모리에 저장 (성공/실패 판단)
        interaction_successful = 'Error' not in ai_reply and ai_reply.strip() != ""
        
        # Gemini/ChatGPT API quota 초과 안내
        if 'Error: 429' in ai_reply or 'quota' in ai_reply:
            reply_text = 'AI api 이용량 초과. 잠시 후 다시 시도해 주세요.'
            angles_json = None
            interaction_successful = False
        else:
            # JSON 배열만 추출
            json_match = re.search(r'(\[.*?\])', ai_reply, re.DOTALL)
            angles_json = None
            if json_match:
                angles_json = json_match.group(0)
                # JSON 명령 로그 저장
                entry = {
                    'timestamp': str(datetime.datetime.now()),
                    'json': angles_json
                }
                if os.path.exists(json_log_path):
                    with open(json_log_path, 'r', encoding='utf-8') as f:
                        try:
                            json_log = json.load(f)
                        except Exception:
                            json_log = []
                else:
                    json_log = []
                json_log.append(entry)
                with open(json_log_path, 'w', encoding='utf-8') as f:
                    json.dump(json_log, f, ensure_ascii=False, indent=2)
                # 실제 DOFBOT 동작 함수 호출 (예시)
                try:
                    import json as jsonlib
                    angles_data = jsonlib.loads(angles_json)
                    from dofbot_control import set_servo_angles
                    # 연속 동작 지원: 배열이면 순차 실행
                    import time
                    if isinstance(angles_data, list):
                        for step in angles_data:
                            delay = step.pop('delay', None)
                            set_servo_angles(jsonlib.dumps(step))
                            if delay:
                                time.sleep(delay/1000.0)
                    else:
                        set_servo_angles(jsonlib.dumps(angles_data))
                except Exception as e:
                    print(f"DOFBOT 제어 오류: {e}")
            # 자연어 답변만 추출 (JSON, 배열, 코드블록, 중괄호, 대괄호 등 모두 제거)
            reply_text = re.sub(r'```json[\s\S]*?```', '', ai_reply)
            reply_text = re.sub(r'```[\s\S]*?```', '', reply_text)
            reply_text = re.sub(r'\{[\s\S]*?\}', '', reply_text)
            reply_text = re.sub(r'(\[.*?\])', '', reply_text)
            reply_text = re.sub(r'DOFBOT:\s*', '', reply_text)
            # 추가: 대괄호로 시작하는 줄 전체 제거
            reply_text = re.sub(r'^\s*\[.*?\]\s*$', '', reply_text, flags=re.MULTILINE)
            # 추가: 남아있는 대괄호 포함 문자열 제거
            reply_text = re.sub(r'\[.*?\]', '', reply_text)
            reply_text = reply_text.strip()
        # 경험 로그 저장
        experience_log.append({
            'role': 'user',
            'content': prompt
        })
        experience_log.append({
            'role': 'bot',
            'content': reply_text
        })
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(experience_log, f, ensure_ascii=False, indent=2)
        
        # 대화 메모리에 저장 및 학습
        interaction_type = "robot_control" if angles_json else "general_chat"
        conversation_memory.add_conversation(prompt, reply_text, interaction_type)
        conversation_memory.learn_from_interaction(prompt, reply_text, interaction_successful)
        
        # 사용자 반응 예측 및 성격 조정
        if any(keyword in prompt.lower() for keyword in ["좋아", "고마워", "잘했어", "멋져"]):
            conversation_memory.add_feedback(prompt, "positive", "사용자가 긍정적 반응을 보임")
            conversation_memory.update_personality("friendliness_level", 0.1)
        elif any(keyword in prompt.lower() for keyword in ["싫어", "별로", "안돼", "틀렸어"]):
            conversation_memory.add_feedback(prompt, "negative", "사용자가 부정적 반응을 보임")
            conversation_memory.update_personality("helpfulness_level", 0.1)
    # 채팅 메시지 렌더링
    messages = experience_log[-20:] if experience_log else []
    return render_template('chat.html', messages=messages, vision_enabled=vision)

# 메모리 상태 확인 API
@app.route('/memory_status', methods=['GET'])
def memory_status():
    try:
        memory_data = conversation_memory.memory_data
        analysis = conversation_memory.analyze_conversation_patterns()
        
        return jsonify({
            'success': True,
            'personality_traits': memory_data['personality_traits'],
            'conversation_analysis': analysis,
            'total_conversations': len(memory_data['conversation_memory']['topics_discussed']),
            'user_preferences': memory_data['user_preferences'],
            'recent_context': conversation_memory.get_conversation_context()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 메모리 리셋 API
@app.route('/reset_memory', methods=['POST'])
def reset_memory():
    try:
        conversation_memory.memory_data = conversation_memory.load_memory()
        conversation_memory.save_memory()
        return jsonify({'success': True, 'message': '메모리가 초기화되었습니다.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    
    # Ollama 타입인 경우 서버 확인 및 시작
    if AIType == "ollama":
        ensure_ollama_running()
    
    # 프로그램 시작 시 홈 자세 복귀
    try:
        from dofbot_control import move_to_home_pose
        move_to_home_pose()
        print("프로그램 시작: DOFBOT 홈 자세로 복귀 완료")
    except Exception as e:
        print(f"홈 자세 이동 실패: {e}")
    # 웹 접속 주소 안내
    from ip_utils import get_ip_addresses
    ips = get_ip_addresses()
    print("웹 접속 주소:")
    for ip in ips:
        if ip != '127.0.0.1' and not ip.startswith('127.'):
            print(f"  http://{ip}:5000")
    if '127.0.0.1' in ips:
        print(f"  http://127.0.0.1:5000 (로컬호스트)")
    # 종료 시 홈 자세 복귀
    def on_exit():
        try:
            from dofbot_control import move_to_home_pose
            move_to_home_pose()
            print("프로그램 종료: DOFBOT 홈 자세로 복귀 완료")
        except Exception as e:
            print(f"종료시 홈 자세 이동 실패: {e}")
    atexit.register(on_exit)
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)