AIMultiple
AI
CATEGORIES
AI Coding
AI Foundations
AI Hardware
AI in Industries
Document Automation
Generative AI
Generative AI Applications
Large Language Models
MCP
RAG
AI Code
AI Code Editor
AI Code Review Tools
AI Coding Benchmark
Screenshot to Code
Agentic AI
CATEGORIES
Agent Architectures & Tools
AI Agent Applications
Open-Source Agents
Agentic AI
Agentic AI Design Patterns
AI Agent Tools
AI Agents
Multi Agent Systems
Cybersecurity
CATEGORIES
Cybersecurity Software
Data Privacy
Data Security
Identity & Access Management
Security Tools & Techniques
Threats & Attacks
Deception Tech Companies
Firewall Management Tools
Open Source Firewall
SOC Tools
Data
CATEGORIES
Data Collection
Data Quality & Governance
Datasets
Surveys & Market Research
Synthetic Data
Web Data Scraping
Web Proxies for Data
Appen Alternatives
Data Collection Methods
Data Collection Services
Data Pipeline Tools
Prolific Alternatives
Enterprise Software
CATEGORIES
Cloud Computing
Communication & Messaging
CRM
E-Commerce
File Transfer
Network Monitoring
Process Intelligence & Automation
Robotic Process Automation (RPA)
Workload Automation
Future of Cloud Computing
S3 Compatible Object Storage
Serverless Functions


Search...
Agentic AI
Agentic AI Frameworks
Top 5 Open-Source Agentic Frameworks in 2026
Cem Dilmegani
with Nazlı Şipi
updated on Nov 11, 2025
Oct 2022
Nov 2022
Dec 2022
Jan 2023
Feb 2023
Mar 2023
Apr 2023
May 2023
Jun 2023
Jul 2023
Aug 2023
Sep 2023
Oct 2023
Nov 2023
Dec 2023
Jan 2024
Feb 2024
Mar 2024
Apr 2024
May 2024
Jun 2024
Jul 2024
Aug 2024
Sep 2024
Oct 2024
Nov 2024
Dec 2024
Jan 2025
Feb 2025
Mar 2025
Apr 2025
May 2025
Jun 2025
Jul 2025
Aug 2025
Sep 2025
Oct 2025
Nov 2025
0.0
10k
20k
30k
40k
50k
60k
70k
80k
90k
100k
110k
120k
130k
Github Stars
We reviewed several popular open-source AI agent frameworks, examining their multi-agent orchestration capabilities, agent and function definitions, memory management, and human-in-the-loop features.

To evaluate practical performance, we implemented four data analysis tasks on each framework: logistic regression, clustering, random forest classification, and descriptive statistical analysis. Each task was executed 100 times per framework to measure consistency, performance, and usability under realistic workloads.

Summarize This Research
ChatGPT
ChatGPT
Perplexity
Perplexity
Grok
Grok
Google AI Mode
Google AI Mode
Claude
Claude
Agentic frameworks benchmark
We benchmarked CrewAI, LangChain, OpenAI Swarm and LangGraph.We compared the latency and completion token usage of each framework across different data analysis tasks.

Filter by machine learning task
Logistic Regression
Clustering
Descriptive Statistics
Random Forest
Most Attractive
Least Attractive
350
300
250
200
150
100
Completion Tokens
15
14
13
12
11
10
9
8
7
6
Latency (seconds)
LangGraph is the fastest framework with the lowest latency values across all tasks, while LangChain has the highest latency and token usage.

OpenAI Swarm and CrewAI show very similar performance in both latency and token usage across all tasks. When examining task-level details, the OpenAI Swarm framework uses slightly fewer tokens than the CrewAI framework we prepared, yet it is slightly faster than CrewAI in two of the tasks.

For this benchmark, we integrated the tasks into agent-based architectures on frameworks using Python-based tools. Tasks were executed in a sequential flow with a multi-agent architecture. We chose a sequential setup because steps like data downloading, cleaning, model training, and evaluation are inherently dependent on each other.

To ensure a fair comparison, we created two distinct agent roles on both frameworks: ML Engineer and Data Scientist.

We manually orchestrated a multi-agent setup in LangChain to simulate the same task flow. While this isn’t native to LangChain’s architecture, we ensured equivalent task logic to allow for as fair a comparison as possible.

You can see our methodology in detail here.

