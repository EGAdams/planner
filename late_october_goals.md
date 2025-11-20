# Scratchpad & Goals

A collection of notes, tasks, and links, sorted by date.
This needs to be one file for now.

***
```bash
start notes for today under this line.  we are letting
past notes scroll down.  let's see how much it costs to
save text these days.  let's also see how helpful this
text file will be when it gets into the Megabytes.
Now we won't forget nothing.
```
***

## November 18, 2025
https://youtu.be/MZZCW179nKM?t=324
Progressive Disclosure pops up in this Claude Skills discussion.
This is where we can leverage the file system to be a big toc broken up into
smaller toc sections.



---


## November 17, 2025

* get and set the GEMINI_API_KEY

---
### TOC:
D1 - Green Serves if Green Wins    (Dev 1)
D2 - Red Serves after Green Always (Dev 2)
---
###

### Fix three bugs:
* get rid of the "fast flash"
* lead up to the distorted two test
* lead up to the gwgs (dev 2) serve switch to Red 1 bug

We need to open a shell and start the mcp server before an agent can use chrome-devtools-mcp

```bash
(planner) adamsl@DESKTOP-2OBSQMC:~/planner$ npx -y chrome-devtools-mcp --browser-url http://127.0.0.1:9222
chrome-devtools-mcp exposes content of the browser instance to the MCP clients allowing them to inspect,
debug, and modify any data in the browser or DevTools.
Avoid sharing sensitive or personal information that you do not want to share with MCP clients.
```

## November 16, 2025
used this command to start the mcp dev tool:
npx -y chrome-devtools-mcp --browser-url http://127.0.0.1:9222

If you're using Whisper, whisper.cpp is a great project with an existing Wasm build that works in browsers and offers real-time STT using quantized models.

GitHub: https://github.com/ggerganov/whisper.cpp

https://chatgpt.com/c/6918e951-71d4-8331-a092-589656f74771


### 12:49 PM
discussion about extension to copy chatgpt messages into gemini cli:
https://chatgpt.com/c/691a0848-2cfc-832f-8cbd-f2bf334ba931
---


## November 12, 2025

### 8:49 AM

Add MCP Git tool.
```json
{
  "servers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    }
  }
}
```

### 12:59 AM

Hundred thousand shot prompt is possible with Gemini 2.5 Flash.

---

## November 11, 2025

### 10:33 PM

