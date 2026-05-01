"""
능동적 대화 모델 - 터미널 인터페이스
====================================

Rich 라이브러리를 사용한 아름다운 터미널 UI로
능동적 대화 시스템을 체험할 수 있습니다.

사용법:
    python main.py

시작하면 API 키 입력 화면이 바로 나타납니다.
"""

import os
import sys
import time
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.text import Text
    from rich.table import Table
    from rich.prompt import Prompt
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.padding import Padding
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from conversation_engine import ProactiveConversationEngine, ConversationMode


# ─── 콘솔 초기화 ────────────────────────────────────────────────────────

console = Console() if HAS_RICH else None


# ─── API 키 입력 화면 (핵심!) ────────────────────────────────────────────

def display_api_key_prompt() -> str:
    """
    API 키를 입력받는 화면.
    큰 박스, 밝은 색상, 이모지 등을 사용하여 한 눈에 보기 쉽게 구성.
    """
    if HAS_RICH:
        console.clear()
        console.print()

        # ── 제목 배너 ──
        title_text = Text()
        title_text.append("🔑", style="bold")
        title_text.append("  GROQ API KEY 입력  ", style="bold white on blue")
        title_text.append("🔑", style="bold")

        console.print(Align.center(title_text))
        console.print()

        # ── 안내 패널 (매우 눈에 띄게) ──
        guide_text = Text()
        guide_text.append("╔══════════════════════════════════════════════════╗\n", style="bright_yellow")
        guide_text.append("║                                                  ║\n", style="bright_yellow")
        guide_text.append("║", style="bright_yellow")
        guide_text.append("   ⚡ Groq API 키가 필요합니다!                  ", style="bold bright_white")
        guide_text.append("║\n", style="bright_yellow")
        guide_text.append("║                                                  ║\n", style="bright_yellow")
        guide_text.append("║", style="bright_yellow")
        guide_text.append("   아직 키가 없다면:                              ", style="white")
        guide_text.append("║\n", style="bright_yellow")
        guide_text.append("║", style="bright_yellow")
        guide_text.append("   👉 https://console.groq.com/keys              ", style="bold bright_cyan underline")
        guide_text.append("║\n", style="bright_yellow")
        guide_text.append("║", style="bright_yellow")
        guide_text.append("   에서 무료로 발급받을 수 있습니다               ", style="white")
        guide_text.append("║\n", style="bright_yellow")
        guide_text.append("║                                                  ║\n", style="bright_yellow")
        guide_text.append("║", style="bright_yellow")
        guide_text.append("   키 형식: gsk_xxxxxxxxxxxxxxxxxxxxxxxx          ", style="dim white")
        guide_text.append("║\n", style="bright_yellow")
        guide_text.append("║                                                  ║\n", style="bright_yellow")
        guide_text.append("╚══════════════════════════════════════════════════╝", style="bright_yellow")

        key_panel = Panel(
            Align.center(guide_text),
            title="[bold bright_yellow]🔐 API 키 설정[/bold bright_yellow]",
            subtitle="[dim]무료 회원가입 후 바로 발급 가능[/dim]",
            border_style="bright_yellow",
            box=box.HEAVY,
            padding=(1, 2),
        )
        console.print(key_panel)
        console.print()

        # ── 입력 프롬프트 (크고 눈에 띄게) ──
        input_label = Text()
        input_label.append("  ▼▼▼ ", style="bold bright_green blink")
        input_label.append("아래에 API 키를 붙여넣기 하세요", style="bold bright_green")
        input_label.append(" ▼▼▼  ", style="bold bright_green blink")
        console.print(Align.center(input_label))
        console.print()

        api_key = Prompt.ask(
            "[bold bright_green]🔑 GROQ API KEY[/bold bright_green]"
        )

        return api_key.strip()

    else:
        # Rich 없을 때 ANSI 기반 표시
        print("\033[2J\033[H")  # 화면 클리어
        print()
        print("\033[1;33m" + "=" * 56 + "\033[0m")
        print("\033[1;33m" + "║" + " " * 54 + "║" + "\033[0m")
        print("\033[1;33m" + "║" + "\033[0m" + "\033[1;37;44m" + "       🔑 GROQ API KEY 입력 🔑       " + "\033[0m" + "\033[1;33m" + "                ║" + "\033[0m")
        print("\033[1;33m" + "║" + " " * 54 + "║" + "\033[0m")
        print("\033[1;33m" + "=" * 56 + "\033[0m")
        print()
        print("\033[1;36m" + "  ⚡ Groq API 키가 필요합니다!" + "\033[0m")
        print()
        print("  아직 키가 없다면:")
        print("\033[1;36m" + "  👉 https://console.groq.com/keys" + "\033[0m")
        print("  에서 무료로 발급받을 수 있습니다")
        print()
        print("\033[2m" + "  키 형식: gsk_xxxxxxxxxxxxxxxxxxxxxxxx" + "\033[0m")
        print()
        print("\033[1;33m" + "=" * 56 + "\033[0m")
        print()
        print("\033[1;32m  ▼▼▼ 아래에 API 키를 붙여넣기 하세요 ▼▼▼\033[0m")
        print()
        api_key = input("\033[1;32m🔑 GROQ API KEY: \033[0m")
        return api_key.strip()


