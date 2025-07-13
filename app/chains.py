import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()

class Chain:
    def __init__(self):
        self.llm = ChatGroq(
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant"
    )
    
    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}

            ### INSTRUCTION:
            You are an expert job posting extractor. The above content is scraped from a job listing website.

            Your task is to extract all relevant job postings from the text and return them in **strict JSON format**.

            Each JSON object must contain the following keys:
            - "role"
            - "experience"
            - "skills"
            - "description"

            Do NOT include any introduction, explanation, or preamble.  
            Respond with **JSON only** — not Markdown, not prose, just the JSON.  
            Do NOT use triple backticks or text like "Here is the JSON:"  
            If information is missing, use an empty string.

            ### OUTPUT FORMAT:
            [
            {{
                "role": "...",
                "experience": "...",
                "skills": "...",
                "description": "..."
            }},
            ...
            ]
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res,list) else [res]
    
    def write_mail(self,job,links):
        prompt_email = PromptTemplate.from_template(
                """
                no preamble, just the email content.

                ### JOB DESCRIPTION:
                {job_description}

                ### RELEVANT PORTFOLIO LINKS:
                {link_list}

                ### INSTRUCTIONS:
                Write a cold email tailored to the job above, following these formatting rules:

                1. Start directly with the email content (no introductory text).

                2. Structure the email like this:
                Subject: [Your Subject Line]

                [Opening paragraph expressing enthusiasm for the role and company]
                <Then, generate an actual enthusiastic opening paragraph here>

                [Bullet-point list of relevant projects formatted exactly as:
                • Project Name: [ProjectName](project-link) - Brief description of relevance and technologies used (1-2 lines)]

                [Closing paragraph expressing interest in discussing further]

                Best regards,  
                Upendra Paluru

                3. Requirements:
                - Each project must use the exact bullet-point format shown above
                - Focus on how projects demonstrate required skills from the job description
                - Maintain consistent formatting for all project listings
                - Keep project descriptions concise and technology-focused

                4. Do NOT include:
                - Any text before "Subject:"
                - Any surrounding tags
                - Duplicated links or raw URLs
                - Paragraph-style project descriptions
                - Any explanation of the email's purpose

                Ensure the output looks like an actual, ready-to-send cold email.
                """
        )


        chain_email = prompt_email | self.llm
        res = chain_email.invoke({"job_description": str(job), "link_list": links})
        return res.content
    
        
if __name__ == "__main__":
    print(os.getenv("GROQ_API_KEY"))