Potential reasons behind the performance differences
The key to understanding these performance differences lies in each framework’s architectural foundation:

Framework
Token Usage
Architectural DNA
When Does LLM Work?
Tool Usage Pattern
Analogy
LangChain
🔴 VERY HIGH
Chain Logic – Every link goes through LLM
Every step: “Which tool?” → “How to use?”
Natural language interpretation required
Using a translator constantly
CrewAI
🟡 MEDIUM
Team Approach – Role-based coordination
Only coordination: “This agent does this task”
Agents know their own tools
Team leader coordinating
LangGraph
🟢 VERY LOW
Graph Flow – Deterministic path
Only at “?” nodes: A→B→C→?→D
Pre-determined steps
Following a ready recipe
Swarm
🟢 LOW
Functional – Direct Python calls
Only messaging: function_call()
Python functions (0 interpretation)
Direct tool usage
The primary reason for CrewAI’s performance lies in its architecture, which is fundamentally designed around multi-agent systems. Task delegation, inter-agent communication, and state management are handled naturally and centrally at the framework level. Additionally, tools are directly connected to agents, enabling data flow with minimal middleware, resulting in faster and more efficient execution. This architecture contributes to both lower latency and reduced token consumption.

On the other hand, LangChain is chain-first and built with a single-agent focus at its core. Multi-agent support was added later and is not a native part of the framework’s natural flow. In LangChain, tool selection depends on the LLM’s natural language reasoning rather than direct function calls. Each step involves passing the task to the LLM through a natural language input, and the LLM analyzes this input to decide which tool to use. Since every invocation includes tool selection, LLM interpretation, and, if needed, output parsing, it increases both token consumption and execution time. While this approach offers more flexibility, it introduces more indirect steps, which leads to increased latency and higher token costs.

In contrast, Swarm and LangGraph are more efficiency-oriented. Swarm distributes tasks among specialized agents, each working directly with its own toolset. Tools are connected as native Python functions, and the LLM is only involved when necessary. This leads to lower token usage and faster execution. LangGraph, on the other hand, defines tasks as a graph (DAG), where the tool to be executed at each step is predetermined.It minimizes LLM involvement by only invoking it in ambiguous or decision-making nodes, depending on graph design. This approach minimizes the LLM’s involvement in the system, enhances performance, and simplifies debugging.

In this benchmark, we explained the frameworks along with their design approaches and how we used each individually. However, these frameworks have very different use cases, implementations, and design methods. All performance outcomes ultimately depend on the framework’s architecture, the specific use case, and the deployment environment, so results may vary according to the developer’s design choices and scenario needs.

Compare agentic frameworks
Framework
Pros✅
Cons❌
LangGraph
• Graph-based orchestration with state management
• Supports in-thread and cross-thread memory
• Custom breakpoints for human input
• Highly modular, useful for enterprise logic
• Steep learning curve
• Documentation still maturing
• More rigid than adaptive frameworks
AutoGen
• Adaptive and asynchronous agent interactions
• Low-code support
• Human-in-the-loop via UserProxyAgent
Show More
• No built-in persistent memory
• Difficult to manage in large-scale deployments
CrewAI
• Easy role-based YAML configuration
• Built-in memory
• Human-in-the-loop configurable
• Python-centric design
• Focused on linear task flows
OpenAI Swarm
• Natural language routine definitions
• Lightweight and fast to prototype
• Flexible, prompt-based logic
• No built-in memory
• No formal orchestration or state model
• No native human-in-the-loop support
Show More
LangChain
• Wide integration support (APIs, databases, vector stores)
• Modular components: chains, tools, memory, basic agents
• Strong for RAG and tool-augmented workflows
• Mature documentation and large community
Show More
• Basic agent framework, lacks advanced orchestration
• No graph-based or role-based models
• Multi-agent setups require manual composition
• Performance overhead in deep chains
Show More
Agentic frameworks vary across several key dimensions, and understanding these differences is essential for making meaningful comparisons.


Best use cases by framework:
LangGraph: Complex agent workflows requiring fine-grained orchestration
AutoGen: Research and prototyping where agent behavior needs flexibility and refinement
CrewAI: Production-grade agent systems with structured roles and task delegation
OpenAI Swarm: Lightweight experiments and open-ended task execution in LLM-driven pipelines
LangChain: General-purpose LLM application development with modular components for chains, tools, memory, and retrieval-augmented generation (RAG)

