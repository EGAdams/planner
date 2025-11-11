# Gemini Structured Outputs and Agent Orchestration Examples

## Project Overview

This project serves as a collection of Python examples demonstrating the capabilities of Google's Gemini models, particularly focusing on:

1.  **Agent Orchestration with Google ADK:** The `adk_subagents.py` file showcases how to build and orchestrate multiple specialized agents (e.g., greeting, farewell, weather) using the Google Agent Development Kit (ADK). It illustrates delegation patterns where a root agent can delegate tasks to sub-agents based on user input, as well as tool usage for specific functionalities like fetching weather information.
2.  **Structured Output Generation with Pydantic:** The `test_pydantic.py` file demonstrates how to leverage Pydantic models to define and enforce structured JSON outputs from Gemini models. This is particularly useful for tasks like content moderation, where a predictable and parseable response format is crucial.

## Technologies Used

*   **Python:** The primary programming language.
*   **Google ADK (Agent Development Kit):** For building and managing AI agents.
*   **Google Generative AI:** Interacting with Gemini models.
*   **Pydantic:** For data validation and defining structured outputs.

## Building and Running

To set up and run these examples, follow these steps:

1.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies:**
    This project uses `google-generativeai`, `google-adk`, and `pydantic`. You can install them using pip:
    ```bash
    pip install google-generativeai google-adk pydantic
    ```
    *(Note: A `requirements.txt` file is not provided, so these are inferred dependencies.)*

3.  **Set up Google API Key:**
    Ensure you have your Google API Key set as an environment variable:
    ```bash
    export GOOGLE_API_KEY="YOUR_API_KEY"
    ```
    Replace `"YOUR_API_KEY"` with your actual Gemini API key.

4.  **Run the Examples:**

    *   **Agent Orchestration Example:**
        ```bash
        python adk_subagents.py
        ```
        This script will initialize the agents. You can then interact with the `root_agent` by providing inputs that trigger greetings, farewells, or weather requests.

    *   **Structured Output with Pydantic Example:**
        ```bash
        python test_pydantic.py
        ```
        This script will demonstrate how to send a prompt to a Gemini model and receive a structured JSON response validated by a Pydantic model.

## Development Conventions

*   **Python Best Practices:** Adherence to standard Python coding conventions.
*   **Pydantic for Data Validation:** Pydantic models are used to define clear data structures and ensure type safety for model inputs and outputs.
*   **Google ADK for Agent Development:** Agents are designed and orchestrated using the Google ADK framework, promoting modularity and reusability.

## Testing

*(TODO: Add specific testing instructions if a testing framework like `pytest` is introduced and tests are written for the agents or structured outputs.)*
Currently, the `test_pydantic.py` file serves as a runnable example demonstrating the structured output functionality rather than a formal test suite.
