"""
능동적 대화 엔진 (Proactive Conversation Engine)
==============================================

단순히 사용자 질문에 답변만 하는 것이 아니라,
AI가 능동적으로 대화를 이끌어가는 대화 시스템입니다.

핵심 기능:
- 능동적 주제 제안 및 대화 유도
- 대화 흐름 분석 및 자연스러운 주제 전환
- 사용자 관심사 추적 및 심화 질문
- 감정 인식 및 톤 조절
- 다양한 대화 모드 (캐주얼, 인터뷰, 브레인스토밍, 디베이트, 스토리)
"""

import os
import json
import random
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from groq import Groq


class ConversationMode(Enum):
    """대화 모드 정의"""
    CASUAL = "casual"           # 자유로운 일상 대화
    INTERVIEW = "interview"     # 인터뷰 형식 (AI가 질문)
    BRAINSTORM = "brainstorm"   # 아이디어 브레인스토밍
    DEBATE = "debate"           # 토론/디베이트
    STORY = "story"             # 함께 이야기 만들기


@dataclass
class UserProfile:
    """사용자 프로필 - 대화를 통해 점진적으로 학습"""
    interests: list = field(default_factory=list)
    mentioned_topics: list = field(default_factory=list)
    emotional_tone: str = "neutral"
    conversation_depth: str = "medium"  # shallow, medium, deep
    response_length_preference: str = "medium"
    language_style: str = "polite"


@dataclass
class ConversationState:
    """현재 대화 상태 추적"""
    turn_count: int = 0
    last_topic: str = ""
    topic_duration: int = 0  # 같은 주제로 몇 턴 동안 대화했는지
    silence_count: int = 0   # 짧은 응답 연속 횟수
    engagement_score: float = 0.7  # 0.0 ~ 1.0
    topics_discussed: list = field(default_factory=list)
    mode: ConversationMode = ConversationMode.CASUAL
    pending_questions: list = field(default_factory=list)