Production readiness:
Framework
Model support
LangChain support
Multimodality
Real-time feedback (streaming)
Observability
Low-code
LangGraph
Any LLM via LangChain
✅ Native (built on LangChain)
Text (extendable via nodes)
✅
✅ (via LangSmith)
❌
AutoGen
OpenAI, Anthropic, custom
❌
Text (extendable)
✅
❌
✅
CrewAI
OpenAI, Anthropic & open model endpoints
Show More
⚠️ Limited (Can wrap LangChain tools manually)
Show More
Text, image, audio (via tools)
✅
❌
✅
OpenAI Swarm
OpenAI only
❌
Limited; prompt-based only
✅
❌
❌
LangChain
Any LLM
❌
Text, image, audio, video (via integrations)
✅
✅ (via LangSmith)
❌
Of note, LangGraph is proprietary software, but it provides an open-source library for agent development.

Here are the most important factors that distinguish one framework from another:

Multi-agent orchestration
Framework
Multi-agent orchestration
Ease of use
LangGraph (Graph-Based)
Centralized: Graph-based multi-agent flows
Complex: Requires understanding acyclic graph structures
AutoGen (Adaptive)
Adaptive orchestration
Moderate: Conversational agent interactions simplify usage
CrewAI (Role-Based)
Hierarchical: Role-based multi-agent flows
Easy: Structured, role-based design makes it easy to start
OpenAI Swarm (Routine-Based)
No defined control flow (routine-based prompting patterns)
Easy: Lightweight and routine-based
LangChain (Chain-Based)
Linear or nested chains with optional agent support
Moderate: Good for pipelines, but multi-agent orchestration needs manual setup
LangGraph

LangGraph framework
LangGraph is a relatively well-known framework and stands out as a key option for developers building agent systems.

Explicit multi-agent coordination: You can model multiple agents as individual nodes or groups, each with its own logic, memory, and role in the system.

It creates AI workflows across APIs and tools. Thus, it is a good fit for RAG and custom pipelines.

That said, it is complex/challenging to debug and the learning curve is steep.

AutoGen

AutoGen1
Free-form agent collaboration: AutoGen allows multiple agents to communicate by passing messages in a loop. Each agent can respond, reflect, or call tools based on its internal logic.

It has an asynchronous agent collaboration, making it particularly useful for research and prototyping scenarios where agent behavior requires experimentation or iterative refinement.

CrewAI

Crew AI2
CrewAI offers a high-level abstraction that simplifies building agent systems by handling most of the low-level logic for you. However, CrewAI’s multi-agent orchestration is limited:

There’s no built-in execution graph or flow control. Agents self-organize based on responses.
Multi-agent flows are linear or loop-based, not hierarchical or DAG-based.
With multiple agents sending messages, it could become difficult to trace, monitor, or debug agent decisions and coordination.

OpenAI Swarm

Swarm framework
OpenAI has described Swarm as a multi-agent framework. However, based on what’s been shared so far:

Swarm currently operates via a single-agent control loop, with:

Natural language routines in the system prompt
Tool usage via docstring parsing
An agent iteratively planning and executing tasks
Thus, it has no agent-to-agent communication (single-agent execution). Unlike frameworks like AutoGen (which supports message passing between agents) or CrewAI (which uses role-based team setups), Swarm has no built-in mechanism for agents to interact with each other.

This makes Swarm a good fit for prototyping, single-agent, step-by-step reasoning workflows using tools or routines (a natural language description of a tasks or workflows).

This approach makes routines in Swarm more flexible and generalizable than traditional scripts or rule-based flows rather than hard-coding logic.

LangChain
LangChain provides comprehensive RAG tooling but operates primarily through single-agent execution patterns.

Single-agent document processing: LangChain handles the user-to-answer pipeline through one coordinating agent that manages the RAG workflow. While LangChain supports multi-agent architectures through its extended components, the core framework lacks native agent-to-agent communication mechanisms.

Unlike AutoGen’s message-passing system or CrewAI’s role-based teams, LangChain’s base architecture routes everything through a central orchestrator rather than enabling direct agent collaboration. This makes it powerful for document-heavy applications but requires additional tooling for true multi-agent coordination.