def validate_api_key(api_key: str) -> bool:
    """API 키 기본 형식 검증"""
    if not api_key:
        return False
    if len(api_key) < 10:
        return False
    return True


# ─── 배너 출력 ──────────────────────────────────────────────────────────

def print_banner():
    """메인 배너 출력"""
    if HAS_RICH:
        console.print()
        
        title = Text()
        title.append("🤖 능동적 대화 AI", style="bold bright_white")
        
        subtitle = Text("Proactive Conversation AI — Powered by Groq", style="dim white")

        banner_text = Text()
        banner_text.append("이 AI는 단순히 답변하는 것이 아니라\n", style="white")
        banner_text.append("능동적으로 대화를 이끌어갑니다!", style="bold bright_cyan")

        panel = Panel(
            Align.center(banner_text),
            title=title,
            subtitle=subtitle,
            border_style="bright_cyan",
            box=box.DOUBLE_EDGE,
            padding=(1, 3),
        )
        console.print(panel)
        console.print()

        # 명령어 안내
        cmd_table = Table(
            box=box.ROUNDED,
            border_style="dim cyan",
            title="⌨️  사용 가능한 명령어",
            title_style="bold cyan",
            show_header=True,
            header_style="bold magenta",
        )
        cmd_table.add_column("명령어", style="bold yellow", width=40)
        cmd_table.add_column("설명", style="white")
        cmd_table.add_row("/mode [casual|interview|brainstorm|debate|story]", "대화 모드 변경")
        cmd_table.add_row("/status", "대화 상태 확인")
        cmd_table.add_row("/save", "대화 로그 저장")
        cmd_table.add_row("/proactive", "AI가 능동적으로 메시지 생성")
        cmd_table.add_row("/help", "도움말 표시")
        cmd_table.add_row("/quit", "대화 종료")
        console.print(cmd_table)
        console.print()
    else:
        banner = """
╔══════════════════════════════════════════════════════════╗
║        🤖 능동적 대화 AI (Proactive Chat AI)           ║
║            Powered by Groq API                          ║
╠══════════════════════════════════════════════════════════╣
║  이 AI는 단순히 답변하는 것이 아니라                     ║
║  능동적으로 대화를 이끌어갑니다!                         ║
╠══════════════════════════════════════════════════════════╣
║  명령어:                                                ║
║    /mode [casual|interview|brainstorm|debate|story]      ║
║    /status   - 대화 상태 확인                           ║
║    /save     - 대화 로그 저장                           ║
║    /help     - 도움말                                   ║
║    /quit     - 종료                                     ║
╚══════════════════════════════════════════════════════════╝
"""
        print(f"\033[1;36m{banner}\033[0m")


# ─── 메시지 출력 함수들 ─────────────────────────────────────────────────

def print_ai(message: str):
    """AI 메시지 출력"""
    if HAS_RICH:
        console.print()
        panel = Panel(
            Markdown(message),
            title="🤖 AI",
            title_align="left",
            border_style="bright_magenta",
            box=box.ROUNDED,
            padding=(0, 2),
        )
        console.print(panel)
    else:
        print()
        print(f"\033[1;35m🤖 AI:\033[0m")
        print(f"  {message}")
        print()


def print_user(message: str):
    """사용자 메시지 표시"""
    if HAS_RICH:
        panel = Panel(
            Text(message, style="white"),
            title="👤 You",
            title_align="right",
            border_style="bright_green",
            box=box.ROUNDED,
            padding=(0, 2),
        )
        console.print(panel)


def print_status(summary: dict):
    """대화 상태 출력"""
    if HAS_RICH:
        table = Table(
            title="📊 대화 상태",
            title_style="bold yellow",
            box=box.ROUNDED,
            border_style="yellow",
            show_header=True,
            header_style="bold white",
        )
        table.add_column("항목", style="bold cyan")
        table.add_column("값", style="white")
        for key, value in summary.items():
            if isinstance(value, list):
                value = ", ".join(value) if value else "없음"
            table.add_row(str(key), str(value))
        console.print()
        console.print(table)
        console.print()
    else:
        print(f"\033[1;33m\n📊 대화 상태:\033[0m")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print()


def print_system(message: str):
    """시스템 메시지 출력"""
    if HAS_RICH:
        console.print(f"  ⚙️  {message}", style="dim yellow")
    else:
        print(f"\033[2;33m  ⚙️  {message}\033[0m")


def print_error(message: str):
    """에러 메시지 출력"""
    if HAS_RICH:
        console.print(f"  ❌ {message}", style="bold red")
    else:
        print(f"\033[1;31m  ❌ {message}\033[0m")


