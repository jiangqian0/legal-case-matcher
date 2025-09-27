import os
from flask import Flask, render_template, request, jsonify
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# 手动处理CORS（避免安装flask-cors）
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

class LegalCaseMatcher:
    def __init__(self):
        self.cases = []
        self.vectorizer = TfidfVectorizer(max_features=500)
        self.load_data()
    
    def load_data(self):
        """加载案例数据"""
        try:
            with open('sample_cases.json', 'r', encoding='utf-8') as f:
                self.cases = json.load(f)
            
            texts = [f"{case.get('title', '')} {case.get('content', '')}" for case in self.cases]
            if texts:
                self.case_vectors = self.vectorizer.fit_transform(texts)
                print(f"成功加载 {len(self.cases)} 个案例")
            else:
                self.case_vectors = None
                print("没有找到案例数据")
                
        except Exception as e:
            print(f"数据加载失败: {e}")
            self.cases = [
                {
                    "id": 1, "title": "系统就绪", "content": "请输入案件描述进行搜索", 
                    "category": "系统", "outcome": "运行中"
                },
                {
                    "id": 2, "title": "劳动合同纠纷案例", 
                    "content": "员工因公司违法解除劳动合同要求经济赔偿金，法院支持原告诉求。",
                    "category": "劳动法", "outcome": "原告胜诉"
                }
            ]
            texts = [f"{case.get('title', '')} {case.get('content', '')}" for case in self.cases]
            self.case_vectors = self.vectorizer.fit_transform(texts)

    def search(self, query, top_k=5):
        """搜索相似案例"""
        if not self.cases or self.case_vectors is None:
            return [{"title": "示例案例", "content": "系统初始化中...", "similarity": 0.9}]
        
        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.case_vectors).flatten()
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    case = self.cases[idx].copy()
                    case['similarity'] = float(similarities[idx])
                    results.append(case)
            return results
        except Exception as e:
            print(f"搜索错误: {e}")
            return [{"title": "搜索出错", "content": f"错误信息: {str(e)}", "similarity": 0}]

# 初始化匹配器
matcher = LegalCaseMatcher()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET', 'POST'])
def search_cases():
    try:
        # 处理GET请求
        if request.method == 'GET':
            query = request.args.get('query', '劳动合同')
            top_k = int(request.args.get('top_k', 3))
            
            results = matcher.search(query, top_k=top_k)
            return jsonify({
                'query': query,
                'top_k': top_k,
                'results': results
            })
        
        # 处理POST请求
        elif request.method == 'POST':
            data = request.get_json()
            query = data.get('query', '')
            top_k = data.get('top_k', 5)
            
            results = matcher.search(query, top_k=top_k)
            return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test_search():
    """测试搜索"""
    results = matcher.search("劳动合同", top_k=2)
    return jsonify({'results': results})

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': '法律类案匹配系统',
        'case_count': len(matcher.cases)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 服务器启动在端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
