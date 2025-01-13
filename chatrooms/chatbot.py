from langchain_core.runnables import RunnablePassthrough
from langchain.agents import AgentExecutor, ConversationalAgent, create_tool_calling_agent
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains.llm import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.tools import Tool

from AIBookAgent.aladin import search_aladin
from AIBookAgent.hybridRAG import AIBooksRAG

from typing import Union, List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
from bs4 import BeautifulSoup

import numpy as np
import requests
import pickle
import faiss
import json
import os



# 환경 변수 로드
load_dotenv()

# 환경 변수에서 OpenAI API 키를 불러오기
openai_api_key = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")

# 알라딘 Key 값 불러오기
ALADIN_API_KEY = os.getenv("ALADIN_API_KEY")

# 벡터스토어 경로 불러오기 
JSON_DIR = os.getenv("JSON_DIR")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH")
METADATA_PATH = os.getenv("METADATA_PATH")

LLM = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    api_key=openai_api_key,
)


# 검색 결과 자료형 설정
class SearchResult(BaseModel):
    """
    사용자 질문: str
    액션: str
    검색 키워드: str
    저자: str
    과거 채팅 기록: str | List | Dict
    """
    user_query: str
    action: str
    search_keywords: str
    author: str
    content: Union[str, List, Dict]