**Multi-agent observability**
We will need this:
- [YouTube: Multi-Agent Observability](https://www.youtube.com/watch?v=9ijnN985O_c)
- [GitHub: claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability)

---

## November 6, 2025

### 7:06 PM

- dj whitey: <https://www.youtube.com/shorts/X4Qr1miDR9g>
- asian nails: <https://www.youtube.com/shorts/DUyFdvszAeo>

### ROL Finance Work

**Data Source**

The source of this data comes from here: `/home/adamsl/planner/docling/test_january_statement.py`. The `docling` directory handles the PDF heavy lifting.

**Expense Categorizer**

- URL: `http://172.30.171.179:8080/office/daily_expense_categorizer.html`
- The server is running in WSL.

To run the server for the expense categorizer:
```bash
# Activate virtual environment
cd ~/planner/office-assistant
source venv/bin/activate

# Start the server for the expense categorizer
./start_server.sh
```

---

## November 3, 2025

### 10:44 AM

`/van @pickle_digi.cpp` When the pickle digi C++ process is run, the two Zeros in the top middle section should be on during pairing and blink. Once each team is paired, the respective little Red or Green "0" should stop blinking and stay on steady once the Team is paired. Right now, the Little "0" in the top middle of the PickleDigiScoreBoard is representing the number of serves remaining for the team. This is not right, the Yellow numbers at the top left and the top right should reflect the number of serves left for the respective Team. The little "0"s in the top represent the Teams score of 0 only and should go off when the Team receives their first point. In the beginning of a Doubles game for example, the Team that starts gets 2 serves and the big "2" should be showing on the topmost left or topmost right of the scoreboard depending on which team is serving. When that Team looses a point, the big number goes to "1". When that Team looses another point in a Doubles game, the big Yellow number should go completely off and the other Team should then show "2" to give the opposite Team 2 serves to start with.

---

## November 2, 2025

### 11:58 AM

`/van @.claude-collective/agents.md @.claude/agents @agent-testing-implementation-agent` The agent-tesing-implementation-agent needs its llm changed. It is using Claude as an llm now, but instead we want it to use a gpt-5-codex powered Agent. Please alter the Testing Implementation expert to use a Codex Agent through the communication interfaces that are already built. Here is the directory for those tools: `@communicaton_interface/`

### 8:21 AM

- To communicate with OpenAI from Gemini: <https://github.com/googleapis/python-genai>
- Google AI Studio: <https://aistudio.google.com/projects>
- Draggable (probably use n8n instead): <https://chatgpt.com/c/6902b368-176c-8331-84e0-2dab58f2254d>

---

## October 28, 2025

### 9:26 AM

- **Finish this:** `/home/adamsl/scoreboard_controller/display/test_display`
- **Pickleball:** (context missing)
- **Telegram message handler:** `/home/adamsl/codex-telegram-coding-assistant/src/bot/handlers/message.ts`

### 9:19 AM

- **Understand and fire up Cole's Telegram solution.** We could use this for times when Claude Code is down and also for parallel work. (In progress...)
- **ROL due Friday!** Open up the planner dashboard and finish nailing down the ROL non-personal PDF anomalies.
- **ROL extra:** Incorporate the SST and TTS to one of the agents below.
- **Blue Time:**
    - Then see how he used the Claude agent SDK and let's make a collaboration.
    - How can we use the new Claude web to be more productive?
    - Dig up some memory solutions. What happened to Lance and mem0? What about the Letto solution?
    - Archon code review and possible switchover to Lance or Chroma. This may have already been done in Linux admin or a project like it.

---

## October 27, 2025

### 7:36 PM

`/mnt/e/codex-telegram-coding-assistant/README.md`

---

## October 26, 2025

### 8:44 AM

**YouTube to watch:**
- Claude's Incredible New Skills & More AI News You Can Use
- Anthropic Finally Solved AI Memory & More AI Use Cases
- 9 MCP servers Sean Kochel
- Chrome Dev Tools MCP Server
- Claude Code's Real Purpose (It's Bigger Than You Think)
- The OFFICIAL Archon Guide - 10x Your AI Coding Workflow

**Links to use:**
- <https://brandonhancock.io/ai-agent-bakeoff>

**GitHub to use:**
- <https://github.com/bhancockio/claude-crash-course-templates/tree/main>
- <https://github.com/bhancockio/agent-development-kit-crash-course>
- <https://github.com/jerhadf/linear-mcp-server/tree/main?tab=readme-ov-file>

---

## October 25, 2025

### 10:20 PM

- 3 sub-agents working at night? Find this guy and watch that again: <https://www.youtube.com/watch?v=hmKRlgEdau4>

---

## Unsorted & Undated

### General Tasks
- This all needs to be one file for now.
- Read all of the text files on my desktop and make a file system to store.
- Start experimenting on your own.

### Agent Development
- `/van` Let's create a memory agent using the codex sdk. All agents should be able to send "memories" to this agent that we create. The new memory agent should be able to answer questions about the past using its memory. Read the `LETTA_INTEGRATION.md` document for a guide to implementing the new memory agent's memory.
- Check out the project here: `/home/adamsl/claude-code-sub-agent-collective`. This is where all of the source code for the Claude Agent Collective is. It works very well with the Claude Code ecosystem. We are trying to use the gpt-5-codex cli from OpenAI instead of using Claude from Anthropic. After you take a look at that project, everything should become clear to you as to what we are trying to accomplish and what is wrong with us (our system).

### Miscellaneous Notes
- heating element
- irs `summer0F511prince`
- `~/codex_tdd_orchestrator/.codex-collective$ source ../../planner/.venv/bin/activate`

### Personal/Communications
- Good morning, Roy. My day off was non-stop work until about 3am. I got some sleep. I will be working on those tweaks now. EG
- I am trying to fill out a bill pay form at my American Momentum Bank. I have already given them the account number of the bank. The payment is going to Bank of America. It is asking for the Payee ZIP Code. What should I use for Bank of America Florida?
- Good morning, Roy. I'm glad that everything went good. Thank you for the update. You have a great day and I will see you in the morning. EG
