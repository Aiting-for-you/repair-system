import re
import json
import requests

# 读取schoolRepairItems.ts
with open('schoolRepairItems.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取学校和项目
school_blocks = re.findall(r'\{\s*schoolId: \d+,.*?items: \[(.*?)\]\s*\}', content, re.S)
school_names = [
    '两江职业教育中心',
    '重庆市育才中学'
]
schools = []
for idx, block in enumerate(school_blocks):
    items = re.findall(r'\{\s*id: \d+,\s*name: "(.*?)",\s*basePrice: (\d+)\s*\}', block)
    schools.append({
        'name': school_names[idx],
        'items': [{'name': name, 'price': float(price)} for name, price in items]
    })

# 调用API导入
resp = requests.post('http://127.0.0.1:5001/api/dev/import_school_repair_items', json={'schools': schools})
print(resp.text) 