# 검색 Agent 설정
class AIAgent:
    def __init__(self, llm):
        self.llm = llm

    def analyze_query(self, user_query, chat_history):
        """
        LLM을 사용하여 유저 쿼리를 분석하고 그 결과를 반환.
        """
        self.output_parser = PydanticOutputParser(pydantic_object=SearchResult)
        
        self.template = [SystemMessage(content=
            """
            당신은 유용한 AI 챗봇입니다.
            
            주어진 대화 내역과 사용자의 마지막 질문을 기반으로, 질문이 다음 세 가지 카테고리 중 어디에 속하는지 판단하세요:
            
            1. **도서 검색 관련 질문**:
            - 질문에 도서 제목, 저자, 출판사, 출판 연도, 장르 등의 키워드가 포함되어 있는 경우
            - 질문의 의도가 도서 정보를 요구하거나 책 추천을 요청하는 경우
            - 도서 선택, 세부 정보, 리뷰, 활용과 관련된 일반적인 주제인 경우 

            2. **시험 계획 생성 관련 질문**:
            - 사용자가 특정 시험(예: 수능, 자격증 시험)과 관련된 학습 계획, 스케줄링, 목차 활용 방안, 공부 전략 등에 대해 질문하거나 논의한 경우.
            - 질문 내용에 "시험", "학습 계획", "목차 활용", "스케줄", "공부 방법"과 같은 키워드가 포함되어 있거나 학습과 관련된 계획 생성에 대한 요청이 있는 경우.

            3. **일반 대화 질문**:
            - 위 두 가지 카테고리에 속하지 않는 질문.
            - 기술적인 세부사항 없이 단순한 의견 교환, 비관련 질문, 또는 일반적인 주제(예: 일상, 잡담, 다른 기술 도구 관련 논의 등)에 대한 질문.
            
            1번 도서 검색 관련 질문인 경우 다음 작업을 수행하세요.
            - action을 "search_books"로 설정 
            - content는 빈 문자열로 설정 
            - author를 저자 추출 규칙에 따라 설정 
                저자 추출 규칙:
                - 도서의 저자에 대한 질문은 저자 이름만 골라내어 "author"로 저장해주세요.
            - 키워드 추출: 최적화 검색어 생성
                키워드 추출 규칙:
                1) 핵심 주제어 분리
                - 도서 관련 핵심 개념 추출
                - 보조어 및 조사 제거

                2) 의미론적 최적화
                - 전문 용어 완전성 유지
                - 개념 간 관계성 보존
                - 맥락 적합성 확보
            
            2번 시험 계획 생성 관련 질문인 경우 다음 작업을 수행하세요.
            - action을 "make_plans"로 설정
            - content, author는 빈 문자열로 설정 
            - 키워드 추출: 최적화 검색어 생성
                키워드 추출 규칙:
                1) 핵심 주제어 분리
                - 도서 관련 핵심 개념 추출
                - 보조어 및 조사 제거

                2) 의미론적 최적화
                - 전문 용어 완전성 유지
                - 개념 간 관계성 보존
                - 맥락 적합성 확보
            
            3번 일반 대화 질문인 경우 다음 작업을 수행하세요.
            - action을 "basic_chat"으로 설정
            - search_keyword, author, content는 빈 문자열로 설정
            
            3가지 답변 모두 절대로 마크다운 문법을 사용하지 않고 반드시 아래의 json 형식을 갖는 문자열로 작성하세요.
                "action": "",
                "search_keyword": "",
                "author": "",
                "content": "",
            """
        )] + chat_history + [HumanMessage(content="{user_query}")]
        
        self.prompt = ChatPromptTemplate(
            messages=self.template,
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        self.chain = {"question": RunnablePassthrough()} | self.prompt | LLM
        
        try:
            response = self.chain.invoke(user_query).content 

            return response
        except Exception as e:
            raise ValueError(f"Parsing Error: {e}")


# tool setting: 도서 검색
@tool
def search_books(query: str, k: int = 5):
    """
    책을 검색하는 함수 
    먼저 AIBookRAG의 hybrid 검색을 이용
    만약 hybrid 검색 결과가 없거나 신뢰도가 낮다면 그냥 알라딘에서 검색 
    """
    book_rag = AIBooksRAG()
    
    # 벡터스토어 로드
    book_rag.load_vector_store()

    # BM25 초기화
    book_rag.initialize_bm25()

    # 하이브리드 검색
    results = book_rag.hybrid_search(query, k=5)
    
    # 하이브리드 검색 결과의 점수가 낮은 경우 알라딘에서 직접 책 검색 
    if results[0][1] >= 0.5:
        print(f"\n✨ 검색 완료! {len(results)}개의 결과를 찾았습니다.\n")
        books = []
        for result in results:
            books.append(result[0])
        return books
    else:
        books = search_aladin(query, k)
        print(f"\n✨ 검색 완료! {len(books)}개의 결과를 찾았습니다.\n")
        
        return books

# tool setting: 시험 계획 생성 
@tool
def make_plans(query: str, chat_history):
    """
    과거 대화 내역을 바탕으로 시험 계획을 생성하는 함수 
    """
    output_parser = PydanticOutputParser(pydantic_object=SearchResult)
    
    template = [SystemMessage(content=
        """
        당신은 시험 계획을 세워주는 AI 챗봇입니다.
        과거의 대화 내역에서 사용자의 마지막 질문과 관련된 책의 정보가 있다면 그 책의 목차를 활용해 학습 계획을 만들어주세요.

        아래의 절차를 따라 시험 계획을 만들어주세요.
        1. action, search_keywords, author는 빈 문자열로 설정
        2. content에 작성한 계획을 문자열로 저장 
        
        작성 예시를 보고 형식에 맞게 계획을 작성하세요.
        - 작성 예시
            시험 계획1:
            <시험일>2025/03/11
            <장소>스파르타고등학교
            <계획>2025/01/04 ~ 2025/01/06,1단원|2025/01/08,2단원|2025/01/13,3단원
            <끝>
            
            시험 계획1:
            <시험일>2025/04/05
            <장소>
            <계획>2025/02/04~2025/02/06,1단원|2025/02/08,2단원|2025/02/13,3~4단원
            <끝>

        과거의 대화 내역에 책에 대한 정보가 없다면 일반적인 지식으로 학습 계획을 만드세요.
        
        아래의 대화를 보고 시험 계획을 생성하세요. 
        """
    )] + chat_history + [HumanMessage(content="{question}")]
    
    prompt = ChatPromptTemplate(
        messages=template,
        partial_variables={"format_instructions": output_parser.get_format_instructions()}
    )

    chain = {"question": RunnablePassthrough()} | prompt | LLM
    
    try:
        response = chain.invoke(query).content 
        return response
    except Exception as e:
        raise ValueError(f"Parsing Error: {e}")

# tool setting: 일반 대화
def do_nothing(*args, **kwargs):  # 빈 함수 생성 
    pass

@tool
def basic_chat(query: str, chat_history, on_tool_start=do_nothing):
    """
    과거 대화 내역을 바탕으로 일반적인 대화를 진행하는 함수 
    """
    tool.on_
    output_parser = PydanticOutputParser(pydantic_object=SearchResult)
    
    template = [(
        "system",
        """
        당신은 유용한 AI 챗봇입니다.
        
        아래의 절차에 따라 답변을 만들어주세요.
        1. action, search_keywords, author는 빈 문자열로 설정
        2. content에 답변을 문자열로 저장 
        
        아래의 대화 내역을 참고해 사용자의 마지막 질문에 대한 답을 해주세요.
        """
    )] + chat_history + [("user", "{question}")]
    
    prompt = ChatPromptTemplate(
        messages=template,
        partial_variables={"format_instructions": output_parser.get_format_instructions()}
    )

    chain = {"question": RunnablePassthrough()} | prompt | LLM
    
    response = chain.invoke(query).content 
    return response

# tools 설정
tools = [
    Tool(
        name="Search Books",
        func=search_books,
        description="질문에 맞는 책을 검색합니다."
    ),
    Tool(
        name="Make Plans",
        func=make_plans,
        description="대화 내역을 바탕으로 계획을 생성합니다. "
    ),
    Tool(
        name="Basic Chat",
        func=basic_chat,
        description="대화 내역을 참고해 일반적인 대화를 진행합니다."
    )
]


######################### 답변하는 부분 #########################

# Agent 초기화
agent = AIAgent(llm=LLM)


def chatbot(user_message):
    # 1. 사용자 질문 분석 
    chat_history = user_message["chat_history"]
    user_query = user_message["user_msg"]
    result = agent.analyze_query(user_query, chat_history)
    print(result)
    result = json.loads(result)
    
    # 2. 분석 결과에 따른 챗봇 답변 시작 
    
    # 2-1. 책 검색
    if result["action"] == "search_books":
        search_results = search_books(result["search_keyword"])
        
        if search_results:
            print({
                "message": "도서 검색 결과입니다.",
                "content": search_results
            })
            return search_results
        else:
            print({
                "message": "검색 결과가 없습니다.",
                "content": search_results
            })
            return search_results
    
    # 2-2. 시험 계획 생성 
    elif result["action"] == "make_plans":
        plan = make_plans(user_query, chat_history)
        
        if plan:
            print({
                "message": "생성된 학습 계획입니다.",
                "content": plan
            })
            return plan
        else:
            print({
                "message": "계획이 생성되지 않았습니다.",
                "content": plan
            })
            return plan
    
    # 2-3. 일반적인 챗봇
    else:
        response = basic_chat(user_query, chat_history)
        
        if response:
            print({
                "message": "답변이 생성되었습니다.",
                "content": response
            })
        else:
            print({
                "message": "답변이 생성되지 않았습니다.",
                "content": response
            })