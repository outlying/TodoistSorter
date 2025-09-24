import asyncio
import os
import logging
import argparse

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from todoist_api_python.api_async import TodoistAPIAsync
from pydantic_ai import Agent


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class TaskSectionAssignment(BaseModel):
    task_id: str = Field(description="The Todoist Task ID")
    section_id: str = Field(description="The Todoist Section ID")


class SupportOutput(BaseModel):
    task_to_sections: list[TaskSectionAssignment] = Field(
        description="List of tasks mapped to section IDs"
    )


async def run(todoist: TodoistAPIAsync, project_id: str) -> None:
    logger.info("Starting task-section assignment process")

    tasks = []
    async for page in await todoist.get_tasks(project_id=project_id):
        tasks.extend(page)

    non_assigned_tasks = [task for task in tasks if not task.section_id]

    if not non_assigned_tasks:
        logger.info("All tasks already have sections assigned")
        return

    logger.info(f"Found {len(non_assigned_tasks)} tasks without section")

    sections = []
    async for page in await todoist.get_sections(project_id=project_id):
        sections.extend(page)

    # Maps for logging names instead of IDs
    task_map = {task.id: task.content for task in tasks}
    section_map = {section.id: section.name for section in sections}

    agent = Agent(
        "openai:gpt-4o",
        output_type=SupportOutput,
        instructions="""
        I need you to assign section to a task, based on task name and section name the best you can.
        """,
    )

    msg_tasks = "\n".join(f"{task.content} [TASK_ID: {task.id}]" for task in non_assigned_tasks)
    logger.debug("Tasks without section:\n%s", msg_tasks)

    msg_sections = "\n".join(f"{section.name} [SECTION_ID: {section.id}]" for section in sections)
    logger.debug("Available sections:\n%s", msg_sections)

    logger.info("Requesting AI agent to map tasks to sections")
    result = await agent.run(user_prompt=f"""
    List of tasks:
    {msg_tasks}

    List of sections:
    {msg_sections}
    """)

    logger.info("Received mapping from AI agent, moving tasks to sections")
    results = await asyncio.gather(
        *(
            todoist.move_task(task_id=pair.task_id, section_id=pair.section_id)
            for pair in result.output.task_to_sections
        ),
        return_exceptions=True,
    )

    for pair, move_result in zip(result.output.task_to_sections, results):
        task_name = task_map.get(pair.task_id, pair.task_id)
        section_name = section_map.get(pair.section_id, pair.section_id)

        if isinstance(move_result, Exception):
            logger.error(
                "Failed to move task '%s' to section '%s': %s",
                task_name,
                section_name,
                move_result,
            )
        else:
            logger.info(
                "Successfully moved task '%s' to section '%s'",
                task_name,
                section_name,
            )

    logger.info("Task-section assignment process completed")


def parse_args() -> tuple[str, str]:
    """Parse CLI arguments and environment variables.

    Returns
    -------
    tuple[str, str]
        A (api_token, project_id) pair.
    """
    load_dotenv()  # Load env first so we can fall back to it

    parser = argparse.ArgumentParser(description="Assign Todoist tasks to sections using an AI helper.")
    parser.add_argument(
        "--project-id",
        required=True,
        help="Todoist project ID to operate on (must be provided via CLI)",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        help="Todoist API token. Optional if TODOIST_API_TOKEN is set in the environment.",
    )

    args = parser.parse_args()

    api_token = args.api_key or os.getenv("TODOIST_API_TOKEN")
    if not api_token:
        parser.error("API key is required: pass --api-key or set TODOIST_API_TOKEN in the environment.")

    project_id = args.project_id
    return api_token, project_id


if __name__ == "__main__":
    api_token, project_id = parse_args()

    todoist = TodoistAPIAsync(api_token)

    asyncio.run(run(todoist=todoist, project_id=project_id))
