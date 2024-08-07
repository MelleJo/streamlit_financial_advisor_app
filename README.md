# Financial Advisor Assistant

This Streamlit application helps financial advisors transcribe and analyze their advisory notes using advanced AI technologies.

## Features

- Audio recording using streamlit-mic-recorder
- Transcription of audio using OpenAI's Whisper API
- Analysis of transcripts using GPT-4 via LangChain
- Interactive UI for reviewing and refining analysis results
- Easy copying of results to clipboard

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/streamlit_financial_advisor_app.git
   cd streamlit_financial_advisor_app
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   - Rename `.env.example` to `.env`
   - Replace `your_openai_api_key_here` with your actual OpenAI API key

## Running the Application

To run the application, use the following command:

```
streamlit run main.py
```

## Usage

1. Open the application in your web browser.
2. Click the microphone button to start recording your advisory notes.
3. Click the microphone button again to stop recording.
4. The application will transcribe your audio and analyze it.
5. Review the analysis results and provide feedback if necessary.
6. Use the "Copy" buttons to easily copy the results to your clipboard.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.