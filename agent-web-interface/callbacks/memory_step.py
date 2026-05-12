from functools import wraps

# import file_glob_search
import os
import re
from typing import List
import uuid
from mcp import stdio_client
from rich.panel import Panel
from rich.text import Text
from smolagents import (
    ActionStep,
    CodeAgent,
    LiteLLMModel,
    LogLevel,
    MCPClient,
    PlanningStep,
    TaskStep,
)
from agent_config import EXPENSIVE_RESEARCHER_AGENT, MANAGED_TASKMASTER_AGENT
from tools import continue_builtins
from host import Host


def handle_errors(default_return=None, default_factory=None):
    if default_factory:
        default_return = default_factory()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"{func.__name__} → Unexpected error: {e}")
                return default_return

        return wrapper

    return decorator


@handle_errors()
def post_process_output(
    agent: CodeAgent, memory_step: ActionStep | PlanningStep | TaskStep
):
    if isinstance(memory_step, TaskStep):
        return
    if isinstance(memory_step, PlanningStep):
        cleaned_plan = re.sub(
            r"<think>.*?</think>", "", memory_step.plan, flags=re.DOTALL
        )
        agent.logger.log(
            Panel(
                Text(
                    f"Plan postprocessing. Size of plan: {len(memory_step.plan)} -> {len(cleaned_plan)}"
                )
            ),
            level=LogLevel.INFO,
        )
        memory_step.plan = cleaned_plan
    if isinstance(memory_step, ActionStep):
        cleaned_output = re.sub(
            r"<think>.*?</think>", "", memory_step.model_output, flags=re.DOTALL
        )
        agent.logger.log(
            Panel(
                Text(
                    f"Action postprocessing. Size of model output: {len(memory_step.model_output)} -> {len(cleaned_output)}"
                )
            ),
            level=LogLevel.INFO,
        )
        memory_step.model_output = cleaned_output


@handle_errors()
def trim_memory(
    memory_step: ActionStep,
    agent: CodeAgent,
    write_code=True,
    log_memory=False,
    write_memory=True,
    reset_at_planning=True,
    remove_model_thinks=True,
    keep_latest_action_think=False,
    max_prev_actions_steps=-1,
) -> None:
    latest_step = memory_step.step_number
    keep = []
    msgs: list[str] = []
    if isinstance(memory_step, ActionStep) and keep_latest_action_think:
        pass
    elif remove_model_thinks:
        post_process_output(agent, memory_step)

    if log_memory:
        log_current_memory(agent)

    if write_memory:
        write_current_memory(memory_step, agent)

    if reset_at_planning and isinstance(memory_step, PlanningStep):
        reset_on_current_planning(agent, msgs)
        return

    if (
        write_code
        and isinstance(memory_step, ActionStep)
        and (code_str := agent.memory.return_full_code())
    ):
        write_code_steps(memory_step, agent, code_str)

    for index in range(len(agent.memory.steps)):
        previous_memory_step = agent.memory.steps[index]
        is_action = isinstance(previous_memory_step, ActionStep)
        if (
            is_action
            and max_prev_actions_steps >= 0
            and previous_memory_step.step_number <= latest_step - max_prev_actions_steps
        ):
            msgs.append(f"Discarding {type(previous_memory_step)} {index=}")
            continue

        if reset_at_planning and isinstance(previous_memory_step, PlanningStep):
            agent.logger.log(
                Panel(Text("Previous plan found, culling prior memory.")),
                level=LogLevel.INFO,
            )
            task_step = TaskStep(agent.task)
            keep = [task_step, previous_memory_step]
            msgs = [msg.replace("Keeping", "Discarding") for msg in msgs]
            msgs.append(f"Prepending {type(task_step)}")
            msgs.append(f"Keeping {type(previous_memory_step)} {index=}")
            continue

        msgs.append(f"Keeping {type(previous_memory_step)} {index=}")
        keep.append(previous_memory_step)

    agent.logger.log(
        Panel(Text("\n".join(msgs))),
        level=LogLevel.INFO,
    )
    last_action = None
    agent.memory.steps = []
    for step in keep:
        agent.memory.steps.append(step)
        if isinstance(step, ActionStep):
            last_action = step

    if (
        remove_model_thinks
        and keep_latest_action_think
        and isinstance(memory_step, ActionStep)
        and last_action is not None
    ):
        agent.logger.log(
            Panel(Text("New ActionStep. Removing any `think` from last ActionStep.")),
            level=LogLevel.INFO,
        )
        post_process_output(agent, last_action)


