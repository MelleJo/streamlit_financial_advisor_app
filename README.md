# AI Hypotheek Assistent

This project is an AI-powered mortgage assistant that uses speech recognition and natural language processing to help with mortgage applications.

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key:
   - Create a `.streamlit/secrets.toml` file in the project root
   - Add your OpenAI API key to this file like this:
     ```toml
     OPENAI_API_KEY = "your-api-key-here"
     ```
   - Replace `your-api-key-here` with your actual OpenAI API key

## Running the Application

To run the application, use the following command:

```
streamlit run main.py
```

## Features

- Audio recording
- Speech-to-text transcription
- AI-powered analysis of mortgage application information
- Interactive UI for reviewing and refining extracted information

## File Structure

- `main.py`: The main entry point of the application
- `audio_service.py`: Handles audio recording
- `transcription_service.py`: Handles speech-to-text transcription
- `gpt_service.py`: Handles AI-powered analysis using OpenAI's GPT model
- `ui_components.py`: Contains UI components for the Streamlit app
- `.streamlit/secrets.toml`: Contains sensitive information like API keys (not version controlled)

## Security Note

Never commit your `.streamlit/secrets.toml` file or expose your API keys in your code. The `.streamlit/secrets.toml` file should be added to your `.gitignore` to prevent accidental commits.