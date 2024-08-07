import streamlit as st
import pyperclip

class UIComponents:
    def display_and_refine_fields(self, fields, gpt_service):
        st.subheader("Analysis Results")
        
        final_fields = fields.copy()
        
        for field_name, content in fields.items():
            st.write(f"**{field_name}:**")
            new_content = st.text_area(f"Edit {field_name}", value=content, height=150, key=field_name)
            final_fields[field_name] = new_content

        feedback = st.text_area("Provide additional feedback for refinement (optional)")
        
        if st.button("Refine Analysis"):
            transcript = "\n".join(final_fields.values())
            refined_fields = gpt_service.analyze_transcript(transcript, feedback)
            if refined_fields:
                final_fields = refined_fields
                st.success("Analysis refined based on feedback!")
            
        return final_fields

    def add_copy_buttons(self, fields):
        st.subheader("Copy Results")
        
        for field_name, content in fields.items():
            if st.button(f"Copy {field_name}"):
                pyperclip.copy(content)
                st.success(f"{field_name} copied to clipboard!")