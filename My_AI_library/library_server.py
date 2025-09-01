from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from docx import Document  
import PyPDF2
import jieba  # 新增：用于中文分词
import re
from collections import Counter
from volcenginesdkarkruntime import Ark  # 新增：豆包大模型SDK

# 初始化Flask应用
app = Flask(__name__)

# 配置CORS，允许所有域名访问
CORS(app, 
     origins=["*"],  # 允许所有来源
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 允许的HTTP方法（新增PUT）
     allow_headers=["Content-Type", "Authorization"]  # 允许的请求头
)

# 配置
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'  # 存储知识库数据
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATA_FOLDER'] = DATA_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}

# 数据文件路径
KNOWLEDGE_BASES_FILE = os.path.join(DATA_FOLDER, 'knowledge_bases.json')
DOCUMENTS_FILE = os.path.join(DATA_FOLDER, 'documents.json')

# 豆包大模型配置
ARK_API_KEY = "aba732fd-b2a9-4e60-819d-64e0b5e622fe"
ARK_MODEL = "doubao-1-5-pro-32k-250115"

# 初始化豆包客户端
ark_client = Ark(api_key=ARK_API_KEY)

# 内存存储
knowledge_bases = []
documents = []

# 初始化数据存储
def init_data_storage():
    global knowledge_bases, documents
    
    # 加载知识库数据
    if os.path.exists(KNOWLEDGE_BASES_FILE):
        try:
            with open(KNOWLEDGE_BASES_FILE, 'r', encoding='utf-8') as f:
                knowledge_bases = json.load(f)
            print(f"✅ 已加载 {len(knowledge_bases)} 个知识库")
        except Exception as e:
            print(f"❌ 加载知识库数据失败: {e}")
            knowledge_bases = []
    else:
        knowledge_bases = []
        save_knowledge_bases()
    
    # 加载文档数据
    if os.path.exists(DOCUMENTS_FILE):
        try:
            with open(DOCUMENTS_FILE, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            print(f"✅ 已加载 {len(documents)} 个文档")
        except Exception as e:
            print(f"❌ 加载文档数据失败: {e}")
            documents = []
    else:
        documents = []
        save_documents()

# 保存数据到文件
def save_knowledge_bases():
    try:
        with open(KNOWLEDGE_BASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(knowledge_bases, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"❌ 保存知识库数据失败: {e}")

def save_documents():
    try:
        with open(DOCUMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"❌ 保存文档数据失败: {e}")

# ------------------------------
# 2. 知识库管理接口
# ------------------------------

# 获取所有知识库列表
@app.route('/api/knowledge', methods=['GET'])
def get_knowledge_bases():
    try:
        return jsonify(knowledge_bases), 200
    except Exception as e:
        print(f"获取知识库列表失败: {e}")
        return jsonify({'error': f'获取知识库列表失败: {str(e)}'}), 500

# 创建知识库
@app.route('/api/knowledge', methods=['POST'])
def create_knowledge():
    try:
        data = request.get_json()
        if not data or '库名' not in data:
            return jsonify({'error': '缺少库名'}), 400
        
        # 检查是否重名
        if any(kb['name'] == data['库名'] for kb in knowledge_bases):
            return jsonify({'error': '知识库名称已存在'}), 400
        
        # 创建新知识库
        knowledge_id = str(uuid.uuid4())
        knowledge = {
            '_id': knowledge_id,
            'name': data['库名'],
            'description': data.get('库描述', ''),
            'prompt': data.get('提示词', '你是一个专业的知识库助手，请根据提供的文档内容回答用户的问题。'),  # 新增提示词字段
            'create_time': datetime.now().isoformat(),
            'document_count': 0
        }
        
        # 添加到内存并保存到文件
        knowledge_bases.append(knowledge)
        save_knowledge_bases()
        
        print(f"✅ 创建知识库成功: {data['库名']} (ID: {knowledge_id})")
        return jsonify({
            'id': knowledge_id,
            'message': '知识库创建成功'
        }), 201
    except Exception as e:
        print(f"创建知识库失败: {e}")
        return jsonify({'error': f'创建知识库失败: {str(e)}'}), 500

# 删除知识库
@app.route('/api/knowledge', methods=['DELETE'])
def delete_knowledge():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'error': '缺少知识库ID'}), 400
        
        knowledge_id = data['id']
        
        # 查找要删除的知识库
        knowledge_to_delete = None
        for i, kb in enumerate(knowledge_bases):
            if kb['_id'] == knowledge_id:
                knowledge_to_delete = knowledge_bases.pop(i)
                break
        
        if not knowledge_to_delete:
            return jsonify({'error': '知识库不存在'}), 404
        
        # 删除相关文档文件
        docs_to_remove = []
        for i, doc in enumerate(documents):
            if doc['knowledge_id'] == knowledge_id:
                # 删除服务器上的文件
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['file_name'])
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ 删除文件: {doc['file_name']}")
                docs_to_remove.append(i)
        
        # 从后往前删除文档记录（避免索引变化）
        for i in reversed(docs_to_remove):
            documents.pop(i)
        
        # 保存更新后的数据
        save_knowledge_bases()
        save_documents()
        
        print(f"✅ 删除知识库成功: {knowledge_to_delete['name']}")
        return jsonify({'message': '知识库删除成功'}), 200
    except Exception as e:
        print(f"删除知识库失败: {e}")
        return jsonify({'error': f'删除知识库失败: {str(e)}'}), 500

