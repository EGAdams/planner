Hello and welcome back to another episode of Tash Teaches. I'm Tash, and in today’s video I want to talk about something that has massively increased the effectiveness of my Claude Code usage—something we could call metaprompting.

A lot of people who have come to Claude Code have arrived here from more naive or even childlike approaches to AI-assisted coding, like platforms such as Vzero or Lovable. The “vibe coding” concept—where you just say “do this,” “do that,” and hope it works—is lovely in theory. But you’ll notice that a lot of the time, things don’t get implemented properly, or they break, or they can’t be effectively tested. You end up having to give 20 or 30 individual prompts to solve a single problem or add a single feature you originally wanted.

The 'Create Prompt' Prompt

To explain this, I want to show you a particular prompt I run any time I want to do something of substance. If I’m just trying to change a background from yellow to red—sure, I could just change the CSS myself or give a simple prompt. But most of the time, I’m doing more complex things—multi-stage changes across files, analysis, verification, and testing.

That’s where I use a prompt I call create prompt. This is a meta-prompt—a prompt that helps create other prompts. Rarely do I just tell Claude what I want and let it go do it, because there are often assumptions or misalignments that lead to poor results.

This create prompt is designed as a prompt engineer. It analyzes what I want to do, figures out whether the task is simple or complex, checks clarity, breaks things into sequential or parallel sub-prompts, considers dependencies, and ensures validation steps are included.

How It Works

It uses XML tags like <thinking>, <objective>, <requirements>, etc., to structure the prompt clearly. It asks clarification questions if needed and constructs the final prompt accordingly. It even saves the prompt into a folder called prompts/, with incremental filenames like 001_name, 002_name, etc.

Anthropic recommends this XML-based structure. So your prompt includes:

Objective

Context

Requirements

Constraints

Output

Success Criteria

Verification

There are also conditional inclusions—e.g., if extended reasoning is needed, it adds language like “thoroughly analyze” or “go beyond basics.”

Prompt Patterns

There are templates for different kinds of tasks:

Coding Tasks: objective, context, requirements, implementation, output, verification.

Analysis Tasks: required files, context, evaluation, output.

Research Tasks: scope, deliverables, evaluation criteria.

It’s not just about structure—it includes intelligence rules, such as always checking for clarity, context importance (why, who, what for), scope assessment, precision over brevity, and file references.

Every prompt must specify:

Where to save outputs

How success will be measured

Verification steps

After a prompt is created, the user is shown options: run it, review it, save for later, etc. If multiple prompts are needed, it asks whether they should run in parallel or sequentially.

The 'Run Prompt' Prompt

Once a prompt is created, I don’t run it in the same context window—because it pollutes the chat’s memory. Instead, I use a second meta-prompt called run prompt, which spawns new subagents to run the saved prompt with a clean context window. It finds the right prompt file and runs it accordingly.

This separation improves performance and accuracy, because it doesn’t carry over irrelevant context from previous tasks.

Using Meta-Prompting in Practice

So let me show you how I use this in practice. I run the create prompt, describe what I want—say, “I want to create a CLI-based music tool”—and then run it. In another window, I just give Claude that request directly without metaprompting.

The difference is immediate. In the first case (without metaprompting), Claude generates code quickly but doesn’t ask questions. The result is okay but basic and glitchy. In the second case (with metaprompting), Claude asks for clarification on audio libraries, visuals, sequencing, runtime, and dependencies. This helps refine the prompt and leads to significantly better output.

Comparison Results

In the without metaprompting example, the code is a monolithic single file. It runs, but it's glitchy and uses emojis and clicky sound effects.

In the with metaprompting example, the code is modular—split into source files like audio.js and visuals.js, with a clean index.js, and even includes a README. The result is a far superior and more maintainable project.

Making Enhancements

Let’s say I want to add rainbow fractals, sample-and-hold FM modulation, and real-time scale switching. Again, I use metaprompting, answer a few clarifying questions, and get a new structured prompt.

This updated prompt:

Describes visual changes (trippy fractals)

Explains audio enhancements (FM synthesis)

Specifies interactive scale selection (arrow keys, visual indicators)

Details what files to modify

Includes success criteria and verification

Claude executes this new prompt in a clean context, and the generated result is far better than the direct one-shot version.

Outro

So yes, this may seem long-winded. But as I said, if you're just changing a background color, don’t overthink it. But if you're doing something complex, metaprompting dramatically improves results.

This approach works not just for new tools, but for refactoring, database migrations, and any multi-step task. I’ll link to the GitHub where you can download the prompt and try it yourself.

Let me know if you’d like more videos about other prompts I use—I've got some really exciting ones coming. But for now, that’s all folks. Thanks for watching!
