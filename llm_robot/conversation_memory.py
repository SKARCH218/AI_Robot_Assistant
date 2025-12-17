import json
import os
from datetime import datetime
from typing import Dict, List, Any

class ConversationMemory:
    def __init__(self, memory_file: str = "memory_database.json"):
        self.memory_file = memory_file
        self.memory_data = self.load_memory()
    
    def load_memory(self) -> Dict[str, Any]:
        """메모리 데이터베이스를 로드합니다."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본 메모리 구조
        return {
            "user_preferences": {
                "communication_style": "friendly",
                "preferred_greetings": [],
                "favorite_movements": [],
                "learning_patterns": {}
            },
            "conversation_memory": {
                "topics_discussed": [],
                "user_feedback": [],
                "successful_interactions": [],
                "failed_interactions": []
            },
            "learning_insights": {
                "effective_responses": [],
                "movement_preferences": [],
                "conversation_patterns": []
            },
            "personality_traits": {
                "friendliness_level": 8,
                "helpfulness_level": 9,
                "playfulness_level": 7
            }
        }
    
    def save_memory(self):
        """메모리 데이터베이스를 저장합니다."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"메모리 저장 실패: {e}")
    
    def add_conversation(self, user_input: str, bot_response: str, interaction_type: str = "general"):
        """대화를 메모리에 추가합니다."""
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "bot_response": bot_response,
            "interaction_type": interaction_type
        }
        
        # 대화 패턴 학습
        self.memory_data["conversation_memory"]["topics_discussed"].append({
            "topic": self.extract_topic(user_input),
            "timestamp": datetime.now().isoformat(),
            "user_satisfaction": "unknown"
        })
        
        self.save_memory()
    
    def extract_topic(self, text: str) -> str:
        """텍스트에서 주제를 추출합니다."""
        movement_keywords = ["움직", "동작", "이동", "회전", "잡아", "놓아"]
        greeting_keywords = ["안녕", "반가", "만나서"]
        question_keywords = ["어떻게", "왜", "뭐", "언제"]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in movement_keywords):
            return "robot_control"
        elif any(keyword in text_lower for keyword in greeting_keywords):
            return "greeting"
        elif any(keyword in text_lower for keyword in question_keywords):
            return "question"
        else:
            return "general_chat"
    
    def add_feedback(self, user_input: str, feedback_type: str, details: str = ""):
        """사용자 피드백을 기록합니다."""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "feedback_type": feedback_type,  # positive, negative, neutral
            "details": details
        }
        
        self.memory_data["conversation_memory"]["user_feedback"].append(feedback_entry)
        
        # 성공/실패 인터랙션 분류
        if feedback_type == "positive":
            self.memory_data["conversation_memory"]["successful_interactions"].append(feedback_entry)
        elif feedback_type == "negative":
            self.memory_data["conversation_memory"]["failed_interactions"].append(feedback_entry)
        
        self.save_memory()
    
    def learn_from_interaction(self, user_input: str, bot_response: str, was_successful: bool):
        """인터랙션에서 학습합니다."""
        if was_successful:
            # 성공적인 응답 패턴 학습
            self.memory_data["learning_insights"]["effective_responses"].append({
                "user_pattern": user_input,
                "successful_response": bot_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # 성격 특성 향상
            if "😊" in bot_response or "친근" in user_input:
                self.memory_data["personality_traits"]["friendliness_level"] = min(10, 
                    self.memory_data["personality_traits"]["friendliness_level"] + 0.1)
        
        self.save_memory()
    
    def get_conversation_context(self, limit: int = 5) -> str:
        """최근 대화 맥락을 반환합니다."""
        topics = self.memory_data["conversation_memory"]["topics_discussed"][-limit:]
        effective_responses = self.memory_data["learning_insights"]["effective_responses"][-3:]
        
        context = []
        
        if topics:
            recent_topics = [t["topic"] for t in topics]
            context.append(f"최근 대화 주제: {', '.join(set(recent_topics))}")
        
        if effective_responses:
            context.append("효과적이었던 응답 패턴:")
            for resp in effective_responses[-2:]:
                context.append(f"- '{resp['user_pattern']}' → '{resp['successful_response'][:50]}...'")
        
        return "\n".join(context) if context else "이전 대화 기록이 없습니다."
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """사용자 선호도를 반환합니다."""
        return self.memory_data["user_preferences"]
    
    def update_personality(self, trait: str, adjustment: float):
        """성격 특성을 업데이트합니다."""
        if trait in self.memory_data["personality_traits"]:
            current = self.memory_data["personality_traits"][trait]
            self.memory_data["personality_traits"][trait] = max(0, min(10, current + adjustment))
            self.save_memory()
    
    def learn_custom_action(self, trigger_phrase: str, action_description: str, json_command: str):
        """사용자 정의 동작을 학습합니다."""
        if "custom_actions" not in self.memory_data:
            self.memory_data["custom_actions"] = {}
        
        self.memory_data["custom_actions"][trigger_phrase.lower()] = {
            "description": action_description,
            "json_command": json_command,
            "learned_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        self.save_memory()
    
    def get_custom_action(self, user_input: str) -> str:
        """사용자 입력에서 커스텀 동작을 찾습니다."""
        if "custom_actions" not in self.memory_data:
            return None
        
        user_input_lower = user_input.lower()
        for trigger, action_data in self.memory_data["custom_actions"].items():
            if trigger in user_input_lower:
                # 사용 횟수 증가
                action_data["usage_count"] += 1
                self.save_memory()
                return action_data["json_command"]
        
        return None
    
    def analyze_conversation_patterns(self) -> str:
        """대화 패턴을 분석하여 인사이트를 제공합니다."""
        feedback = self.memory_data["conversation_memory"]["user_feedback"]
        
        if not feedback:
            return "아직 충분한 피드백 데이터가 없습니다."
        
        positive_count = len([f for f in feedback if f["feedback_type"] == "positive"])
        negative_count = len([f for f in feedback if f["feedback_type"] == "negative"])
        total_count = len(feedback)
        
        success_rate = (positive_count / total_count * 100) if total_count > 0 else 0
        
        insights = [
            f"총 피드백: {total_count}개",
            f"성공률: {success_rate:.1f}%",
            f"긍정적 상호작용: {positive_count}개",
            f"개선이 필요한 상호작용: {negative_count}개"
        ]
        
        return "\n".join(insights)