# 更新知识库信息（包括提示词）
@app.route('/api/knowledge/<knowledge_id>', methods=['PUT'])
def update_knowledge(knowledge_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        # 查找要更新的知识库
        knowledge_base = None
        for kb in knowledge_bases:
            if kb['_id'] == knowledge_id:
                knowledge_base = kb
                break
        
        if not knowledge_base:
            return jsonify({'error': '知识库不存在'}), 404
        
        # 更新知识库信息
        if 'name' in data:
            # 检查新名称是否重复
            if any(kb['name'] == data['name'] and kb['_id'] != knowledge_id for kb in knowledge_bases):
                return jsonify({'error': '知识库名称已存在'}), 400
            knowledge_base['name'] = data['name']
        
        if 'description' in data:
            knowledge_base['description'] = data['description']
        
        if 'prompt' in data:
            knowledge_base['prompt'] = data['prompt']
        
        knowledge_base['update_time'] = datetime.now().isoformat()
        
        # 保存更新
        save_knowledge_bases()
        
        print(f"✅ 更新知识库成功: {knowledge_base['name']}")
        return jsonify({
            'message': '知识库更新成功',
            'knowledge_base': knowledge_base
        }), 200
    except Exception as e:
        print(f"更新知识库失败: {e}")
        return jsonify({'error': f'更新知识库失败: {str(e)}'}), 500

# 新增：专门用于更新提示词的接口
@app.route('/api/knowledge/<knowledge_id>/prompt', methods=['PUT'])
def update_knowledge_prompt(knowledge_id):
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': '缺少提示词参数'}), 400
        
        # 查找要更新的知识库
        knowledge_base = None
        for kb in knowledge_bases:
            if kb['_id'] == knowledge_id:
                knowledge_base = kb
                break
        
        if not knowledge_base:
            return jsonify({'error': '知识库不存在'}), 404
        
        # 更新提示词
        knowledge_base['prompt'] = data['prompt']
        knowledge_base['update_time'] = datetime.now().isoformat()
        
        # 保存更新
        save_knowledge_bases()
        
        print(f"✅ 更新知识库提示词成功: {knowledge_base['name']}")
        return jsonify({
            'message': '提示词更新成功',
            'prompt': knowledge_base['prompt']
        }), 200
    except Exception as e:
        print(f"更新提示词失败: {e}")
        return jsonify({'error': f'更新提示词失败: {str(e)}'}), 500

# 新增：使用POST方法更新提示词（兼容方案）
@app.route('/api/knowledge/update_prompt', methods=['POST'])
def update_prompt_post():
    try:
        data = request.get_json()
        if not data or 'id' not in data or 'prompt' not in data:
            return jsonify({'error': '缺少必要参数（id和prompt）'}), 400
        
        knowledge_id = data['id']
        prompt = data['prompt']
        
        # 查找要更新的知识库
        knowledge_base = None
        for kb in knowledge_bases:
            if kb['_id'] == knowledge_id:
                knowledge_base = kb
                break
        
        if not knowledge_base:
            return jsonify({'error': '知识库不存在'}), 404
        
        # 更新提示词
        knowledge_base['prompt'] = prompt
        knowledge_base['update_time'] = datetime.now().isoformat()
        
        # 保存更新
        save_knowledge_bases()
        
        print(f"✅ 更新知识库提示词成功: {knowledge_base['name']}")
        return jsonify({
            'message': '提示词更新成功',
            'prompt': knowledge_base['prompt']
        }), 200
    except Exception as e:
        print(f"更新提示词失败: {e}")
        return jsonify({'error': f'更新提示词失败: {str(e)}'}), 500

# ------------------------------
# 4. 文件上传与处理接口
# ------------------------------

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 解析文件内容
def parse_file(file_path, file_type):
    content = ""
    try:
        if file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        elif file_type == 'docx':
            doc = Document(file_path)
            content = '\n'.join([para.text for para in doc.paragraphs])
        
        elif file_type == 'pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = '\n'.join([page.extract_text() for page in reader.pages])
        
    except Exception as e:
        print(f"解析文件失败: {e}")
    return content

# 上传文件到指定知识库
@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        knowledge_id = request.form.get('knowledge_id')
        if not knowledge_id:
            return jsonify({'error': '缺少知识库ID'}), 400
        
        # 检查知识库是否存在
        knowledge_base = None
        for kb in knowledge_bases:
            if kb['_id'] == knowledge_id:
                knowledge_base = kb
                break
        
        if not knowledge_base:
            return jsonify({'error': '知识库不存在'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 保存文件到服务器
            timestamp = datetime.now().timestamp()
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 解析文件内容
            file_type = filename.rsplit('.', 1)[1].lower()
            content = parse_file(file_path, file_type)
            
            # 创建文档记录
            file_id = str(uuid.uuid4())
            document = {
                '_id': file_id,
                'knowledge_id': knowledge_id,
                'file_name': filename,
                'original_name': file.filename,
                'file_type': file_type,
                'file_size': os.path.getsize(file_path),
                'upload_time': datetime.now().isoformat(),
                'content': content[:10000]  # 存储前10000字符
            }
            
            # 添加到内存并保存
            documents.append(document)
            save_documents()
            
            # 更新知识库文档计数
            knowledge_base['document_count'] += 1
            save_knowledge_bases()
            
            print(f"✅ 文件上传成功: {file.filename} -> {knowledge_base['name']}")
            return jsonify({
                'message': '文件上传成功',
                'file_id': file_id
            }), 201
        
        return jsonify({'error': '不支持的文件类型'}), 400
    except Exception as e:
        print(f"文件上传失败: {e}")
        return jsonify({'error': f'文件上传失败: {str(e)}'}), 500

# 获取知识库中的文档列表
@app.route('/api/knowledge/<knowledge_id>/documents', methods=['GET'])
def get_knowledge_documents(knowledge_id):
    try:
        # 查找属于该知识库的文档
        kb_documents = [doc for doc in documents if doc['knowledge_id'] == knowledge_id]
        
        # 返回文档列表（不包含content字段，减少数据传输）
        document_list = []
        for doc in kb_documents:
            doc_info = {
                '_id': doc['_id'],
                'original_name': doc['original_name'],
                'file_type': doc['file_type'],
                'file_size': doc['file_size'],
                'upload_time': doc['upload_time']
            }
            document_list.append(doc_info)
        
        return jsonify(document_list), 200
    except Exception as e:
        print(f"获取文档列表失败: {e}")
        return jsonify({'error': f'获取文档列表失败: {str(e)}'}), 500

# 新增：智能问答类 (集成ask.py的功能)
class IntelligentQA:
    def __init__(self):
        pass
    
    def preprocess_text(self, text):
        """文本预处理：分词并过滤"""
        if not text:
            return []
        words = jieba.lcut(str(text).lower())
        # 过滤掉长度小于2的词，保留中文和字母数字
        words = [word for word in words if len(word) >= 2 and (word.isalnum() or any('\u4e00' <= char <= '\u9fff' for char in word))]
        return words
    
    def calculate_similarity(self, query_words, document_content):
        """计算查询词与文档内容的相似度"""
        doc_words = self.preprocess_text(document_content)
        doc_word_set = set(doc_words)
        query_word_set = set(query_words)
        
        # 计算交集词数量
        common_words = query_word_set & doc_word_set
        if not common_words:
            return 0
        
        # 计算权重分数
        score = len(common_words)
        
        # 考虑词频权重
        doc_word_count = Counter(doc_words)
        for word in common_words:
            score += doc_word_count.get(word, 0) * 0.1
            
        return score
    
    def extract_relevant_sentences(self, query_words, content, max_sentences=3):
        """从文档内容中提取与查询相关的句子"""
        sentences = re.split(r'[。！？\n]', content)
        sentence_scores = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:  # 过滤太短的句子
                continue
                
            sentence_words = set(self.preprocess_text(sentence))
            query_word_set = set(query_words)
            common_words = sentence_words & query_word_set
            
            if common_words:
                # 计算句子得分
                score = len(common_words) / len(query_word_set) if query_word_set else 0
                sentence_scores.append((score, sentence))
        
        # 按得分排序并返回前几个句子
        sentence_scores.sort(reverse=True)
        return [sentence for score, sentence in sentence_scores[:max_sentences] if score > 0]
    
    def search_knowledge_base(self, query, knowledge_base_id, documents, top_k=5):
        """在指定知识库中搜索相关文档"""
        query_words = self.preprocess_text(query)
        if not query_words:
            return []
        
        # 筛选属于指定知识库的文档
        kb_documents = [doc for doc in documents if doc['knowledge_id'] == knowledge_base_id]
        
        if not kb_documents:
            return []
        
        # 计算每个文档的相似度
        scored_docs = []
        for doc in kb_documents:
            content = doc.get('content', '')
            if not content:
                continue
                
            similarity = self.calculate_similarity(query_words, content)
            if similarity > 0:
                scored_docs.append({
                    'document': doc,
                    'similarity': similarity,
                    'relevant_sentences': self.extract_relevant_sentences(query_words, content)
                })
        
        # 按相似度排序
        scored_docs.sort(key=lambda x: x['similarity'], reverse=True)
        return scored_docs[:top_k]
    
    def generate_answer(self, query, search_results, knowledge_base_name):
        """基于搜索结果生成答案 (优化版，类似ask.py的风格)"""
        if not search_results:
            return f"抱歉，在知识库「{knowledge_base_name}」中没有找到与「{query}」相关的信息。\n\n💡 建议：\n• 尝试使用不同的关键词\n• 上传更多相关文档\n• 检查输入的问题是否准确"
        
        # 提取查询关键词用于突出显示
        query_keywords = set(self.preprocess_text(query))
        
        # 构建详细答案 (参考ask.py的格式)
        answer = f"关于「{query}」的相关信息：\n\n"
        
        for i, result in enumerate(search_results, 1):
            doc = result['document']
            similarity = result['similarity']
            relevant_sentences = result['relevant_sentences']
            
            # 文档信息
            answer += f"📄 来源：{doc['original_name']} (关键词匹配数: {int(similarity)})\n"
            
            # 添加相关内容
            if relevant_sentences:
                answer += "重点内容：\n"
                for sentence in relevant_sentences:
                    if sentence.strip():
                        answer += f"• {sentence.strip()}\n"
            else:
                # 如果没有找到特别相关的句子，显示文档摘要
                content = doc.get('content', '')
                if content:
                    # 寻找包含关键词的句子
                    sentences = re.split(r'[。！？\n]', content)
                    relevant_found = []
                    for sentence in sentences:
                        if any(keyword in sentence for keyword in query_keywords):
                            relevant_found.append(sentence.strip())
                            if len(relevant_found) >= 3:
                                break
                    
                    if relevant_found:
                        answer += "相关内容：\n"
                        for sentence in relevant_found:
                            if sentence:
                                answer += f"• {sentence}\n"
                    else:
                        content_preview = content[:200].strip()
                        if content_preview:
                            answer += f"内容摘要：{content_preview}{'...' if len(content) > 200 else ''}\n"
            
            answer += "\n"
        
        # 添加智能建议
        if len(search_results) == 1:
            answer += "💡 提示：找到1个相关文档，如需更详细信息，建议查阅完整文档或上传更多相关资料。"
        else:
            answer += f"💡 提示：找到{len(search_results)}个相关文档，建议结合查看以获得更全面的了解。"
        
        return answer

# 实例化问答系统
qa_system = IntelligentQA()

# 测试连接接口
@app.route('/api/test', methods=['GET'])
def test_connection():
    try:
        return jsonify({
            'message': '服务器运行正常',
            'status': 'ok',
            'database': 'file_storage',
            'knowledge_bases_count': len(knowledge_bases),
            'documents_count': len(documents)
        }), 200
    except Exception as e:
        return jsonify({'error': f'服务器测试失败: {str(e)}'}), 500

# 获取系统统计信息
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_size = 0
        for doc in documents:
            total_size += doc.get('file_size', 0)
        
        return jsonify({
            'knowledge_bases_count': len(knowledge_bases),
            'documents_count': len(documents),
            'total_file_size': total_size,
            'storage_type': 'local_file'
        }), 200
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

# ------------------------------
# 3. 智能问答接口
# ------------------------------

# 智能问答接口（集成大模型）
@app.route('/api/query', methods=['POST'])
def intelligent_query():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        query = data.get('query', '').strip()
        knowledge_base_id = data.get('knowledge_base_id', '').strip()
        
        if not query:
            return jsonify({'error': '查询内容不能为空'}), 400
        
        if not knowledge_base_id:
            return jsonify({'error': '知识库ID不能为空'}), 400
        
        # 检查知识库是否存在
        knowledge_base = None
        for kb in knowledge_bases:
            if kb['_id'] == knowledge_base_id:
                knowledge_base = kb
                break
        
        if not knowledge_base:
            return jsonify({'error': '指定的知识库不存在'}), 404
        
        # 检查知识库是否有文档
        kb_documents = [doc for doc in documents if doc['knowledge_id'] == knowledge_base_id]
        if not kb_documents:
            return jsonify({
                'answer': f"知识库「{knowledge_base['name']}」中暂无文档。请先上传相关文档后再进行查询。",
                'llm_answer': "",
                'sources': [],
                'knowledge_base_name': knowledge_base['name']
            }), 200
        
        print(f"🔍 收到查询请求: \"{query}\" - 知识库: {knowledge_base['name']}")
        
        # 使用智能问答系统搜索相关文档
        search_results = qa_system.search_knowledge_base(
            query=query,
            knowledge_base_id=knowledge_base_id,
            documents=documents,
            top_k=5
        )
        
        # 生成传统匹配答案
        traditional_answer = qa_system.generate_answer(
            query=query,
            search_results=search_results,
            knowledge_base_name=knowledge_base['name']
        )
        
        # 准备大模型问答
        llm_answer = ""
        try:
            # 构建上下文内容
            context_content = ""
            if search_results:
                context_content = "相关文档内容：\n\n"
                for i, result in enumerate(search_results[:3], 1):  # 只取前3个最相关的结果
                    doc = result['document']
                    context_content += f"文档{i}：《{doc['original_name']}》\n"
                    
                    # 添加相关句子或内容摘要
                    if result['relevant_sentences']:
                        for sentence in result['relevant_sentences'][:2]:  # 每个文档最多2个句子
                            context_content += f"- {sentence.strip()}\n"
                    else:
                        # 如果没有相关句子，添加内容摘要
                        content = doc.get('content', '')
                        if content:
                            preview = content[:300].strip()
                            context_content += f"- {preview}{'...' if len(content) > 300 else ''}\n"
                    context_content += "\n"
            else:
                context_content = "暂无相关文档内容。"
            
            # 获取知识库的自定义提示词
            system_prompt = knowledge_base.get('prompt', '你是一个专业的知识库助手，请根据提供的文档内容回答用户的问题。')
            
            # 构建完整的提示词
            full_prompt = f"{system_prompt}\n\n{context_content}\n\n请基于以上内容回答用户的问题。如果文档中没有相关信息，请诚实说明，并提供一般性的建议。"
            
            # 调用豆包大模型
            completion = ark_client.chat.completions.create(
                model=ARK_MODEL,
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            llm_answer = completion.choices[0].message.content
            print(f"✅ 大模型回答生成成功")
            
        except Exception as e:
            print(f"❌ 大模型调用失败: {e}")
            llm_answer = f"抱歉，大模型服务暂时不可用。错误信息：{str(e)}"
        
        # 构建返回的来源信息
        sources = []
        for result in search_results:
            doc = result['document']
            sources.append({
                'document_name': doc['original_name'],
                'similarity': result['similarity'],
                'relevant_content': result['relevant_sentences'][:2]  # 只返回前2个相关句子
            })
        
        print(f"✅ 查询完成，找到 {len(search_results)} 个相关文档")
        
        return jsonify({
            'answer': traditional_answer,
            'llm_answer': llm_answer,
            'sources': sources,
            'knowledge_base_name': knowledge_base['name'],
            'query': query
        }), 200
        
    except Exception as e:
        print(f"❌ 智能问答失败: {e}")
        return jsonify({'error': f'智能问答失败: {str(e)}'}), 500

# ------------------------------
# 4. 文件上传与处理接口 (移动现有的上传接口到这里)
# ------------------------------

# ------------------------------
# 5. 静态文件服务
# ------------------------------

# 提供前端HTML页面
@app.route('/')
def index():
    return app.send_static_file('pagev1.html') if os.path.exists('pagev1.html') else "服务器运行中，请访问 /pagev1.html"

@app.route('/pagev1.html')
def frontend():
    if os.path.exists('pagev1.html'):
        with open('pagev1.html', 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "前端页面未找到", 404

@app.route('/test_public_access.html')
def test_page():
    if os.path.exists('test_public_access.html'):
        with open('test_public_access.html', 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "测试页面未找到", 404

@app.route('/pic/<filename>')
def serve_images(filename):
    """提供图片文件服务"""
    try:
        pic_path = os.path.join('pic', filename)
        if os.path.exists(pic_path):
            with open(pic_path, 'rb') as f:
                content = f.read()
            # 根据文件扩展名设置正确的MIME类型
            if filename.lower().endswith('.png'):
                return content, 200, {'Content-Type': 'image/png'}
            elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                return content, 200, {'Content-Type': 'image/jpeg'}
            elif filename.lower().endswith('.gif'):
                return content, 200, {'Content-Type': 'image/gif'}
            else:
                return content, 200, {'Content-Type': 'image/octet-stream'}
        else:
            return "图片未找到", 404
    except Exception as e:
        print(f"提供图片服务失败: {e}")
        return "图片服务错误", 500

if __name__ == '__main__':
    # 初始化数据存储
    print("🚀 启动智能知识库检索系统...")
    init_data_storage()
    
    print(f"📚 当前知识库数量: {len(knowledge_bases)}")
    print(f"📄 当前文档数量: {len(documents)}")
    print("=" * 50)
    
    # 启动Flask应用
    print("🌐 服务器启动中...")
    print("💡 本地访问地址: http://localhost:5000")
    print("🌍 公网访问地址: http://152.136.167.211:5000")
    print("� 前端页面: http://152.136.167.211:5000/pagev1.html")
    print("�📡 API接口地址: http://152.136.167.211:5000/api")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',    # 监听所有网络接口（允许公网访问）
        port=5000,         # 端口号
        debug=False,       # 生产环境关闭调试模式
        threaded=True      # 支持多线程
    )