Agent and function definition
Framework
Agent definition
Function definition
LangGraph (Graph-Based)
🔲 Nodes that maintain a state
📝 Annotations (structured & explicit functions)
AutoGen (Adaptive)
🤖 Agents with flexible routing
📝 Annotations (structured & explicit functions)
CrewAI (Role-Based)
🤖 Agents with skills and associated tasks
📝 Annotations (structured & explicit functions)
OpenAI Swarm (Routine-Based)
🤖 Agents with routines and functions
📄 Docstrings (general-purpose functions)
LangChain (Chain-Based)
🤖 Agent(s) coordinating calls to LLMs and tools (central orchestrator)
📝 Function calls with explicit interfaces (toolkits, prompt templates)
LangGraph
LangGraph takes a graph-based approach to agent design, where each agent is represented as a node that maintains its own state. These nodes are connected through a directed graph, enabling conditional logic, multi-team coordination, and hierarchical control. This enables you build and visualize multi-agent graphs with supervisor nodes for scalable orchestration.

LangGraph uses annotated, structured functions that attach tools to agents. You can build out nodes, connect them to various supervisors, and visualize how different teams interact. Think of it like giving each team member a detailed job description. This makes it easier to build and test agents that work together.

AutoGen
AutoGen defines agents as adaptive units capable of flexible routing and asynchronous communication. Agents interact with each other (and optionally with humans) by exchanging messages, allowing for collaborative problem-solving. Like LangGraph uses annotated, structured functions.

CrewAI
CrewAI takes a role-based design approach. Each agent is assigned a role (e.g., Researcher, Developer) and a set of skills, functions or tools it can access. Function definition is through structured annotations.

OpenAI Swarm
OpenAI Swarm uses a routine-based model where agents are defined through prompts and function docstrings. It doesn’t have formal orchestration or state models, relying instead on manually structured workflows. Functions behavior is inferred by the LLM through docstrings (Swarm identifies what a function does by reading its description) making this setup flexible but less precise.

LangChain
LangChain uses a chain-based architecture where a single orchestrator agent manages calls to language models and various tools. It defines functions through explicit interfaces like toolkits and prompt templates.

While primarily focused on centralized workflows, LangChain supports extensions for multi-agent setups but lacks built-in agent-to-agent communication.

Memory
Framework
Stateful
Contextual
Memory features
LangGraph (Graph-Based)
✅ Yes
✅ Yes
• Short-term: Customizable
• Long-term: External integrations
• Entity memory: Fully supported
AutoGen (Adaptive)
❌ No
✅ Yes
• Short-term: Message lists
• Long-term: External integrations
• Entity memory: Not supported
CrewAI (Role-Based)
✅ Yes
✅ Yes
• Short-term: RAG, Contextual
• Long-term: SQLite3 DB
• Entity memory: Supported via RAG
OpenAI Swarm (Routine-Based)
❌ No
Manual contextual memory
• Short-term: Context variables
• Long-term: External integrations
• Entity memory: Not supported
LangChain (Chain-Based)
✅ Yes
✅ Yes
• Short-term: In-memory or cache-based (e.g., conversation history)
• Long-term: Supports external memory integrations (databases, vector stores, etc.)
• Entity memory: Supported via retrieval and embeddings-based methods
Show More
Memory capabilities:

Stateful: Whether the framework supports persistent memory across executions.
Contextual: Whether it supports short-term memory via message history or context passing.
Memory features is a key part of building agentic systems to remember context and adapt over time:

Short-term memory: Keeps track of recent interactions, enabling agents to handle multi-turn conversations or step-by-step workflows.
Long-term memory: Stores persistent information across sessions, such as user preferences or task history.
Entity memory: Tracks and updates knowledge about specific objects, people, or concepts mentioned during interactions (e.g., remembering a company name or project ID mentioned earlier).
LangGraph
LangGraph uses two types of memory: in-thread memory, which stores information during a single task or conversation, and cross-thread memory, which saves data across sessions. Developers can use MemorySaver to save the flow of a task and link it to a specific thread_id. For long-term storage, LangGraph supports tools like InMemoryStore or other databases. This provides flexible control over how memory is scoped and retained across executions.

AutoGen
AutoGen uses a contextual memory model. Each agent maintains short-term context through a context_variables object, which stores interaction history. It doesn’t have built-in persistent memory.

CrewAI
CrewAI provides layered memory out of the box. It stores short-term memory in a ChromaDB vector store, recent task results in SQLite, and long-term memory in a separate SQLite table (based on task descriptions). Additionally, it supports entity memory using vector embeddings. This memory setup is automatically configured when memory=True is enabled,