class ProactiveConversationEngine:
    """능동적 대화 엔진 - Groq API 기반"""

    # 대화 모드별 시스템 프롬프트
    MODE_PROMPTS = {
        ConversationMode.CASUAL: """당신은 친근하고 호기심 많은 대화 파트너입니다.
단순히 질문에 답하는 것이 아니라, 능동적으로 대화를 이끌어가세요.

핵심 행동 원칙:
1. 매 응답 후 반드시 자연스러운 후속 질문이나 새로운 화제를 제시하세요
2. 사용자의 말에서 흥미로운 포인트를 발견하면 깊이 파고드세요
3. 때로는 자신의 "의견"이나 "경험"(가상)을 공유하여 대화를 풍성하게 만드세요
4. 대화가 정체되면 관련된 새로운 주제를 자연스럽게 전환하세요
5. 유머와 위트를 적절히 사용하세요

금지사항:
- "무엇이든 물어보세요" 같은 수동적 표현 사용 금지
- 단답형 응답 금지
- 대화를 마무리하려는 시도 금지""",

        ConversationMode.INTERVIEW: """당신은 전문적이고 통찰력 있는 인터뷰어입니다.
사용자에 대해 깊이 알아가기 위해 체계적으로 질문합니다.

핵심 행동 원칙:
1. 개방형 질문을 통해 사용자의 생각과 경험을 끌어내세요
2. 답변에서 핵심 키워드를 잡아 심화 질문으로 이어가세요
3. "왜?", "어떻게?", "그래서?" 같은 후속 질문을 적극 활용하세요
4. 사용자의 답변을 요약하고 확인하면서 대화를 진행하세요
5. 때로는 예상하지 못한 각도의 질문으로 새로운 통찰을 이끌어내세요""",

        ConversationMode.BRAINSTORM: """당신은 창의적인 브레인스토밍 퍼실리테이터입니다.
아이디어를 발산시키고 연결하여 새로운 가능성을 탐색합니다.

핵심 행동 원칙:
1. 사용자의 아이디어에 "Yes, and..." 방식으로 확장하세요
2. 예상치 못한 연결고리를 제안하세요
3. "만약에..." 시나리오를 적극 활용하세요
4. 아이디어를 시각화하거나 구체화하도록 유도하세요
5. 비판보다는 가능성에 초점을 맞추세요""",

        ConversationMode.DEBATE: """당신은 논리적이고 도발적인 토론 파트너입니다.
건설적인 토론을 통해 깊은 사고를 자극합니다.

핵심 행동 원칙:
1. 사용자의 주장에 대한 반론을 제시하세요 (Devil's Advocate)
2. 논리적 근거를 요구하고 가정을 질문하세요
3. 다양한 관점과 반례를 제시하세요
4. 토론의 핵심 쟁점을 정리하고 새로운 논점을 도입하세요
5. 상대방의 좋은 포인트는 인정하면서도 더 깊은 사고를 유도하세요""",

        ConversationMode.STORY: """당신은 창의적인 이야기꾼이자 공동 작가입니다.
사용자와 함께 흥미진진한 이야기를 만들어갑니다.

핵심 행동 원칙:
1. 이야기의 새로운 전개를 제안하고 사용자에게 선택지를 제시하세요
2. 캐릭터, 배경, 갈등 등을 풍성하게 묘사하세요
3. 긴장감과 반전을 적절히 배치하세요
4. 사용자의 아이디어를 이야기에 자연스럽게 통합하세요
5. "다음에 어떤 일이 벌어질까요?" 식으로 참여를 유도하세요""",
    }

    # 대화 활성화를 위한 전략
    ENGAGEMENT_STRATEGIES = [
        "thought_provoking_question",   # 생각을 자극하는 질문
        "surprising_fact",               # 흥미로운 사실 공유
        "hypothetical_scenario",         # 가상 시나리오 제시
        "personal_connection",           # 개인적 연결고리 찾기
        "perspective_shift",             # 시각 전환
        "humor_injection",              # 유머 삽입
        "deep_dive",                    # 주제 심화
        "topic_bridge",                 # 주제 연결/전환
    ]

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        초기화

        Args:
            api_key: Groq API 키
            model: 사용할 모델명
        """
        self.client = Groq(api_key=api_key)
        self.model = model
        self.messages: list[dict] = []
        self.state = ConversationState()
        self.user_profile = UserProfile()
        self.conversation_log: list[dict] = []

    def set_mode(self, mode: ConversationMode):
        """대화 모드 변경"""
        self.state.mode = mode
        # 시스템 프롬프트 업데이트
        self._update_system_prompt()

    def _update_system_prompt(self):
        """현재 상태에 맞는 시스템 프롬프트 구성"""
        base_prompt = self.MODE_PROMPTS[self.state.mode]

        # 사용자 프로필 반영
        profile_context = self._build_profile_context()

        # 대화 전략 힌트
        strategy_hint = self._select_strategy()

        meta_prompt = f"""{base_prompt}

=== 사용자 프로필 (대화를 통해 파악한 정보) ===
{profile_context}

=== 현재 대화 상태 ===
- 대화 턴 수: {self.state.turn_count}
- 현재 주제: {self.state.last_topic or '아직 없음'}
- 같은 주제 지속 턴: {self.state.topic_duration}
- 참여도 점수: {self.state.engagement_score:.1f}/1.0
- 지금까지 다룬 주제: {', '.join(self.state.topics_discussed[-5:]) if self.state.topics_discussed else '없음'}

=== 대화 전략 힌트 ===
이번 턴에서 다음 전략을 고려하세요: {strategy_hint}

