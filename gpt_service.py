import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o-2024-08-06",
            temperature=0.3,
            openai_api_key=api_key
        )
        self.prompt = PromptTemplate(
            input_variables=["transcript", "conversation_history"],
            template=self._load_prompt()
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def _load_prompt(self):
        with open("prompt_template.txt", "r", encoding='utf-8') as file:
            return file.read()

    def analyze_transcript(self, transcript, app_state=None):
        logger.info("Starting comprehensive analysis")
        try:
            # Format conversation history if available
            conversation_history = ""
            if app_state and app_state.conversation_history:
                conversation_history = "\n".join([
                    f"{'AI: ' if msg['is_ai'] else 'Klant: '}{msg['content']}"
                    for msg in app_state.conversation_history
                ])

            # Run the analysis
            result = self.chain.run(
                transcript=transcript,
                conversation_history=conversation_history
            )
            
            logger.info("Analysis complete!")
            return self._parse_result(result)
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return None

    def _parse_result(self, result):
        sections = {
            "adviesmotivatie_leningdeel": "",
            "adviesmotivatie_werkloosheid": "",
            "adviesmotivatie_aow": ""
        }
        
        current_section = None
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('<adviesmotivatie_'):
                current_section = line[1:-1]
            elif line.startswith('</adviesmotivatie_'):
                current_section = None
            elif current_section and current_section in sections:
                sections[current_section] += line + '\n'
        
        # Clean up sections
        return {k: v.strip() for k, v in sections.items() if v.strip()}