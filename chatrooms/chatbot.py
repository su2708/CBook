import os
from typing import Union, List, Dict
import requests
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.runnables import RunnablePassthrough, RunnableSequence
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.llm import LLMChain
from langchain.agents import Tool


# 환경 변수 로드
load_dotenv()

# 환경 변수에서 OpenAI API 키를 불러오기
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("OPENAI_API_KEY 환경 변수를 설정해주세요.")

# 네이버 clinet 값 불러오기
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
if not NAVER_CLIENT_ID:
    print("NAVER_CLIENT_ID 환경 변수를 설정해주세요.")

NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
if not NAVER_CLIENT_SECRET:
    print("NAVER_CLIENT_SECRET 환경 변수를 설정해주세요.")

NAVER_BOOKS_URL = "https://openapi.naver.com/v1/search/book.json?"

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
    """
    user_query: str
    action: str
    search_keywords: str
    author: str

class ChatNormallyInput(BaseModel):
    """
    사용자 질문: str
    과거 채팅 기록: str | List | Dict
    """
    user_msg: str
    content: Union[str, List, Dict]


# tool setting: 도서 검색
@tool
def search_books(query: str, k: int = 5):
    """
    네이버 도서 검색 API를 사용하여 도서를 검색합니다.

    Args:
        query (str): 검색어
        k (int): 반환할 결과 수 (기본값 5)

    Returns:
        list: 검색 결과 (책 정보 리스트)
    """
    search_results = []

    while True:
        query = query.strip()

        if not query:
            continue

        if query.lower() in ["q", "quit"]:
            print("\n👋 검색을 종료합니다.")
            break

        try:
            print(f"\n'{query}' 검색을 시작합니다...")

            # HTTP 요청 헤더 설정
            headers = {
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            }

            # 요청 파라미터 설정
            params = {"query": query, "display": k}

            # API 요청 보내기
            response = requests.get(NAVER_BOOKS_URL, headers=headers, params=params)
            response.raise_for_status()  # 요청 에러 확인

            data = response.json()
            items = data.get("items", [])

            search_results = search_results + items
            print(f"\n✨ 검색 완료! {len(search_results)}개의 결과를 찾았습니다.\n")

            # 종료
            break

        except Exception as e:
            print(f"\n❌ 검색 중 오류가 발생했습니다: {str(e)}")

    return search_results

# tools 설정
tools = [
    Tool(
        name="Search Books",
        func=search_books,
        description="질문에 맞는 책을 검색합니다."
    )
]


# 검색 Agent 설정
class AIAgent:
    def __init__(self, llm):
        self.llm = llm

    def analyze_query(self, user_query):
        """
        LLM을 사용하여 유저 쿼리를 분석하고 그 결과를 반환.
        """
        self.output_parser = PydanticOutputParser(pydantic_object=SearchResult)

        self.prompt = PromptTemplate(
            input_variables=["user_query"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            },
            template="""
            당신은 일반적인 챗봇입니다.
            다만 도서 관련 질문의 경우 도서 관련 정보를 제공하세요.
            
            먼저 입력된 질의가 도서 관련 내용인지 확인하세요.

            도서 관련 주제 판단 기준:
            1. 질문에 도서 제목, 저자, 출판사, 출판 연도, 장르 등의 키워드가 포함되어 있는지 확인하세요.
            2. 질문의 의도가 도서 정보를 요구하거나 책 추천을 요청하는지 분석하세요.
            3. 도서 선택, 세부 정보, 리뷰, 활용과 관련된 일반적인 주제인지 판단하세요.
            4. 질의 유형이 정보 검색형인지, 도서 추천 의도가 있는지 확인하세요.
            5. 도서와 관련 없는 질문(예: \"책상 추천\")은 제외하세요.
            6. 검색된 키워드 문자열의 마지막에 '책'은 붙이지 말아주세요.

            도서 관련 질의가 아닌 경우:
            - action을 "chat_normally"로 설정
            - search_keyword는 빈 문자열로 설정 
            
            도서 관련 질의인 경우 다음 작업을 수행하세요:
            - action을 "search_books"로 설정 
            - 키워드 추출: 최적화 검색어 생성

            키워드 추출 규칙:
            1. 핵심 주제어 분리
            - 도서 관련 핵심 개념 추출
            - 보조어 및 조사 제거

            2. 의미론적 최적화
            - 전문 용어 완전성 유지
            - 개념 간 관계성 보존
            - 맥락 적합성 확보
            
            저자 추출 규칙:
            - 도서의 저자에 대한 질문은 저자 이름만 골라내어 "author"로 저장해주세요.

            분석 대상 질의: {user_query}

            {format_instructions}
            """,
        )

        # 실행 체인 생성 - 프롬프트 처리부터 결과 파싱까지의 전체 흐름 
        self.chain = RunnableSequence(
            first={"user_query": RunnablePassthrough()}
            | self.prompt,  # 먼저 프롬프트 처리 
            middle=[self.llm],  # 그 다음 LLM으로 처리 
            last=self.output_parser,  # 마지막으로 결과 파싱 
        )

        response = self.chain.invoke(user_query)  # 질문 분석 
        print(response)

        return response.model_dump()  # json 형식으로 변형 


######################### 답변하는 부분 #########################

# Agent 초기화
agent = AIAgent(llm=LLM)


def chatbot(user_message):
    # 1. 사용자 질문 분석 
    chat_history = user_message["chat_history"]
    user_msg = user_message["user_msg"]
    result = agent.analyze_query(user_msg)
    
    # 2. 분석 결과에 따른 챗봇 답변 시작 
    
    # 2-1. 책 검색
    if result["action"] == "search_books":
        search_results = search_books(result["search_keywords"])
        
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
    
    # 2-2. 일반적인 챗봇
    else:
        """
        일반적인 챗봇 기능을 수행합니다.
        """
        output_parser = PydanticOutputParser(pydantic_object=ChatNormallyInput)
        
        template = [(
            "system",
            """
            당신은 유용한 AI 챗봇입니다.
            아래의 대화를 보고 마지막 user의 질문에 답하세요.
            최종 답변은 하나의 문자열이어야 합니다.
            """
        )] + chat_history + [("user", "{question}")]
        
        prompt = ChatPromptTemplate(
            messages=template,
            partial_variables={"format_instructions": output_parser.get_format_instructions()}
        )

        chain = {"question": RunnablePassthrough()} | prompt | LLM
        
        try:
            response = chain.invoke(user_msg).content 
            return response
        except Exception as e:
            raise ValueError(f"Parsing Error: {e}")


### 동작 테스트 
# while True:
#     query = input("질문을 입력하세요: ")
#     print(f"user: {query}")

#     try:
#         if query.lower() in ["q", "quit"]:
#             print("\n👋 대화를 종료합니다.")
#             break
        
#         response = chatbot(query)
#         print(f"ai: {response}")

#     except Exception as e:
#         print(f"\n❌ 검색 중 오류가 발생했습니다: {str(e)}")