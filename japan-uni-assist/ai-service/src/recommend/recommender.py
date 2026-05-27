from typing import List
from src.providers.manager import ProviderManager
from src.models.schemas import (
    StudentProfileInput, RecommendResponse, RecommendItem, RecommendCategory, ChatRequest, Message, TokenUsage
)

RECOMMEND_SYSTEM_PROMPT = """你是一位专业的日本留学顾问，擅长根据学生的背景条件匹配适合的日本大学院（修士课程）。

请根据学生的以下信息，推荐分别属于以下三类的日本大学：
1. 冲刺校（REACH）：略高于学生当前条件，需要努力争取
2. 稳妥校（TARGET）：与学生条件基本匹配，录取可能性较高
3. 保底校（SAFETY）：低于学生条件，录取把握很大

对每所学校，请提供：
- 学校名称（中文和日文）
- 匹配的具体研究科/专业
- 推荐理由（分析学生的GPA、语言成绩、背景与该校要求的匹配度）
- 匹配度分数（0-100）
- AI置信度（0-1）

请严格按照以下JSON格式输出，不要输出其他内容：
{
  "recommendations": [
    {
      "category": "REACH|TARGET|SAFETY",
      "university_name": "中文名",
      "university_name_jp": "日文名",
      "program_name": "研究科名",
      "reason": "推荐理由",
      "match_score": 85.0,
      "confidence": 0.8,
      "tuition_yen": 800000,
      "location": "东京"
    }
  ]
}"""

class Recommender:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager

    async def recommend(self, profile: StudentProfileInput, model: str = "gpt-4o") -> RecommendResponse:
        user_content = f"""学生背景：
- GPA: {profile.gpa}/4.0
- 英语考试: {profile.english_type} {profile.english_score}
- JLPT: {profile.jlpt_level or "无"}
- 本科院校: {profile.bachelor_school}
- 本科专业: {profile.bachelor_major}
- 目标专业: {profile.target_major or profile.bachelor_major}
- 年预算: {profile.budget_yen or "未指定"} 日元

请推荐3所冲刺校、3所稳妥校、3所保底校。"""

        messages = [
            Message(role="system", content=RECOMMEND_SYSTEM_PROMPT),
            Message(role="user", content=user_content)
        ]

        request = ChatRequest(messages=messages, model=model, temperature=0.4)
        response = await self.provider_manager.chat(request)

        import json
        try:
            data = json.loads(response.content)
            raw_items = data.get("recommendations", [])
        except json.JSONDecodeError:
            raw_items = self._parse_with_heuristics(response.content)

        items: List[RecommendItem] = []
        for item in raw_items:
            try:
                items.append(RecommendItem(
                    category=RecommendCategory(item.get("category", "TARGET")),
                    university_name=item.get("university_name", ""),
                    university_name_jp=item.get("university_name_jp", ""),
                    program_name=item.get("program_name", ""),
                    reason=item.get("reason", ""),
                    match_score=float(item.get("match_score", 50)),
                    confidence=float(item.get("confidence", 0.5)),
                    tuition_yen=item.get("tuition_yen"),
                    location=item.get("location")
                ))
            except Exception:
                continue

        return RecommendResponse(
            recommendations=items,
            model_used=response.model,
            usage=response.usage
        )

    def _parse_with_heuristics(self, text: str) -> List[dict]:
        import re
        items = []
        blocks = re.split(r'\n\n+', text)
        for block in blocks:
            if not block.strip():
                continue
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            item = {}
            for line in lines:
                if '校' in line and ('REACH' in line or 'TARGET' in line or 'SAFETY' in line):
                    for cat in ['REACH', 'TARGET', 'SAFETY']:
                        if cat in line:
                            item['category'] = cat
                if line.startswith('-') or line.startswith('*'):
                    if '大学' in line or '学校' in line:
                        item['university_name'] = line.strip('- *').split(':')[-1].strip()
                    elif '研究科' in line or '专业' in line:
                        item['program_name'] = line.strip('- *').split(':')[-1].strip()
                    elif '理由' in line:
                        item['reason'] = line.strip('- *').split(':')[-1].strip()
            if item.get('university_name'):
                item.setdefault('match_score', 50)
                item.setdefault('confidence', 0.5)
                items.append(item)
        return items