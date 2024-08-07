import streamlit as st
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

class GPTService:
    def __init__(self, api_key):
        self.llm = OpenAI(model_name="gpt-4", temperature=0.7, openai_api_key=api_key)
        self.prompt = PromptTemplate(
            input_variables=["transcript", "field_names", "feedback"],
            template="""
            Analyze the following transcript from a financial advisor and extract information for the following fields: {field_names}.
            
            Transcript: {transcript}
            
            Additional feedback: {feedback}
            
            Provide the extracted information for each field in a clear and concise manner.
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def analyze_transcript(self, transcript, feedback=""):
        st.subheader("Analyzing Transcript")
        with st.spinner("Analyzing..."):
            try:
                field_names = "Field 1, Field 2, Field 3"  # You can customize these field names
                result = self.chain.run(transcript=transcript, field_names=field_names, feedback=feedback)
                st.success("Analysis complete!")
                return self._parse_result(result)
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                return None

    def _parse_result(self, result):
        # This is a simple parsing method. You might need to adjust it based on the actual output format.
        fields = result.split('\n\n')
        return {f"Field {i+1}": field.split(': ', 1)[1] for i, field in enumerate(fields)}