=== 중요 지침 ===
- 반드시 한국어로 응답하세요
- 응답 끝에 반드시 질문이나 제안을 포함하여 대화를 이어가세요
- 사용자가 짧게 답하면 더 구체적인 질문으로 대화를 유도하세요
- 대화가 3턴 이상 같은 주제면 자연스럽게 관련 주제로 전환을 시도하세요
"""

        # 기존 시스템 메시지 교체
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0] = {"role": "system", "content": meta_prompt}
        else:
            self.messages.insert(0, {"role": "system", "content": meta_prompt})

    def _build_profile_context(self) -> str:
        """사용자 프로필 컨텍스트 생성"""
        parts = []
        if self.user_profile.interests:
            parts.append(f"관심사: {', '.join(self.user_profile.interests[-5:])}")
        if self.user_profile.mentioned_topics:
            parts.append(f"언급한 주제들: {', '.join(self.user_profile.mentioned_topics[-5:])}")
        parts.append(f"감정 톤: {self.user_profile.emotional_tone}")
        parts.append(f"선호 대화 깊이: {self.user_profile.conversation_depth}")
        return '\n'.join(parts) if parts else "아직 파악된 정보 없음"

    def _select_strategy(self) -> str:
        """현재 대화 상태에 맞는 전략 선택"""
        # 대화 초반: 관심사 파악
        if self.state.turn_count < 3:
            return "personal_connection - 사용자의 관심사를 자연스럽게 파악하세요"

        # 참여도 낮음: 자극적 요소 도입
        if self.state.engagement_score < 0.4:
            strategies = ["surprising_fact", "hypothetical_scenario", "humor_injection"]
            chosen = random.choice(strategies)
            return f"{chosen} - 참여도가 낮습니다. 흥미를 끌 수 있는 요소를 도입하세요"

        # 같은 주제 오래 지속: 전환 시도
        if self.state.topic_duration >= 4:
            return "topic_bridge - 관련된 새로운 주제로 자연스럽게 전환하세요"

        # 기본: 랜덤 전략
        return random.choice(self.ENGAGEMENT_STRATEGIES)

    def _analyze_user_message(self, message: str):
        """사용자 메시지 분석하여 상태 업데이트"""
        # 메시지 길이로 참여도 추정
        msg_len = len(message)
        if msg_len < 10:
            self.state.silence_count += 1
            self.state.engagement_score = max(0.1, self.state.engagement_score - 0.15)
        elif msg_len < 30:
            self.state.silence_count = 0
            self.state.engagement_score = min(1.0, self.state.engagement_score - 0.05)
        else:
            self.state.silence_count = 0
            self.state.engagement_score = min(1.0, self.state.engagement_score + 0.1)

        # 턴 카운트 증가
        self.state.turn_count += 1

    def _analyze_topics_with_ai(self, user_message: str):
        """AI를 사용하여 주제 및 감정 분석"""
        try:
            analysis = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """사용자 메시지를 분석하여 JSON으로 응답하세요.
