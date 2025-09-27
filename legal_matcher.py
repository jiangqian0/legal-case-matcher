import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class LegalCaseMatcher:
    def __init__(self):
        self.cases = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self.case_vectors = None
    
    def load_cases(self, cases):
        """加载案例数据"""
        self.cases = cases
        # 提取案例文本用于向量化
        texts = [f"{case.get('title', '')} {case.get('content', '')}" 
                for case in cases]
        
        if texts:
            self.case_vectors = self.vectorizer.fit_transform(texts)
        else:
            self.case_vectors = None
    
    def search(self, query, top_k=5):
        """搜索相似案例"""
        if not self.cases or self.case_vectors is None:
            return []
        
        # 将查询文本向量化
        query_vec = self.vectorizer.transform([query])
        
        # 计算相似度
        similarities = cosine_similarity(query_vec, self.case_vectors).flatten()
        
        # 获取最相似的案例
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # 只返回有相似度的结果
                case = self.cases[idx].copy()
                case['similarity'] = float(similarities[idx])
                results.append(case)
        
        return results