@handle_errors()
def log_current_memory(agent):
    memory_log = "\n".join(
        str(type(step))
        + " "
        + str(
            getattr(
                step,
                "model_output",
                getattr(step, "task", getattr(step, "plan", "unknown")),
            )
        )[:100].replace("\n", " ")
        # + str(step.to_messages())
        + "\n"
        for step in agent.memory.steps
    )
    agent.logger.log(
        Panel(Text(memory_log)),
        level=LogLevel.INFO,
    )


@handle_errors()
def write_current_memory(
    memory_step: ActionStep | PlanningStep | TaskStep, agent: CodeAgent
):
    task = getattr(agent, "task", "unknown")
    agent_uuid = getattr(agent, "uuid", None)
    if not agent_uuid:
        agent.uuid = agent_uuid = f"{uuid.uuid4()}"

    task = (
        task.replace(" ", "_")
        .replace("\n", "_")
        .replace(".", "_")
        .replace("/", "_")
        .replace("?", "_")
        .replace("!", "_")
        .replace("\\", "_")
    )
    task = task[0:20]
    code_dir = f"agent_memory/{agent.name}"
    os.makedirs(code_dir, exist_ok=True)
    filename = f"{code_dir}/agent_{agent.name}_memory_{task}_{memory_step.step_number}_{agent_uuid}.jsonl"
    with open(filename, "w") as file:
        file.writelines(
            (
                chat_message.model_dump_json() + "\n"
                for chat_message in agent.write_memory_to_messages()
            )
        )
        agent.logger.log(
            Panel(Text(f"Wrote memory to {filename}")),
            level=LogLevel.INFO,
        )


@handle_errors()
def reset_on_current_planning(agent: CodeAgent, msgs: List[str]):
    # todo handle when managed agent mem in history (don't cull)
    agent.logger.log(
        Panel(Text("Plan updated, culling prior memory.")),
        level=LogLevel.INFO,
    )
    task_step = TaskStep(agent.task)
    agent.memory.steps = []
    agent.memory.steps.append(task_step)
    msgs.append(f"Prepending {type(task_step)}")
    agent.logger.log(
        Panel(Text("\n".join(msgs))),
        level=LogLevel.INFO,
    )


@handle_errors()
def write_code_steps(memory_step: ActionStep, agent: CodeAgent, code_str: str):
    memory_step.model_output
    task = getattr(agent, "task", "unknown")
    agent_uuid = getattr(agent, "uuid", None)
    if not agent_uuid:
        agent.uuid = agent_uuid = f"{uuid.uuid4()}"

    task = (
        task.replace(" ", "_")
        .replace("\n", "_")
        .replace(".", "_")
        .replace("/", "_")
        .replace("?", "_")
        .replace("!", "_")
        .replace("\\", "_")
    )
    task = task[0:20]
    code_dir = f"agent_code_blocks/{agent.name}"
    os.makedirs(code_dir, exist_ok=True)
    filename = f"{code_dir}/agent_{agent.name}_memory_full_code_{task}_{memory_step.step_number}_{agent_uuid}.py"
    with open(filename, "w") as file:
        file.write(code_str)
        agent.logger.log(
            Panel(Text(f"Wrote code to {filename}")),
            level=LogLevel.INFO,
        )