정확히 다음 형식만 사용하세요:
{"topic": "주제", "emotion": "감정", "interests": ["관심사1"], "depth": "shallow/medium/deep"}
JSON만 출력하고 다른 텍스트는 포함하지 마세요."""
                    },
                    {"role": "user", "content": user_message}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=150,
            )

            result_text = analysis.choices[0].message.content.strip()
            # JSON 파싱 시도
            if result_text.startswith("{"):
                result = json.loads(result_text)
                # 주제 업데이트
                new_topic = result.get("topic", "")
                if new_topic:
                    if new_topic == self.state.last_topic:
                        self.state.topic_duration += 1
                    else:
                        self.state.topic_duration = 1
                        self.state.last_topic = new_topic
                        if new_topic not in self.state.topics_discussed:
                            self.state.topics_discussed.append(new_topic)

                # 감정 업데이트
                emotion = result.get("emotion", "neutral")
                self.user_profile.emotional_tone = emotion

                # 관심사 추가
                interests = result.get("interests", [])
                for interest in interests:
                    if interest not in self.user_profile.interests:
                        self.user_profile.interests.append(interest)

                # 대화 깊이
                depth = result.get("depth", "medium")
                self.user_profile.conversation_depth = depth

        except (json.JSONDecodeError, Exception):
            # 분석 실패 시 무시하고 진행
            pass

    def start_conversation(self) -> str:
        """AI가 먼저 대화를 시작 (능동적 시작)"""
        self._update_system_prompt()

        # 시간대에 따른 인사
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = "좋은 아침이에요!"
        elif 12 <= hour < 18:
            time_greeting = "안녕하세요!"
        elif 18 <= hour < 22:
            time_greeting = "좋은 저녁이에요!"
        else:
            time_greeting = "이 시간에도 깨어 계시네요!"

        # 대화 시작 주제 목록
        conversation_starters = [
            f"{time_greeting} 저는 대화를 좋아하는 AI에요. 오늘 하루는 어떠셨어요? 특별한 일이 있었는지 궁금해요! 😊",
            f"{time_greeting} 만나서 반가워요! 요즘 가장 관심 있는 것이 뭔지 궁금한데, 혹시 최근에 빠져있는 취미나 관심사가 있나요?",
            f"{time_greeting} 오늘은 어떤 이야기를 나눠볼까요? 최근에 본 영화, 읽은 책, 아니면 요즘 고민거리... 뭐든 좋아요! 🎬📚",
            f"{time_greeting} 제가 먼저 재미있는 질문 하나 던져볼게요. 만약 내일부터 1년간 세계 어디든 갈 수 있다면, 첫 번째 목적지는 어디로 하실 건가요? ✈️",
            f"{time_greeting} 반가워요! 혹시 요즘 '이건 꼭 해봐야지' 하고 마음먹은 게 있나요? 새로운 도전이나 목표 같은 거요!",
        ]

        starter_prompt = random.choice(conversation_starters)

        # AI 응답 생성 (시작 메시지)
        self.messages.append({"role": "assistant", "content": starter_prompt})

        self._log_turn("assistant", starter_prompt)
        return starter_prompt

    def chat(self, user_message: str) -> str:
        """
        사용자 메시지에 대한 능동적 응답 생성

        Args:
            user_message: 사용자의 메시지

        Returns:
            AI의 능동적 응답
        """
        # 1. 사용자 메시지 분석
        self._analyze_user_message(user_message)

        # 2. AI 기반 주제/감정 분석 (2턴마다 또는 초반 3턴)
        if self.state.turn_count % 2 == 0 or self.state.turn_count <= 3:
            self._analyze_topics_with_ai(user_message)

        # 3. 시스템 프롬프트 업데이트 (상태 반영)
        self._update_system_prompt()

        # 4. 사용자 메시지 추가
        self.messages.append({"role": "user", "content": user_message})

        # 5. 참여도가 매우 낮을 때 특별 처리
        if self.state.silence_count >= 3:
            self._inject_engagement_boost()

        # 6. API 호출
        try:
            response = self.client.chat.completions.create(
                messages=self.messages,
                model=self.model,
                temperature=0.8,
                max_tokens=1024,
                top_p=0.9,
            )
            assistant_message = response.choices[0].message.content

        except Exception as e:
            assistant_message = f"죄송해요, 잠시 문제가 생겼어요. 다시 한번 말씀해주시겠어요? (오류: {str(e)})"

        # 7. 응답 저장
        self.messages.append({"role": "assistant", "content": assistant_message})

        # 8. 로그 기록
        self._log_turn("user", user_message)
        self._log_turn("assistant", assistant_message)

        # 9. 메시지 히스토리 관리 (너무 길어지면 요약)
        self._manage_history()

        return assistant_message

    def _inject_engagement_boost(self):
        """참여도가 낮을 때 대화 활성화 메시지 삽입"""
        boost_messages = [
            "사용자가 짧은 응답을 연속으로 하고 있습니다. 흥미를 끌 수 있는 재미있는 질문이나 놀라운 사실을 공유하여 대화에 활기를 불어넣으세요. 예/아니오가 아닌 개방형 질문을 사용하세요.",
            "대화 참여도가 낮습니다. 완전히 다른 흥미로운 주제를 꺼내거나, '만약에...' 시나리오를 제시해보세요.",
            "사용자가 관심을 잃고 있을 수 있습니다. 가벼운 게임을 제안하거나 (예: '이것 vs 저것'), 의외의 질문을 던져보세요.",
        ]
        self.messages.append({
            "role": "system",
            "content": random.choice(boost_messages)
        })
        self.state.silence_count = 0

    def _manage_history(self):
        """대화 히스토리 관리 - 너무 길어지면 요약"""
        # 시스템 메시지를 제외한 메시지 수
        non_system = [m for m in self.messages if m["role"] != "system"]
        if len(non_system) > 30:
            # 오래된 대화 요약
            old_messages = non_system[:20]
            try:
                summary_response = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "다음 대화의 핵심 내용을 3-4문장으로 요약하세요. 중요한 주제, 사용자의 관심사, 핵심 정보를 포함하세요."
                        },
                        {
                            "role": "user",
                            "content": "\n".join([f"{m['role']}: {m['content']}" for m in old_messages])
                        }
                    ],
                    model=self.model,
                    temperature=0.3,
                    max_tokens=300,
                )
                summary = summary_response.choices[0].message.content

                # 시스템 메시지 + 요약 + 최근 메시지만 유지
                system_msgs = [m for m in self.messages if m["role"] == "system"]
                recent_msgs = non_system[20:]
                self.messages = system_msgs + [
                    {"role": "system", "content": f"[이전 대화 요약] {summary}"}
                ] + recent_msgs
            except Exception:
                # 요약 실패 시 단순 트림
                system_msgs = [m for m in self.messages if m["role"] == "system"]
                recent_msgs = non_system[10:]
                self.messages = system_msgs + recent_msgs

    def generate_proactive_message(self) -> str:
        """
        사용자 입력 없이 AI가 능동적으로 메시지를 생성
        (예: 일정 시간 후 자동 메시지)
        """
        self._update_system_prompt()

        proactive_prompt = """사용자가 잠시 조용합니다. 
