from flask import Flask, render_template, request, jsonify
import json
import os
from legal_matcher import LegalCaseMatcher

app = Flask(__name__)
matcher = LegalCaseMatcher()

# 加载示例数据
@app.before_first_request
def load_data():
    try:
        with open('sample_cases.json', 'r', encoding='utf-8') as f:
            cases = json.load(f)
        matcher.load_cases(cases)
        print(f"成功加载 {len(cases)} 个案例")
    except Exception as e:
        print(f"加载数据失败: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_cases():
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        results = matcher.search(query, top_k=top_k)
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': '法律类案匹配系统'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)