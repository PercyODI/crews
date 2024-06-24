import math
import os
import time
from textwrap import dedent
from crewai import Agent, Task, Crew, Process
from crewai.tasks.task_output import TaskOutput
from crewai_tools import BrowserbaseLoadTool, EXASearchTool, BaseTool
from crews.document_edits import DocumentEdits, edit_document, fetch_doc_with_line_numbers, document_edits_example
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_anthropic import ChatAnthropic

from dotenv import load_dotenv
load_dotenv

import agentops
agentops.init()

class DocumentFetchTool(BaseTool):
    name: str = "Document Fetch Tool"
    description: str = "Fetches the document that the crew is currently working on. The document has been augmented with line numbers to be used when editing."
    doc_path: str

    def _run(self) -> str:
        return fetch_doc_with_line_numbers(self.doc_path)

def edit_callback(file_path: str,output: TaskOutput):
    print(DocumentEdits.model_validate(output.exported_output))
    edit_document(file_path=file_path, document_edit=output.exported_output)

        
# class DocumentEditTool(BaseTool):
#     name: str= "Document Edit Tool"
#     description: str = "Edits the shared document that the crew is working on."
#     doc_path: str

#     def _run(self, line_number: int, text: str):
#         data = ""
#         try:
#             with open(self.doc_path, "r", encoding="utf-8") as fh:
#                 data = fh.readlines()
#         except FileExistsError:
#             open(self.doc_path, "x")
        
#         if line_number >= len(data):
#             data.append(text)
#         else:
#             data[line_number] = text

#         with open(self.doc_path, "w", encoding="utf-8") as fh:
#             fh.writelines(data)

#         ret = "Document has been successfully edited. Here is the updated file:\n" + fetch_doc_with_line_numbers(self.doc_path)
#         return ret