OpenAI Swarm
Swarm is stateless and does not manage memory natively. Developers can pass short-term memory through context_variables manually, and optionally integrate external tools or third-party memory layers (e.g., mem0) to store longer-term context.

LangChain
LangChain supports both short-term and long-term memory through flexible components. Short-term memory is typically managed via in-memory buffers that track conversation history within a session. For long-term memory, LangChain integrates with external vector stores or databases to persist embeddings and retrieval data.

Developers can customize memory scopes and strategies using built-in memory classes, enabling efficient management of contextual and entity-specific memory across interactions.

Human-in-the-loop
Framework
Human-in-the-loop
LangGraph (Graph-Based)
⏸️ Custom breakpoints for human input
AutoGen (Adaptive)
💬 Requests feedback after agent execution
CrewAI (Role-Based)
💬 Requests feedback after agent execution
OpenAI Swarm (Routine-Based)
❌ N/A (human-as-a-tool)
LangChain (Chain-Based)
⏸️ Supports custom breakpoints and user interactions within workflows for human feedback and intervention
LangGraph
LangGraph supports custom breakpoints (interrupt_before) to pause the graph and wait for user input mid-execution.

AutoGen
AutoGen natively supports human agents via UserProxyAgent, allowing humans to review, approve, or modify steps during agent collaboration.

CrewAI:
CrewAI enables feedback after each task by setting human_input=True; the agent pauses to collect natural language input from the user.

OpenAI Swarm
OpenAI Swarm offers no built-in HITL.

LangChain
LangChain allows inserting custom breakpoints within chains or agents to pause execution and request human input. This supports review, feedback, or manual intervention at defined points in the workflow.

What agentic frameworks actually do?
Agentic frameworks assist with prompt engineering and managing how data flows to and from LLMs. At a basic level, they help structure prompts so the LLM responds in a predictable format and route responses to the right tool, API, or document.

If building from scratch, you would manually define the prompt, extract the tool the LLM wants to use, and trigger the corresponding API call. Frameworks streamline this by:

Prompt orchestration: Building, managing, and routing complex prompts to LLMs
Tool integration: Letting agents call external APIs, databases, code functions, etc.
Memory: Maintaining state across turns or sessions (short- and long-term)
RAG integration: Enabling knowledge retrieval from external sources
Multi-agent coordination: Structuring how agents collaborate or delegate tasks

Agentic framework3
Agentic frameworks: Real life use cases
LangGraph – Multi-agent travel planner
A production project built with LangGraph demonstrates a stateful, multi-agent travel assistant that pulls flight and hotel data (using Google Flights & Hotels APIs) and generates travel recommendations.4

CrewAI – Agentic content creator
CrewAI’s official examples repository includes flows like trip planning, marketing strategy, stock analysis, and recruitment assistants, where role-specific agents (e.g., “Researcher”, “Writer”) collaborate on tasks.5

CrewAI turns a high-level content brief into a complete article using Groq.

Core features of agentic frameworks
Model support:

Most are model-agnostic, supporting multiple LLM providers (e.g., OpenAI, Anthropic, open-source models).
However, system prompt structures vary by framework and may perform better with some models than others.
Access to and customization of system prompts is often essential for optimal results.
Tooling:

All frameworks support tool use, a core part of enabling agent actions.
Offer simple abstractions to define custom tools.
Most support Model-Context-Protocol (MCP), either natively or through community extensions.
Memory / State:

Use state tracking to maintain short-term memory across steps or LLM calls.
Some helps agents retain prior interactions or context within a session.
RAG (Retrieval-Augmented Generation):

Most include easy setup options for RAG, integrating vector databases or document stores.
This allows agents to reference external knowledge during execution.
Other common features
Support for asynchronous execution, enabling concurrent agent or tool calls.
Built-in handling for structured outputs (e.g., JSON).
Support for streaming outputs where the model generates results incrementally.
Basic observability features for monitoring and debugging agent runs.
Benchmark methodology
In this benchmark, we designed fully equivalent pipelines to fairly and directly compare the LangChain and CrewAI frameworks. We executed four fundamental data analysis tasks: Random Forest, Clustering, Descriptive Statistics, and Logistic Regression, on both frameworks using the same dataset, the same tools, identical task definitions, and identical prompts.

