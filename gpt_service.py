import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(model_name="gpt-4o-2024-08-06", temperature=0.3, openai_api_key=api_key)
        self.prompt = PromptTemplate(
            input_variables=["transcript"],
            template=self._load_prompt()
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def _load_prompt(self):
        with open("prompt_template.txt", "r") as file:
            prompt_template = file.read()
        return prompt_template

    def analyze_transcript(self, transcript, app_state=None):
        logger.info("Analyzing Transcript")
        try:
            # Prepare person details string
            person_details = ""
            if app_state and app_state.person_details:
                for person_id, details in app_state.person_details.items():
                    person_details += f"\nPersoon {person_id.split('_')[1]}:\n"
                    for key, value in details.items():
                        person_details += f"- {key}: {value}\n"

            # Run the analysis
            result = self.chain.run(
                transcript=transcript,
                number_of_persons=app_state.number_of_persons if app_state else "Onbekend",
                person_details=person_details if person_details else "Geen details beschikbaar"
            )
            
            logger.info("Analysis complete!")
            return self._parse_result(result)
        except Exception as e:
            logger.error(f"An error occurred during analysis: {str(e)}")
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
                current_section = line[1:-1]  # Extract tag name without <>
            elif line.startswith('</adviesmotivatie_'):
                current_section = None
            elif current_section:
                sections[current_section] += line + '\n'
        
        # Remove any leading/trailing whitespace from each section
        sections = {key: value.strip() for key, value in sections.items()}
        
        return sections
