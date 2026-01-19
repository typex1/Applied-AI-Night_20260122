# Applied-AI-Night_20260122
My talk about Kiro - the IDE for AI powered spec-driven design

Kiro prompt for my project:
```
I need an app that drafts LinkedIn posts based on content from the "What's new on AWS" RSS feed available at
https://aws.amazon.com/about-aws/whats-new/recent/feed/. The draft should be sent as an email via an SNS topic.
To have a daily selection, the LinkedIn content topics should be configurable via a keyword list, and not more
than 5 drafts should be sent per day.
```

* Kiro landing page: https://kiro.dev
* Kiro follows the pattern of an "Autonomous Agent" -> https://www.anthropic.com/engineering/building-effective-agents
* MCP servers used: https://github.com/awslabs/mcp/tree/main/src
* What's new with AWS: https://aws.amazon.com/new/
* 156 news on Amazon Bedrock in 2025: https://aws.amazon.com/new/?ams%23article-feed%23pattern-data--111430994.filter=%257B%2522search%2522%253A%2522bedrock%2522%252C%2522filters%2522%253A%255B%257B%2522id%2522%253A%2522whats-new-v2%2523year.or%2522%252C%2522value%2522%253A%255B%25222025%2522%255D%257D%255D%257D
* Kiro pricing: https://kiro.dev/pricing/

My lessons learned / hints:
* Do not keep your initial Kiro prompt too short, because the more brief and generic it is, the more difficult it is for Kiro to "guess" the requirements.
* Carefully review requirements.md, design.md, and tasks.md. Kiro tends to a quite detailed implementation, so it might make sense to remove items.
* Adjustments to the project can be made underway (e.g. removing a taks), Kiro will perform the needed corrections.
* As Kiro sometimes modifies larger parts of the created code project, always commit after each task is done.

Event details
* Event link: https://www.linkedin.com/company/ai-dusseldorf/posts/?feedView=all

### FAQ:
* Can Kiro be also used for projects outside of AWS? **Yes**, Kiro is provider agnostic. Make sure to configure the necessary MCP servers to get started with other providers / stacks.
* More resources on Kiro? Yes, e.g. its own YT channel: https://www.youtube.com/@kirodotdev
