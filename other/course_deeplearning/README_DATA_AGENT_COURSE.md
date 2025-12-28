# 2025

## Building and Evaluating Data Agents

### Course description

- https://www.deeplearning.ai/short-courses/building-and-evaluating-data-agents/


  > "About this course

  > Learn how to build and evaluate a data agent in “Building and Evaluating Data Agents,” a
  > course created in collaboration with Snowflake, and taught by Anupam Datta, AI Research
  > Lead, and Josha Reini, Developer Advocate at Snowflake.

  > You’ll design a data agent that connects to data sources (databases, files) and performs
  > web searches to respond to users’ queries. The agent will consist of sub-agents, each
  > specialized in connecting to a particular data source, and other sub-agents that
  > summarize or visualize the results. To answer a particular query, the agent will use a
  > planner that identifies which sub-agents to call and in what order.

  > You’ll add observability to the agent’s workflow and evaluate the quality of its output.
  > Using an LLM-as-a-judge approach, you’ll assess whether the final answer is relevant to
  > the user’s query and grounded in the collected data. You’ll also evaluate the process by
  > determining whether the agent’s goal, plan, and actions (GPA) are all aligned.

  > Finally, you’ll apply inline evaluations to evaluate the agent’s performance during
  > runtime. At every retrieval step, you’ll evaluate if the collected data is relevant to
  > the user’s query. The agent will use this evaluation score to decide if it needs to
  > adjust its plan.

  > What you’ll do, in detail:

  >     Understand what data agents are and how they can be trustworthy when their goal,
  >     plan, and actions are properly aligned. Build a data agent that plans, performs web
  >     searches ,and visualizes or summarizes the results, using a multi-agent workflow
  >     implemented in LangGraph. Expand the agent’s capabilities by adding a Cortex
  >     sub-agent that retrieves information from structured and unstructured data stored in
  >     Snowflake. Add tracing to the agent’s workflow to log the steps it takes to answer a
  >     query. Evaluate the context relevance of the retrieved results, the groundedness of
  >     the final answer, and its relevance to the user’s query. Measure the alignment of
  >     the agent’s goal, plan, and actions (GPA) by computing metrics such as plan quality,
  >     plan adherence, logical consistenc,y and execution efficiency. Improve the agent’s
  >     performance by adding inline evaluations and updating the agent’s prompt..

  > By the end, you’ll know how to build, trace, and evaluate a multi-agent workflow that
  > plans tasks, pulls context from structured and unstructured data, performs web search,
  > and summarizes or visualizes the final results."


- Course introduction

    - LLM as a judge to evaluate whether the answer is relevant to the users query. You
    can use offline evaluation metrics to evaluate the process by which the agent
    arrives at the final answer.

    - You will compare the offline evaluation metric. Both


- Goal, Plan and Action GPA

    - ChatGPT deep research would be considered a data agent. It only makes use of data
      that is available on the web.

    - In many enterprise settings, it might be useful to make useful of data that is
      available internally. Snowflake intelligence is one example of such an agent that
      works on company internal data.

    - Example use of three data agents to answer a complex query. "Identify regulatory
      changes in the financial services industry. Identify pending deals in industries
      that are currently experiencing regulatory changes. Help reposition our value
      proposition for each given the changes.

        - Pending deals ← Proprietary database retrieved through SQL
        - Regulatory changes ← Web search
        - Enhance value proposition ← internal search into meeting notes

    - Goal: responding to a query
    - Plan: to accomplish the goal. **Query decomposition**. Decompose the query into 3 sub-queries.
    - Action to achieve various subgoals. Interactions between plan and action.

    - Trustworthy agents Execute with Goal, Plan and Action aligned.

        - How do we measure an agent's GPA?
        - Plan quality
        - Plan adherence: deviations from the plan can be indications of failure modes
        - Execution efficiency is also implemented with an LLM judge. Checks whether the
          execution part of the Agent was the most efficient part. It can help identify
          redundancies which are sources of improvement.
        - Logical consistency. At the intersection. Check consistencies between plan &
          Goal and planning & replanning.

    - Lesson 2 Build a data agent
    - Lesson 3 Expand data agent capabilities for data search with the langgraph open
      source framework
    - Lesson 4 Observe Agent Performance using the Truelens open source library for
      evaluating agents.
    - Lesson 5 expand evaluation to measure agents GPA. Measure consistency and plan
      adherence as well as failure modes that can be catched. F
    - Lesson 6 improve Agents GPA


### Lesson 2 Build a data agent

prompts.py defines the following functions:

- State
- get_agent_descriptions
- _get_enabled_agents
- format_agent_list_for_planning
- format_agent_guidelines_for_planni
- format_agent_guidelines_for_execut
- plan_prompt
- executor_prompt
- agent_system_prompt


```python
from typing import Literal, Optional, List, Dict, Any, Type
from langgraph.graph import MessagesState

# Custom State class with specific keys
class State(MessagesState):
    user_query: Optional[str] # The user's original query
    enabled_agents: Optional[List[str]] # Makes our multi-agent system modular on which agents to include
    plan: Optional[List[Dict[int, Dict[str, Any]]]] # Listing the steps in the plan needed to achieve the goal.
    current_step: int # Marking the current step in the plan.
    agent_query: Optional[str] # Inbox note: `agent_query` tells the next agent exactly what to do at the current step.
    last_reason: Optional[str] # Explains the executor’s decision to help maintain continuity and provide traceability.
    replan_flag: Optional[bool] # Set by the executor to indicate that the planner should revise the plan.
    replan_attempts: Optional[Dict[int, Dict[int, int]]] # Replan attempts tracked per step number.
```


### Lesson 3 Expand data agent capabilities

- Query structured sales data using SQL

- Query unstructured meeting notes, for example, discovery call.


Cortex analyst relies on a **semantic model**


- describes the Cortex agent tool


TODO: find what the semantic model is. Where is it defined?

Documentation of a react_agent in this context:

    from langgraph.prebuilt import create_react_agent

- https://reference.langchain.com/python/langgraph/agents/?h=create_react_agent

    > Deprecated "create_react_agent has been moved to langchain.agents. Please update
    > your import to from langchain.agents import create_agent."

- https://docs.langchain.com/oss/python/langchain/agents#tool-use-in-the-react-loop

    > "Agents follow the ReAct (“Reasoning + Acting”) pattern, alternating between brief
    > reasoning steps with targeted tool calls and feeding the resulting observations
    > into subsequent decisions until they can deliver a final answer."



### Lesson 4 Observe Agent Performance using Truelens

- RAG Triad to evaluate if an answer is relevant to the query's goal
    - Query
    - Response
    - Context
- Metrics
    - Context relevance is the retrieved context relevant to the query?
    - Answer relevance is the response relevant to the query?
    - Groundedness is the response supported by the research result?


Truelens otel tracing with the open ai provider used to measure agent performance.

- Import the instrument decorator from truelens then use it like this:

        @instrument

- In the instrument attributes `ret` represents the return of the function and `args`
  represents the input of the functions

Comment Paul: never seen such a complex decorator.

Understand the entire trace of the agent. The new instrumentations provides key labels
on each step. Helps extract query and retrieved text. Without which the information
would be buried in a complex data structure that would be hard to retrieve.

Dashboard reads traces and evaluation data. Explore traces to understand what's going
wrong and identify different failure modes.


### Lesson 5 expand evaluation to measure agents GPA


### Lesson 6 improve Agents GPA