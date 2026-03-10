from __future__ import annotations

from orion_agent.core import Agent


def main() -> None:
    agent = Agent()
    print("Orion TUI 已启动，输入 exit 退出。")
    while True:
        user_input = input("\n你> ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", ":q"}:
            print("再见。")
            break

        result = agent.run_dialogue_turn(user_input)
        print("\n[ReAct]")
        for index, step in enumerate(result.steps, start=1):
            print(f"{index}. Thought: {step.thought}")
            print(f"   Action: {step.action}")
            print(f"   Action Input: {step.action_input}")
            print(f"   Observation: {step.observation}")

        print("\n助手>")
        print(result.answer)


if __name__ == "__main__":
    main()