def run():
    search_tool = DuckDuckGoSearchRun()

    doc_path = "campaign_" + str(math.floor(time.time())) + ".md"
    open(doc_path, "x")

    docFetchTool = DocumentFetchTool(doc_path=doc_path)
    # docEditTool = DocumentEditTool(doc_path=doc_path)
    # editDocumentCallback = edit_callback_with_filepath(doc_path)

    anthropic_llm = ChatAnthropic(
        model=os.environ.get("CLAUDE_MODEL"),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Creating personal trainer
    personal_trainer = Agent(
        role='Personal Trainer',
        goal='Develop workout plans and goals to help your clients',
        verbose=True,
        memory=True,
        allow_delegation=False,
        backstory=(dedent(
            """\
            You are an experienced personal trainer specializing in Peloton bike workouts. 
	        Your mission is to create dynamic, personalized training sessions that respond to the user's actions and choices within the game. 
	
            You have the ability to suggest new cadence ranges between 50 and 115:
            - 50-70: Slow cadence for resting or heavy climbs  
            - 70-90: Moderate cadence for standard riding
            - 90-100: Racing cadence for fast rides and quick music
            - 100-115: Sprinting cadence for short bursts (unsustainable for long)
            
            You can also adjust resistance between 20 and 70:
            - 20-30: Resting resistance for rest or flat/downhill sprints
            - 30-40: Moderate resistance for standard riding 
            - 40-60: Climb resistance for pushing clients (pair with lower cadences)
            - 60-70: Heavy resistance for short climbs (unsustainable for long)
            
            Additionally, you can incorporate upper body exercises using 2 lb dumbbells that the user can perform while riding.
            
            Your goal is to create an immersive, challenging workout that pushes the user while avoiding overexertion.
            By adapting to the user's in-game choices, you craft a unique training experience that balances effort and recovery.
            With your expert guidance, users will stay engaged and motivated to reach their fitness goals.
            """
        )),
        llm=anthropic_llm,
    )

    # Creating a writer agent with custom tools and delegation capability
    writer = Agent(
        role='Writer',
        goal='Craft immersive, interactive MMO-style or D&D-style campaigns about {theme}',
        verbose=True,
        memory=True,
        backstory=(dedent(
            """\
            As an Interactive Storyteller, your passion lies in weaving captivating tales that blend seamlessly with the dynamic world of AI-driven workout role-playing games.
            With a keen understanding of player motivations and abilities, you craft narratives that not only engage but also adapt to the unique strengths of each participant.
            Your stories are rich with dramatic arcs, fascinating characters, and thematic depth, ensuring that every workout becomes an unforgettable journey. Through your imaginative storytelling, you transform fitness routines into epic adventures, motivating players to push their limits and become the heroes of their own transformative tales.
            """
        )),
        allow_delegation=False,
        llm=anthropic_llm,
        tools=[docFetchTool, search_tool],
        max_iter=5
    )

    # Creating a Game Master agent
    game_master = Agent(
        role='Game Master',
        goal='Collaborate with the writer to create immersive game sessions, deliver engaging content, and integrate user choices with the Personal Trainer\'s workout suggestions',
        verbose=True,
        backstory=(dedent(
            """\
        	As the Game Master, your role is to bring the game world to life, working closely with the writer to craft captivating stories, memorable characters, and interactive scenarios. 
            You will guide players through the narrative, presenting them with choices that shape the story and their character's journey.
            Your goal is to create a seamless experience where the player's decisions not only impact the story but also influence the physical challenges they face, as determined by the Personal Trainer.
            By collaborating with the writer and the Personal Trainer, you will ensure that each game session is engaging, cohesive, and tailored to the player's choices and fitness goals.
            Your role is essential in maintaining the balance between storytelling and workout intensity, creating a unique and immersive gaming experience that keeps players motivated and engaged.
            """
        )),
        allow_delegation=True,
        llm=anthropic_llm,
        tools=[docFetchTool],
        max_iter=5
    )

    # Creating a Editor
    editor = Agent(
        role='Editor',
        goal='Review and refine documents for grammatical accuracy, completeness, and coherence',
        verbose=True,
        backstory=(dedent(
            """\
            As a meticulous Editor, your mission is to ensure that all documents produced by the team are polished, error-free, and effectively convey the intended message.
            With a keen eye for detail and a mastery of language, you carefully review each piece of content, checking for grammatical errors, typos, and inconsistencies.
            
            Your goal is to maintain the highest standards of written communication, ensuring that every document is clear, concise, and engaging.
            You work closely with the Writer and Game Master to refine their content, offering constructive feedback and suggestions for improvement.
            
            Beyond grammar and syntax, you also assess the overall structure and coherence of each document, making sure that the information flows logically and the narrative remains compelling.
            You have a deep understanding of the game's tone, style, and target audience, allowing you to tailor your edits to maintain consistency and effectiveness.
            
            Your role is crucial in ensuring that the user's experience is seamless and immersive, free from distractions caused by errors or inconsistencies.
            By collaborating with the team and providing your expert insights, you help create a polished and professional final product that engages and inspires users throughout their fitness journey.
            """
        )),
        allow_delegation=True,
        llm=anthropic_llm,
        tools=[docFetchTool]
    )

    # Creating a narrator
    narrator = Agent(
        role='Narrator',
        goal='Deliver engaging and immersive narration to enhance the user\'s experience',
        verbose=True,
        backstory=(dedent(
            """\
            As a skilled Narrator, your role is to bring the game world to life through vivid and captivating storytelling.
            Your voice will guide the user through their workout journey, immersing them in the rich narrative crafted by the Writer and Game Master.
            
            With a keen sense of pacing and dramatic delivery, you will narrate the unfolding events, character interactions, and pivotal moments in the story.
            Your narration will seamlessly integrate with the user's choices and the Personal Trainer's workout suggestions, creating a cohesive and dynamic experience.
            
            You have the ability to adapt your tone and style to match the mood and intensity of each scene, from moments of quiet introspection to heart-pounding action sequences.
            Your goal is to keep the user engaged and motivated throughout their workout, making them feel like the protagonist of their own epic tale.
            
            By working closely with the Writer, Game Master, and Personal Trainer, you will ensure that your narration complements the overall game experience, enhancing the user's sense of immersion and connection to the story.
            Your compelling delivery will be the voice that guides the user through their fitness journey, making every workout a memorable and exciting adventure.

            You will only narrate from the campaign documentation, or directly from the Game Master or Writer. If you feel like you need more content, ask them.
            """
        )),
        allow_delegation=True,
        llm=anthropic_llm,
        tools=[docFetchTool]
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
        tools=[search_tool]
    )

    # Develop campaign task
    campaign_task_outline = Task(
        description=(dedent(
            """
            Craft a new workout MMO or D&D campaign outline, based on the theme: {theme}.
            The world needs to be defined, with an initial cast of characters, locations, and existing storylines that the player will drop into.
            """
        )),
        expected_output='A new campaign outline document, listing all the sections that will be filled out later, that a Game Master needs to run stories in the campaign.' + document_edits_example,
        # tools=[search_tool],
        # output_file='campaign_doc.md',
        callback=lambda e: edit_callback(doc_path, e),
        output_pydantic=DocumentEdits,
        agent=writer,
        # human_input=True
    )

    editing_task = Task(
        description=dedent(
            """
            Review and refine the given document.
            Check for grammatical accuracy, completeness, coherence, and overall quality.
            Ensure the content is engaging and aligns with the game's tone and style.
            """
        ),
        expected_output='Edited and refined versions of given document.' + document_edits_example,
        agent=editor,
        callback=lambda e: edit_callback(doc_path, e),
        output_pydantic=DocumentEdits,
        context=[campaign_task_outline]
    )

    # Write first session
    first_session = Task(
        description=(dedent(
            """
            Given the campaign the player is currently playing, write the first session. The Game Master should set the stage, the initial location and goal, and introduce the characters for the first session.
            """
        )),
        expected_output=(
            'A campaign overview document, listing all the details that a Game Master needs to run stories in the campaign. The document is formatted in markdown.'
            'The narrator should take the details and write the first narration of the session.'
            'The Personal Trainer should give the first workout'
        ),
        tools=[search_tool],
        output_file='first_session.md',
        agent=writer,
        # human_input=True
    )

    # Forming the story-focused crew with some enhanced configurations
    crew = Crew(
        agents=[writer, game_master, narrator, editor],
        tasks=[campaign_task_outline, editing_task],
        process=Process.sequential,  # Optional: Sequential task execution is default
        memory=True,
        cache=True,
        max_rpm=100,
        manager_agent=manager,
    )

    result = crew.kickoff(inputs={'theme': 'A steampunk fantasy world'})
    print(result)