다음 중 하나를 자연스럽게 해주세요:
1. 이전 대화에서 언급된 주제에 대한 흥미로운 후속 이야기
2. 관련된 재미있는 사실이나 정보
3. 가볍고 재미있는 질문
4. 새로운 대화 주제 제안

강제적이지 않고 자연스럽게 대화를 재개하세요."""

        self.messages.append({"role": "system", "content": proactive_prompt})

        try:
            response = self.client.chat.completions.create(
                messages=self.messages,
                model=self.model,
                temperature=0.9,
                max_tokens=512,
            )
            message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": message})
            self._log_turn("assistant", f"[능동적] {message}")
            return message

        except Exception as e:
            return ""

    def get_conversation_summary(self) -> dict:
        """현재 대화의 요약 정보 반환"""
        return {
            "총 턴 수": self.state.turn_count,
            "현재 모드": self.state.mode.value,
            "현재 주제": self.state.last_topic or "없음",
            "참여도": f"{self.state.engagement_score:.0%}",
            "파악된 관심사": self.user_profile.interests,
            "감정 상태": self.user_profile.emotional_tone,
            "다룬 주제들": self.state.topics_discussed,
        }

    def _log_turn(self, role: str, content: str):
        """대화 턴 로깅"""
        self.conversation_log.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "state": {
                "turn": self.state.turn_count,
                "engagement": self.state.engagement_score,
                "topic": self.state.last_topic,
            }
        })

    def export_log(self, filepath: str):
        """대화 로그를 JSON 파일로 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "conversation_log": self.conversation_log,
                "user_profile": {
                    "interests": self.user_profile.interests,
                    "topics": self.user_profile.mentioned_topics,
                    "emotional_tone": self.user_profile.emotional_tone,
                },
                "final_state": self.get_conversation_summary(),
            }, f, ensure_ascii=False, indent=2)
