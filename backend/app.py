# backend/app.py
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import datetime
import openpyxl
from PIL import Image, ImageDraw, ImageFont
import io
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///repair_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)  # 允许跨域请求，方便前后端分离开发
db = SQLAlchemy(app)

# --- 数据库模型 ---
class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    items = db.relationship('RepairItem', backref='school', lazy=True)

class RepairItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(32), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    school_name = db.Column(db.String(100), nullable=False)
    repair_person = db.Column(db.String(100), nullable=False)
    repair_location = db.Column(db.String(100), nullable=False)
    repair_time = db.Column(db.String(32), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.String(32), nullable=False)
    items = db.relationship('QuotationItem', backref='quotation', lazy=True)

class QuotationItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotation.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

# --- 内存数据存储 (后续可以替换为数据库) ---
schools = [
    {"id": 1, "name": "第一中学"},
    {"id": 2, "name": "实验小学"},
    {"id": 3, "name": "职业技术学院"}
]

repair_items = {
    1: [ # 第一中学的维修项目
        {"id": 101, "name": "更换灯管", "price": 20.0, "unit": "个"},
        {"id": 102, "name": "维修水龙头", "price": 50.0, "unit": "个"},
        {"id": 103, "name": "疏通下水道", "price": 100.0, "unit": "次"},
        {"id": 104, "name": "更换玻璃", "price": 80.0, "unit": "块"}
    ],
    2: [ # 实验小学的维修项目
        {"id": 201, "name": "课桌维修", "price": 30.0, "unit": "个"},
        {"id": 202, "name": "椅子维修", "price": 25.0, "unit": "个"},
        {"id": 203, "name": "投影仪灯泡更换", "price": 300.0, "unit": "个"}
    ],
    3: [ # 职业技术学院的维修项目
        {"id": 301, "name": "网络端口维修", "price": 60.0, "unit": "个"},
        {"id": 302, "name": "电脑系统重装", "price": 100.0, "unit": "台"},
        {"id": 303, "name": "服务器维护", "price": 500.0, "unit": "次"}
    ]
}

quotations = [] # 存储计价单
next_quotation_id = 1

# --- API 路由 ---

@app.route('/')
def home():
    """首页，返回欢迎信息"""
    return jsonify({"message": "欢迎使用维修计价系统 API"})

# --- 学校管理 ---
@app.route('/api/schools', methods=['GET'])
def get_schools():
    schools = School.query.all()
    return jsonify([{'id': s.id, 'name': s.name} for s in schools])

@app.route('/api/schools', methods=['POST'])
def add_school():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'error': '缺少学校名称'}), 400
    school = School(name=name)
    db.session.add(school)
    db.session.commit()
    return jsonify({'id': school.id, 'name': school.name}), 201

@app.route('/api/schools/<int:school_id>', methods=['PUT'])
def update_school(school_id):
    data = request.json
    name = data.get('name')
    school = School.query.get(school_id)
    if not school:
        return jsonify({'error': '未找到学校'}), 404
    school.name = name
    db.session.commit()
    return jsonify({'id': school.id, 'name': school.name})

@app.route('/api/schools/<int:school_id>', methods=['DELETE'])
def delete_school(school_id):
    school = School.query.get(school_id)
    if not school:
        return jsonify({'error': '未找到学校'}), 404
    db.session.delete(school)
    db.session.commit()
    return jsonify({'message': '已删除'})

# --- 维修项目管理 ---
@app.route('/api/schools/<int:school_id>/items', methods=['GET'])
def get_repair_items_by_school(school_id):
    items = RepairItem.query.filter_by(school_id=school_id).all()
    return jsonify([{'id': i.id, 'name': i.name, 'price': i.price, 'unit': i.unit} for i in items])

@app.route('/api/items', methods=['GET'])
def get_all_repair_items():
    items = RepairItem.query.all()
    result = []
    for item in items:
        school = School.query.get(item.school_id)
        result.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'unit': item.unit,
            'school_id': item.school_id,
            'school_name': school.name if school else '未知学校'
        })
    return jsonify(result)

