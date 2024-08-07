# AI Hypotheek Assistent

This project is an AI-powered mortgage assistant that uses speech recognition and natural language processing to help with mortgage applications.

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key:
   - Copy the `.env.example` file and rename it to `.env`
   - Replace `your_openai_api_key_here` with your actual OpenAI API key
   - Alternatively, you can set the `OPENAI_API_KEY` environment variable directly in your system

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

## Security Note

Never commit your `.env` file or expose your API keys in your code. The `.env` file is included in `.gitignore` to prevent accidental commits.