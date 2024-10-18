from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import praw
from langchain_openai import ChatOpenAI

from redditmine.src.crew.tools.custom_tool import SubredditDetailTool

# Uncomment the following line to use an example of a custom tool
# from .tools.custom_tool import MyCustomTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

@CrewBase
class RedditResearchCrew():
	"""Crew crew"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'
 
	def __init__(self):
		# Initialize the Reddit API client
		self.reddit = praw.Reddit(
			client_id="YOUR_CLIENT_ID",
			client_secret="YOUR_CLIENT_SECRET",
			user_agent="YOUR_USER_AGENT"
		)
	@agent
	def subreddit_analyzer(self) -> Agent:
		return Agent(
        config=self.agents_config['subreddit_analyzer'],
        tools=[SubredditDetailTool(self.reddit)],
        verbose=True,
        output_format="markdown",
        llm=ChatOpenAI(
            temperature=0.7,
            model_name="gpt-3.5-turbo"
        )
    )

	@task
	def subreddit_analysis_task(self) -> Task:
		return Task(
			config=self.tasks_config['subreddit_analysis_task'],
			agent=self.subreddit_analyzer()
		)
 

	@crew
	def crew(self) -> Crew:
		"""Creates the Crew crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=2, 
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
  
	def run(self, inputs):
		return self.crew().kickoff(inputs=inputs)