Data and workflow
For data processing, we used the Telco Churn dataset on both frameworks, downloaded via the DownloadDatasetTool from the same GitHub source. Data preprocessing, loading, and overall data flow were structured identically across both platforms.

To ensure secure data sharing between agents and tasks, we implemented thread-safe global state management using Python’s threading.Lock mechanism in both frameworks.

All experiments were executed with the same OpenAI API key, the same LLM model, and identical configuration parameters, including timeout, maximum iterations, and other settings.

Tool alignment
The tools used in frameworks: DownloadDatasetTool, LoadDataTool, TrainModelTool, and EvaluateModelTool were designed to be functionally identical. Error handling, input/output structures, and global state integrations were consistently implemented across both platforms. In addition, fail-safe mechanisms were developed in parallel to ensure that both systems could terminate gracefully in case of errors.

Tools in CrewAI are directly linked to specific agents, allowing straightforward and efficient task execution. In LangChain, however, tool usage depends on the LLM’s natural language understanding to select and invoke tools since multi-agent orchestration is manually implemented and not native to the framework. In LangGraph, tool usage follows a predefined graph (DAG) structure. The tool to run at each step is fixed; the LLM only intervenes in ambiguous or branching scenarios. Tool selection is managed by the graph flow, not the LLM. Although LangGraph can work with LangChain Base tools, for the benchmark, we chose to use LangGraph independently.

In Swarm, tools are connected directly to each agent as Python functions. Each agent only has access to the tools relevant to its task and can call these functions directly.

Task definitions and execution flow
Task definitions and execution order were also designed to be exactly the same. All systems employed two agents: “Data Scientist” and “ML Engineer”. These agents executed the same tasks in the same order, with the same dependency structure. Task descriptions and role definitions were made to match word-for-word to ensure consistency.

Adapting to framework-native architectures
CrewAI is built around a role-based, declarative architecture that naturally supports multi-agent systems. In this setup, each agent is clearly defined with a role and a specific goal. Tasks are explicitly assigned to agents, and for each task, a detailed description and an expected output must be provided. The entire workflow is organized under a centralized Crew structure and executed with a single command. In CrewAI, parameters like task order and expected outputs are mandatory and form an integral part of how the framework operates.

In contrast, LangChain adopts a tool-centric and procedural approach. Agents are created based on a set of tools and a general task type. Unlike CrewAI’s declarative flow, LangChain requires the developer to manually control the task execution step-by-step. Each task must be explicitly invoked by the developer, with no automatic orchestration between steps.

In Swarm, tools are indeed defined as simple Python functions, and agents are created using the agent class, where task instructions guide the agent’s behavior. Agents have access to and can directly call the tools relevant to their specific tasks. Swarm operates through message-based communication, where tasks are executed based on user inputs (messages), and tools are invoked as direct function calls. However, Swarm offers limited built-in automatic step-by-step execution or workflow management; the developer typically controls the process flow. Being more functional and agent-centric, Swarm’s natural operation fits this description.

LangGraph is built around a graph-based, declarative architecture where tasks are represented as nodes in a directed acyclic graph (DAG). Each node has a predetermined, static tool assigned, defining a fixed execution path. The LLM is only engaged in cases of ambiguity or branching, minimizing its use to improve performance and simplify debugging.

Unlike CrewAI’s role-based multi-agent setup or LangChain’s procedural, tool-centric flow requiring manual orchestration, we used LangGraph’s automatic orchestration through its graph structure. Tasks flow naturally from node to node without explicit developer intervention at each step.

Preserving architectural differences
This methodology preserves the natural architectural differences across the frameworks. While maintaining equivalent logic and task definitions across frameworks, we allowed each framework’s native architecture to guide the execution flow, be it sequential, declarative, or graph-based. This approach guarantees that the benchmark results reflect how each framework performs in its realistic, idiomatic usage scenario.

Python environment and execution logic
All implementations were carried out in a Python environment. We integrated the tasks into agent-based architectures on both frameworks using Python-based tools. Tasks were executed in a sequential flow with a multi-agent architecture on both platforms. We intentionally chose a sequential setup because steps like data downloading, data cleaning, model training, and model evaluation are inherently dependent on each other, making sequential execution the most logical and realistic approach for this benchmark.

