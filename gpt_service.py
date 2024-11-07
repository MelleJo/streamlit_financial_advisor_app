import logging
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=api_key
        )
        self.prompt = PromptTemplate(
            input_variables=["transcript", "conversation_history"],
            template=self._load_prompt()
        )
        # Create chain using modern syntax
        self.chain = (
            {
                "transcript": lambda x: x["transcript"],
                "conversation_history": lambda x: x["conversation_history"]
            }
            | self.prompt 
            | self.llm 
            | StrOutputParser()
        )

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

            # Run the analysis with the new invoke method
            result = self.chain.invoke({
                "transcript": transcript,
                "conversation_history": conversation_history
            })
            
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