def print_mode_change(mode: str):
    """모드 변경 표시"""
    mode_icons = {
        "casual": "☕", "interview": "🎤", "brainstorm": "💡",
        "debate": "⚔️", "story": "📖",
    }
    mode_names = {
        "casual": "캐주얼 대화", "interview": "인터뷰 모드",
        "brainstorm": "브레인스토밍", "debate": "디베이트",
        "story": "스토리텔링",
    }
    icon = mode_icons.get(mode, "🔄")
    name = mode_names.get(mode, mode)

    if HAS_RICH:
        panel = Panel(
            Text(f"대화 모드가 '{name}'(으)로 변경되었습니다!", style="bold"),
            title=f"{icon} 모드 변경",
            border_style="bright_yellow",
            box=box.ROUNDED,
        )
        console.print(panel)
    else:
        print(f"\n\033[1;33m{icon} 모드 변경: {name}\033[0m")


def get_input() -> str:
    """사용자 입력 받기"""
    if HAS_RICH:
        try:
            return Prompt.ask("\n[bold green]👤 You[/bold green]")
        except (EOFError, KeyboardInterrupt):
            return "/quit"
    else:
        try:
            return input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "/quit"


# ─── 명령어 처리 ────────────────────────────────────────────────────────

def handle_command(command: str, engine: ProactiveConversationEngine) -> bool:
    """
    명령어 처리

    Returns:
        True: 계속 진행, False: 종료
    """
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit"):
        print_system("대화를 종료합니다. 좋은 하루 되세요! 👋")
        return False

    elif cmd == "/mode":
        mode_map = {
            "casual": ConversationMode.CASUAL,
            "interview": ConversationMode.INTERVIEW,
            "brainstorm": ConversationMode.BRAINSTORM,
            "debate": ConversationMode.DEBATE,
            "story": ConversationMode.STORY,
        }
        if arg.lower() in mode_map:
            engine.set_mode(mode_map[arg.lower()])
            print_mode_change(arg.lower())

            # 모드 변경 후 AI가 새 모드에 맞는 메시지 생성
            response = engine.generate_proactive_message()
            if response:
                print_ai(response)
        else:
            print_error("사용 가능한 모드: casual, interview, brainstorm, debate, story")

    elif cmd == "/status":
        summary = engine.get_conversation_summary()
        print_status(summary)

    elif cmd == "/save":
        filename = f"conversation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        engine.export_log(filepath)
        print_system(f"대화 로그가 저장되었습니다: {filepath}")

    elif cmd == "/proactive":
        print_system("AI가 능동적으로 대화를 시도합니다...")
        response = engine.generate_proactive_message()
        if response:
            print_ai(response)

    elif cmd == "/help":
        print_banner()

    else:
        print_error(f"알 수 없는 명령어: {cmd}. /help로 도움말을 확인하세요.")

    return True


# ─── 메인 실행 ──────────────────────────────────────────────────────────

def main():
    """메인 실행 함수"""

    # ════════════════════════════════════════════════════════════════
    #  STEP 1: API 키 입력 (눈에 잘 띄는 화면)
    # ════════════════════════════════════════════════════════════════
    api_key = display_api_key_prompt()

    if not validate_api_key(api_key):
        print_error("유효하지 않은 API 키입니다. 다시 실행해주세요.")
        sys.exit(1)

    # API 키 확인 메시지
    if HAS_RICH:
        console.print()
        console.print(
            Panel(
                Text("✅ API 키가 설정되었습니다!", style="bold bright_green"),
                border_style="bright_green",
                box=box.ROUNDED,
            )
        )
        time.sleep(1)
        console.clear()
    else:
        print("\n\033[1;32m✅ API 키가 설정되었습니다!\033[0m")
        time.sleep(1)
        print("\033[2J\033[H")  # 화면 클리어

    # ════════════════════════════════════════════════════════════════
    #  STEP 2: 메인 대화 화면
    # ════════════════════════════════════════════════════════════════
    print_banner()

    # 엔진 초기화 (입력받은 API 키 사용)
    engine = ProactiveConversationEngine(api_key=api_key)

    # AI가 먼저 대화 시작!
    print_system("AI가 대화를 시작합니다...\n")

    starter = engine.start_conversation()
    print_ai(starter)

    # 대화 루프
    while True:
        try:
            user_input = get_input()

            if not user_input:
                continue

            # 명령어 처리
            if user_input.startswith("/"):
                if not handle_command(user_input, engine):
                    break
                continue

            # 사용자 메시지 표시
            print_user(user_input)

            # AI 응답 생성
            if HAS_RICH:
                with console.status("[bold magenta]AI가 생각하는 중...[/bold magenta]", spinner="dots"):
                    response = engine.chat(user_input)
            else:
                print("  🤔 AI가 생각하는 중...")
                response = engine.chat(user_input)

            # AI 응답 출력
            print_ai(response)

        except KeyboardInterrupt:
            print()
            print_system("대화를 종료합니다. 다음에 또 만나요! 👋")
            break
        except EOFError:
            break

    # 종료 시 대화 요약 출력
    summary = engine.get_conversation_summary()
    print()
    print_status(summary)


if __name__ == "__main__":
    main()