@app.route('/api/items', methods=['POST'])
def add_repair_item():
    data = request.json
    school_id = data.get('school_id')
    name = data.get('name')
    price = data.get('price')
    unit = data.get('unit')
    if not all([school_id, name, price, unit]):
        return jsonify({'error': '缺少必要参数'}), 400
    item = RepairItem(name=name, price=float(price), unit=unit, school_id=school_id)
    db.session.add(item)
    db.session.commit()
    return jsonify({'id': item.id, 'name': item.name, 'price': item.price, 'unit': item.unit, 'school_id': item.school_id}), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_repair_item(item_id):
    data = request.json
    item = RepairItem.query.get(item_id)
    if not item:
        return jsonify({'error': '未找到项目'}), 404
    item.name = data.get('name', item.name)
    item.price = float(data.get('price', item.price))
    item.unit = data.get('unit', item.unit)
    db.session.commit()
    return jsonify({'id': item.id, 'name': item.name, 'price': item.price, 'unit': item.unit, 'school_id': item.school_id})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_repair_item(item_id):
    item = RepairItem.query.get(item_id)
    if not item:
        return jsonify({'error': '未找到项目'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': '项目已删除', 'item': {'id': item.id, 'name': item.name}})

# --- 价格计算 ---
@app.route('/api/calculate_price', methods=['POST'])
def calculate_price():
    """计算维修总价"""
    data = request.json
    selected_items = data.get('items', []) # 格式: [{'item_id': 101, 'quantity': 2, 'school_id': 1}, ...]
    total_price = 0

    for selected in selected_items:
        school_id = selected.get('school_id')
        item_id = selected.get('item_id')
        quantity = selected.get('quantity', 0)

        if not school_id or not item_id or quantity <= 0:
            continue

        items_at_school = RepairItem.query.filter_by(school_id=school_id).all()
        item_info = next((item for item in items_at_school if item.id == item_id), None)

        if item_info:
            total_price += item_info.price * quantity

    return jsonify({"total_price": round(total_price, 2)})

# --- 计价单管理 ---
@app.route('/api/quotations', methods=['POST'])
def submit_quotation():
    data = request.json
    school_id = data.get('school_id')
    selected_items_details = data.get('items', [])
    total_price = data.get('total_price')
    repair_person = data.get('repair_person', '未指定')
    repair_location = data.get('repair_location', '未指定')
    repair_time_str = data.get('repair_time')
    if not all([school_id, selected_items_details, total_price is not None, repair_time_str]):
        return jsonify({'error': '缺少必要参数，请确保所有字段都已填写'}), 400
    try:
        repair_time = datetime.datetime.fromisoformat(repair_time_str)
    except ValueError:
        return jsonify({'error': '维修时间格式不正确，请使用 ISO 格式 (例如 YYYY-MM-DDTHH:MM)'}), 400
    school = School.query.get(school_id)
    if not school:
        return jsonify({'error': '无效的学校ID'}), 400
    quotation_number = f"Q{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{int(datetime.datetime.now().timestamp())%1000:03d}"
    quotation = Quotation(
        quotation_number=quotation_number,
        school_id=school_id,
        school_name=school.name,
        repair_person=repair_person,
        repair_location=repair_location,
        repair_time=repair_time.isoformat(),
        total_price=total_price,
        created_at=datetime.datetime.now().isoformat()
    )
    db.session.add(quotation)
    db.session.commit()
    for item in selected_items_details:
        qitem = QuotationItem(
            quotation_id=quotation.id,
            item_id=item['item_id'],
            name=item['name'],
            price=item['price'],
            unit=item['unit'],
            quantity=item['quantity'],
            subtotal=item['subtotal']
        )
        db.session.add(qitem)
    db.session.commit()
    return jsonify({
        'id': quotation.id,
        'quotation_number': quotation.quotation_number,
        'school_id': quotation.school_id,
        'school_name': quotation.school_name,
        'repair_person': quotation.repair_person,
        'repair_location': quotation.repair_location,
        'repair_time': quotation.repair_time,
        'items': [
            {
                'item_id': item.item_id,
                'name': item.name,
                'price': item.price,
                'unit': item.unit,
                'quantity': item.quantity,
                'subtotal': item.subtotal
            } for item in quotation.items
        ],
        'total_price': quotation.total_price,
        'created_at': quotation.created_at
    }), 201

@app.route('/api/quotations', methods=['GET'])
def get_quotations():
    quotations = Quotation.query.order_by(Quotation.id.desc()).all()
    result = []
    for q in quotations:
        result.append({
            'id': q.id,
            'quotation_number': q.quotation_number,
            'school_id': q.school_id,
            'school_name': q.school_name,
            'repair_person': q.repair_person,
            'repair_location': q.repair_location,
            'repair_time': q.repair_time,
            'items': [
                {
                    'item_id': item.item_id,
                    'name': item.name,
                    'price': item.price,
                    'unit': item.unit,
                    'quantity': item.quantity,
                    'subtotal': item.subtotal
                } for item in q.items
            ],
            'total_price': q.total_price,
            'created_at': q.created_at
        })
    return jsonify(result)

@app.route('/api/quotations/<int:quotation_id>/image', methods=['GET'])
def generate_quotation_image(quotation_id):
    """生成计价单图片"""
    quotation = Quotation.query.get(quotation_id)
    if not quotation:
        return jsonify({"error": "未找到计价单"}), 404

    try:
        img_width = 800
        img_height = 600 + len(quotation.items) * 30
        img = Image.new('RGB', (img_width, img_height), color = 'white')
        d = ImageDraw.Draw(img)
        try:
            font_path = "C:/Windows/Fonts/simsun.ttc"
            if not os.path.exists(font_path):
                 font_path = "arial.ttf"
            title_font = ImageFont.truetype(font_path, 30)
            text_font = ImageFont.truetype(font_path, 18)
            small_font = ImageFont.truetype(font_path, 14)
        except IOError:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        y_offset = 20
        d.text((img_width/2, y_offset), "维修计价单", font=title_font, fill=(0,0,0), anchor="mt")
        y_offset += 50
        d.text((30, y_offset), f"单号: {quotation.quotation_number}", font=text_font, fill=(0,0,0))
        d.text((img_width - 250, y_offset), f"日期: {datetime.datetime.fromisoformat(quotation.created_at).strftime('%Y-%m-%d')}", font=text_font, fill=(0,0,0))
        y_offset += 30
        d.text((30, y_offset), f"学校: {quotation.school_name}", font=text_font, fill=(0,0,0))
        # 不再显示客户
        y_offset += 40
        d.line([(30, y_offset), (img_width - 30, y_offset)], fill=(0,0,0), width=1)
        y_offset += 10
        d.text((40, y_offset), "维修项目", font=text_font, fill=(0,0,0))
        d.text((img_width/2 - 100, y_offset), "单价", font=text_font, fill=(0,0,0))
        d.text((img_width/2 + 0, y_offset), "数量", font=text_font, fill=(0,0,0))
        d.text((img_width/2 + 100, y_offset), "单位", font=text_font, fill=(0,0,0))
        d.text((img_width - 150, y_offset), "小计", font=text_font, fill=(0,0,0))
        y_offset += 20
        d.line([(30, y_offset), (img_width - 30, y_offset)], fill=(0,0,0), width=1)
        y_offset += 10
        for item in quotation.items:
            d.text((40, y_offset), str(item.name), font=text_font, fill=(0,0,0))
            d.text((img_width/2 - 100, y_offset), f"{item.price:.2f}", font=text_font, fill=(0,0,0))
            d.text((img_width/2 + 0, y_offset), str(item.quantity), font=text_font, fill=(0,0,0))
            d.text((img_width/2 + 100, y_offset), str(item.unit), font=text_font, fill=(0,0,0))
            d.text((img_width - 150, y_offset), f"{item.subtotal:.2f}", font=text_font, fill=(0,0,0))
            y_offset += 30
        d.line([(30, y_offset), (img_width - 30, y_offset)], fill=(0,0,0), width=1)
        y_offset += 20
        d.text((img_width - 250, y_offset), f"总计金额: {quotation.total_price:.2f} 元", font=title_font, fill=(0,0,0))
        y_offset += 50
        d.text((30, y_offset), "维修单位: 重庆星豫科技", font=small_font, fill=(100,100,100))
        d.text((img_width - 150, y_offset), "签字: _________", font=small_font, fill=(100,100,100))
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"{quotation.quotation_number}.png")
    except Exception as e:
        print(f"Error generating image: {e}")
        return jsonify({"error": f"生成图片失败: {str(e)}"}), 500

@app.route('/api/quotations/<int:quotation_id>/excel', methods=['GET'])
def export_quotation_excel(quotation_id):
    """导出计价单为Excel（单行模式）"""
    quotation = Quotation.query.get(quotation_id)
    if not quotation:
        return jsonify({"error": "未找到计价单"}), 404
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "维修计价单"
        # 单行表头
        headers = ["单号", "学校", "维修人员", "维修地点", "维修时间", "总金额"]
        max_items = len(quotation.items)
        for i in range(max_items):
            headers += [f"项目{i+1}名称", f"项目{i+1}单价", f"项目{i+1}数量", f"项目{i+1}单位", f"项目{i+1}小计"]
        ws.append(headers)
        # 单行数据
        row = [
            quotation.quotation_number,
            quotation.school_name,
            quotation.repair_person,
            quotation.repair_location,
            quotation.repair_time,
            quotation.total_price
        ]
        for item in quotation.items:
            row += [item.name, item.price, item.quantity, item.unit, item.subtotal]
        ws.append(row)
        excel_io = io.BytesIO()
        wb.save(excel_io)
        excel_io.seek(0)
        uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        return send_file(excel_io, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"{quotation.quotation_number}.xlsx")
    except Exception as e:
        print(f"Error exporting excel: {e}")
        return jsonify({"error": f"导出Excel失败: {str(e)}"}), 500

@app.route('/api/quotations/export_batch_excel', methods=['GET'])
def export_batch_quotations_excel():
    """批量导出所有计价单为Excel（单行模式，支持筛选）"""
    # 获取筛选参数
    school_id = request.args.get('school_id', type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    filtered = Quotation.query.all()
    if school_id:
        filtered = [q for q in filtered if q.school_id == school_id]
    if start:
        try:
            start_dt = datetime.datetime.fromisoformat(start)
            filtered = [q for q in filtered if datetime.datetime.fromisoformat(q.created_at) >= start_dt]
        except Exception:
            pass
    if end:
        try:
            end_dt = datetime.datetime.fromisoformat(end)
            filtered = [q for q in filtered if datetime.datetime.fromisoformat(q.created_at) <= end_dt]
        except Exception:
            pass
    if not filtered:
        return jsonify({"message": "没有计价单可以导出"}), 404
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "批量计价单"
        # 计算最大项目数
        max_items = max(len(q.items) for q in filtered)
        headers = ["单号", "学校", "维修人员", "维修地点", "维修时间", "总金额"]
        for i in range(max_items):
            headers += [f"项目{i+1}名称", f"项目{i+1}单价", f"项目{i+1}数量", f"项目{i+1}单位", f"项目{i+1}小计"]
        ws.append(headers)
        for quotation in filtered:
            row = [
                quotation.quotation_number,
                quotation.school_name,
                quotation.repair_person,
                quotation.repair_location,
                quotation.repair_time,
                quotation.total_price
            ]
            for item in quotation.items:
                row += [item.name, item.price, item.quantity, item.unit, item.subtotal]
            # 补齐空项目
            for _ in range(max_items - len(quotation.items)):
                row += ["", "", "", "", ""]
            ws.append(row)
        excel_io = io.BytesIO()
        wb.save(excel_io)
        excel_io.seek(0)
        uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        filename = f"批量导出计价单_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        return send_file(excel_io, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Error exporting batch excel: {e}")
        return jsonify({"error": f"批量导出Excel失败: {str(e)}"}), 500

@app.route('/api/dev/clear_schools_and_items', methods=['POST'])
def clear_schools_and_items():
    RepairItem.query.delete()
    School.query.delete()
    db.session.commit()
    return jsonify({'message': '已清空所有学校和维修项目'})

@app.route('/api/dev/import_school_repair_items', methods=['POST'])
def import_school_repair_items():
    data = request.json
    # data: {schools: [{name: '学校名', items: [{name, price}]}]}
    for school in data['schools']:
        s = School(name=school['name'])
        db.session.add(s)
        db.session.flush()  # 获取id
        for item in school['items']:
            db.session.add(RepairItem(name=item['name'], price=item['price'], unit='项', school_id=s.id))
    db.session.commit()
    return jsonify({'message': '导入完成'})

if __name__ == '__main__':
    # 确保 uploads 文件夹存在
    uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    app.run(debug=True, port=5001) # 使用与前端不同的端口，避免冲突