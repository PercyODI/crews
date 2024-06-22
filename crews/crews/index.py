import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import BrowserbaseLoadTool, EXASearchTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_anthropic import ChatAnthropic

from dotenv import load_dotenv
load_dotenv

def research_callback(output):
    print("Research task completed with output:")
    print(output)

def run():
    search_tool = DuckDuckGoSearchRun()
    # browser_tool = BrowserbaseLoadTool()
    # exa_search_tool = EXASearchTool()

    anthropic_llm = ChatAnthropic(
        model=os.environ.get("CLAUDE_MODEL"),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),

    )

    # Creating a senior researcher agent with memory and verbose mode
    researcher = Agent(
        role='Senior Researcher',
        goal='Uncover groundbreaking technologies in {topic}',
        verbose=True,
        memory=True,
        backstory=(
            "Driven by curiosity, you're at the forefront of"
            "innovation, eager to explore and share knowledge that could change"
            "the world."
        ),
        tools=[search_tool],
        llm=anthropic_llm,
    )

    # Creating a writer agent with custom tools and delegation capability
    writer = Agent(
        role='Writer',
        goal='Narrate compelling tech stories about {topic}',
        verbose=True,
        memory=True,
        backstory=(
            "With a flair for simplifying complex topics, you craft"
            "engaging narratives that captivate and educate, bringing new"
            "discoveries to light in an accessible manner."
        ),
        tools=[search_tool],
        allow_delegation=False,
        llm=anthropic_llm,
    )

    # Setting a specific manager agent
    manager = Agent(
        role='Manager',
        goal='Ensure the smooth operation and coordination of the team',
        verbose=True,
        backstory=(
            "As a seasoned project manager, you excel in organizing"
            "tasks, managing timelines, and ensuring the team stays on track."
        ),
        llm=anthropic_llm,
    )

    # Research task
    research_task = Task(
        description=(
            "Identify the next big trend in {topic}."
            "Focus on identifying pros and cons and the overall narrative."
            "Your final report should clearly articulate the key points,"
            "its market opportunities, and potential risks."
        ),
        expected_output='A comprehensive 3 paragraphs long report on the latest AI trends.',
        tools=[search_tool],
        agent=researcher,
        callback=research_callback,  # Example of task callback
        # human_input=True
    )

    # Writing task with language model configuration
    write_task = Task(
        description=(
            "Compose an insightful article on {topic}."
            "Focus on the latest trends and how it's impacting the industry."
            "This article should be easy to understand, engaging, and positive."
        ),
        expected_output='A 4 paragraph article on {topic} advancements formatted as markdown.',
        tools=[search_tool],
        agent=writer,
        output_file='new-blog-post.md',  # Example of output customization
    )

    # Forming the tech-focused crew with some enhanced configurations
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,  # Optional: Sequential task execution is default
        memory=True,
        cache=True,
        max_rpm=100,
        manager_agent=manager
    )

    result = crew.kickoff(inputs={'topic': 'AI in healthcare'})
    print(result)