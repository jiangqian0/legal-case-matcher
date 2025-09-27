import os
from flask import Flask, render_template, request, jsonify
import json
import re

app = Flask(__name__)

# 手动处理CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

class SimpleLegalMatcher:
    def __init__(self):
        self.cases = self.load_data()
        print(f"✅ 初始化完成，加载 {len(self.cases)} 个案例")
    
    def load_data(self):
        """加载案例数据"""
        try:
            with open('sample_cases.json', 'r', encoding='utf-8') as f:
                cases = json.load(f)
                print("✅ 成功从文件加载案例数据")
                return cases
        except Exception as e:
            print(f"❌ 文件加载失败: {e}")
            # 提供内置数据
            return [
                {
                    "id": 1,
                    "title": "劳动合同纠纷案例",
                    "content": "员工因公司违法解除劳动合同要求经济赔偿金，法院支持原告诉求。",
                    "category": "劳动法",
                    "outcome": "原告胜诉"
                },
                {
                    "id": 2, 
                    "title": "交通事故赔偿案例",
                    "content": "机动车与行人发生交通事故，根据责任认定判决相应赔偿金额。",
                    "category": "侵权法", 
                    "outcome": "部分支持"
                },
                {
                    "id": 3,
                    "title": "民间借贷纠纷案例", 
                    "content": "被告向原告借款未还，法院根据借条和转账记录判决归还本金及利息。",
                    "category": "民法",
                    "outcome": "原告胜诉"
                },
                {
                    "id": 4,
                    "title": "房屋买卖合同纠纷",
                    "content": "买方因卖方隐瞒房屋质量问题要求解除合同，法院认定卖方存在欺诈行为。",
                    "category": "合同法",
                    "outcome": "买方胜诉"
                },
                {
                    "id": 5,
                    "title": "知识产权侵权案",
                    "content": "原告指控被告侵犯其软件著作权，法院认定侵权成立判决赔偿损失。",
                    "category": "知识产权法",
                    "outcome": "原告胜诉"
                }
            ]
    
    def simple_search(self, query, top_k=5):
        """改进的文本匹配搜索"""
        if not query:
            return []
        
        results = []
        for case in self.cases:
            # 组合所有文本进行匹配
            full_text = f"{case['title']} {case['content']} {case['category']} {case['outcome']}".lower()
            query_lower = query.lower()
            
            # 计算匹配分数
            score = 0
            
            # 1. 完全匹配（高权重）
            if query_lower in full_text:
                score += 10
            
            # 2. 关键词匹配
            keywords = query_lower.split()
            matched_keywords = 0
            for keyword in keywords:
                if len(keyword) > 1 and keyword in full_text:  # 避免单字匹配
                    matched_keywords += 1
                    score += 2
            
            # 3. 部分匹配（宽松匹配）
            for keyword in keywords:
                if len(keyword) > 2:
                    for word in full_text.split():
                        if keyword in word:
                            score += 1
                            break
            
            # 4. 类别匹配额外加分
            if any(keyword in case['category'] for keyword in keywords if len(keyword) > 1):
                score += 3
            
            if score > 0:
                case_copy = case.copy()
                case_copy['similarity'] = min(score / 20.0, 0.99)  # 归一化到0-1之间
                case_copy['score'] = score  # 调试用
                results.append(case_copy)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 只返回前top_k个结果
        return results[:top_k]

# 初始化匹配器
matcher = SimpleLegalMatcher()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET', 'POST'])
def search_cases():
    try:
        # 处理GET请求
        if request.method == 'GET':
            query = request.args.get('query', '劳动合同')
            top_k = int(request.args.get('top_k', 5))
            
            if not query or query.strip() == '':
                query = '劳动合同'  # 默认查询词
            
            results = matcher.simple_search(query, top_k=top_k)
            return jsonify({
                'query': query,
                'top_k': top_k,
                'results_count': len(results),
                'results': results
            })
        
        # 处理POST请求
        elif request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            top_k = data.get('top_k', 5)
            
            if not query or query.strip() == '':
                return jsonify({'error': '查询内容不能为空'}), 400
            
            results = matcher.simple_search(query, top_k=top_k)
            return jsonify({
                'results': results,
                'results_count': len(results)
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test_search():
    """测试搜索"""
    results = matcher.simple_search("劳动合同", top_k=3)
    return jsonify({
        'message': '测试搜索成功',
        'results': results
    })

@app.route('/api/debug')
def debug_info():
    """调试信息"""
    return jsonify({
        'status': 'healthy',
        'case_count': len(matcher.cases),
        'sample_titles': [case['title'] for case in matcher.cases[:3]],
        'endpoints': {
            '搜索测试': '/api/search?query=劳动合同',
            '调试信息': '/api/debug',
            '健康检查': '/api/health'
        }
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': '法律类案匹配系统',
        'case_count': len(matcher.cases),
        'version': '2.0 - 修复搜索算法'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 服务器启动在端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