Reference Links
1.
Top 5 Frameworks for Building AI Agents in 2024 (Plus 1 Bonus) - DEV Community
DEV Community
2.
Top 5 Frameworks for Building AI Agents in 2024 (Plus 1 Bonus) - DEV Community
DEV Community
3.
Agentic AI and Automation - by Sasha Pasmanik
Stay Curious
4.
Automate Your Travel Plans with Multi-Agent AI & LangGraph | by Jalaj Agrawal | Medium
Medium
5.
CrewAI Documentation - CrewAI
Principal Analyst
Cem Dilmegani
Principal Analyst
Cem has been the principal analyst at AIMultiple since 2017. AIMultiple informs hundreds of thousands of businesses (as per similarWeb) including 55% of Fortune 500 every month.

Cem's work has been cited by leading global publications including Business Insider, Forbes, Washington Post, global firms like Deloitte, HPE and NGOs like World Economic Forum and supranational organizations like European Commission. You can see more reputable companies and resources that referenced AIMultiple.

Throughout his career, Cem served as a tech consultant, tech buyer and tech entrepreneur. He advised enterprises on their technology decisions at McKinsey & Company and Altman Solon for more than a decade. He also published a McKinsey report on digitalization.

He led technology strategy and procurement of a telco while reporting to the CEO. He has also led commercial growth of deep tech company Hypatos that reached a 7 digit annual recurring revenue and a 9 digit valuation from 0 within 2 years. Cem's work in Hypatos was covered by leading technology publications like TechCrunch and Business Insider.

Cem regularly speaks at international technology conferences. He graduated from Bogazici University as a computer engineer and holds an MBA from Columbia Business School.
Researched by
Nazlı Şipi
AI Researcher
Nazlı is a data analyst at AIMultiple. She has prior experience in data analysis across various industries, where she worked on transforming complex datasets into actionable insights.
Be the first to comment
Your email address will not be published. All fields are required.

Name
Your Name
Email Address
og@gmail.com
Comment
Write your comment
0/450
In This Article
Agentic frameworks benchmark
Compare agentic frameworks
Multi-agent orchestration
Agent and function definition
Memory
Human-in-the-loop
What agentic frameworks actually do?
Agentic frameworks: Real life use cases
Core features of agentic frameworks
Benchmark methodology
We follow ethical norms & our process for objectivity. AIMultiple's customers in Agentic AI Frameworks include n8n, Weights & Biases.



How likely are you recommend us to a friend or colleague?
1
2
3
4
5
6
7
8
9
10
Not Likely
Extremely Likely
Next to Read
LLMs
Oct 31
The LLM Evaluation Landscape: 16 Frameworks by Functionality
Cem Dilmegani
RAG
Nov 12
RAG Frameworks: LangChain vs LangGraph vs LlamaIndex vs Haystack vs DSPy
Cem Dilmegani with Ekrem Sarı
AI Agents
Nov 28
Low/No-Code AI Agent Builders: n8n, AgentKit, make, Zapier
Cem Dilmegani
Agentic AI Frameworks
Nov 7
Benchmarking Agentic AI Frameworks in Analytics Workflows
Cem Dilmegani with Nazlı Şipi
Agentic AI
Nov 26
Top 10+ Agentic Orchestration Frameworks & Tools in 2026
Hazal Şimşek
Agentic AI
Nov 26
AI Agents vs Agentic AI Systems in 2026
Cem Dilmegani
line
AIMultiple
AIMultiple
About
Career
Commitments
Contact
Culture
How we are funded
How we test
Methodology
Services
AI
Agentic AI Frameworks
AI Agents
AI Coding
AI GPUs
AI Foundations
AI Hardware
AI in Industries
AI Models
AI Memory
Computer Vision
Document Automation
GenAI Applications
Large Language Models
MCP Clients
MCP Servers
Retrieval Augmented Generation
Data
Analytics
Data Collection
Data Science
Data Quality
Machine Learning Operations
Proxy Comparisons
Proxy Types
Scraping Tools
Survey Reviews
Synthetic Data
Web Data Scraping
Web Proxies
Enterprise Software
Automation
Cloud Computing
Customer Relationship Management
E-Commerce
Extended Reality
Industry Software
Internet of Things
Managed File Transfer
Process Improvement
Robotic Process Automation
Sustainability
Workload Automation
© 2025 AIMultiple | All Rights Reserved | Terms of Service | Privacy Policy
