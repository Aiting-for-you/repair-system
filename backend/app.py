# backend/app.py
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import datetime
import openpyxl
from PIL import Image, ImageDraw, ImageFont
import io
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
# import json # Removed as it's not directly used; jsonify and request.json handle JSON operations

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
    try:
        db.create_all()
        # 检查每个学校是否有"其他"项目，没有则添加
        schools_db = School.query.all() # Renamed to avoid conflict with global
        for school_item in schools_db: # Renamed to avoid conflict with global
            exists = RepairItem.query.filter_by(school_id=school_item.id, name='其他').first()
            if not exists:
                db.session.add(RepairItem(name='其他', price=0.0, unit='项', school_id=school_item.id))
        db.session.commit()
    except SQLAlchemyError as e:
        app.logger.error(f"Database error during initial setup: {e}")
        # No session rollback needed here as it's initial setup or queries
        # Potentially raise the exception if the app cannot start without this
    except Exception as e:
        app.logger.error(f"General error during initial setup: {e}")
        # Potentially raise the exception

# quotations = [] # 存储计价单 # This seems to be unused as Quotation model is used.
# next_quotation_id = 1 # This also seems to be unused.

# --- API 路由 ---

@app.route('/')
def home():
    """首页，返回欢迎信息"""
    return jsonify({"message": "欢迎使用维修计价系统 API"})

# --- 学校管理 ---
@app.route('/api/schools', methods=['GET'])
def get_schools():
    try:
        schools = School.query.all()
        return jsonify([{'id': s.id, 'name': s.name} for s in schools])
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_schools: {e}")
        return jsonify({'error': 'A database error occurred', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"General error in get_schools: {e}")
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/api/schools', methods=['POST'])
def add_school():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': '缺少学校名称 (Missing school name)'}), 400 # More descriptive
    name = data.get('name')
    
    try:
        school = School(name=name)
        db.session.add(school)
        db.session.commit()
        return jsonify({'id': school.id, 'name': school.name}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in add_school: {e}")
        return jsonify({'error': 'A database error occurred while adding school', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback() # Rollback on general errors too, if session was touched
        app.logger.error(f"General error in add_school: {e}")
        return jsonify({'error': 'An unexpected error occurred while adding school', 'details': str(e)}), 500

@app.route('/api/schools/<int:school_id>', methods=['PUT'])
def update_school(school_id):
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': '缺少学校新名称 (Missing new school name)'}), 400

    name = data.get('name')
    
    try:
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': '未找到学校 (School not found)'}), 404
        school.name = name
        db.session.commit()
        return jsonify({'id': school.id, 'name': school.name})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in update_school: {e}")
        return jsonify({'error': 'A database error occurred while updating school', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in update_school: {e}")
        return jsonify({'error': 'An unexpected error occurred while updating school', 'details': str(e)}), 500

@app.route('/api/schools/<int:school_id>', methods=['DELETE'])
def delete_school(school_id):
    try:
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': '未找到学校 (School not found)'}), 404
        db.session.delete(school)
        db.session.commit()
        return jsonify({'message': '已删除 (School deleted)'})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in delete_school: {e}")
        return jsonify({'error': 'A database error occurred while deleting school', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in delete_school: {e}")
        return jsonify({'error': 'An unexpected error occurred while deleting school', 'details': str(e)}), 500

# --- 维修项目管理 ---
@app.route('/api/schools/<int:school_id>/items', methods=['GET'])
def get_repair_items_by_school(school_id):
    try:
        # Check if school exists first (optional, but good practice)
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': '未找到学校 (School not found)'}), 404
        
        items = RepairItem.query.filter_by(school_id=school_id).all()
        return jsonify([{'id': i.id, 'name': i.name, 'price': i.price, 'unit': i.unit} for i in items])
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_repair_items_by_school: {e}")
        return jsonify({'error': 'A database error occurred', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"General error in get_repair_items_by_school: {e}")
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/api/items', methods=['GET'])
def get_all_repair_items():
    try:
        items = RepairItem.query.all()
        result = []
        for item in items:
            school = School.query.get(item.school_id) # This could be N+1, but let's keep for now
            result.append({
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'unit': item.unit,
                'school_id': item.school_id,
                'school_name': school.name if school else '未知学校 (Unknown School)'
            })
        return jsonify(result)
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_all_repair_items: {e}")
        return jsonify({'error': 'A database error occurred', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"General error in get_all_repair_items: {e}")
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/api/items', methods=['POST'])
def add_repair_item():
    data = request.json
    if not data:
        return jsonify({'error': 'Request data missing'}), 400
        
    school_id = data.get('school_id')
    name = data.get('name')
    price_str = data.get('price') # Get as string first for validation
    unit = data.get('unit')

    if not all([school_id, name, price_str, unit]):
        return jsonify({'error': '缺少必要参数 (Missing required parameters: school_id, name, price, unit)'}), 400
    
    try:
        price = float(price_str)
        if price < 0:
            return jsonify({'error': '价格不能为负数 (Price cannot be negative)'}), 400
    except ValueError:
        return jsonify({'error': '价格格式无效 (Invalid price format)'}), 400

    try:
        # Check if school exists
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': f'学校ID {school_id} 未找到 (School ID {school_id} not found)'}), 404 # More specific 404

        item = RepairItem(name=name, price=price, unit=unit, school_id=school_id)
        db.session.add(item)
        db.session.commit()
        return jsonify({'id': item.id, 'name': item.name, 'price': item.price, 'unit': item.unit, 'school_id': item.school_id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in add_repair_item: {e}")
        return jsonify({'error': 'A database error occurred while adding item', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in add_repair_item: {e}")
        return jsonify({'error': 'An unexpected error occurred while adding item', 'details': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_repair_item(item_id):
    data = request.json
    if not data:
        return jsonify({'error': 'Request data missing'}), 400

    try:
        item = RepairItem.query.get(item_id)
        if not item:
            return jsonify({'error': '未找到项目 (Repair item not found)'}), 404

        item.name = data.get('name', item.name)
        
        price_str = data.get('price')
        if price_str is not None:
            try:
                price = float(price_str)
                if price < 0:
                    return jsonify({'error': '价格不能为负数 (Price cannot be negative)'}), 400
                item.price = price
            except ValueError:
                return jsonify({'error': '价格格式无效 (Invalid price format)'}), 400
        
        item.unit = data.get('unit', item.unit)
        # school_id is not typically updated here, if it is, ensure the new school_id exists.
        # new_school_id = data.get('school_id')
        # if new_school_id and new_school_id != item.school_id:
        #    school = School.query.get(new_school_id)
        #    if not school:
        #        return jsonify({'error': f'School ID {new_school_id} not found'}), 404
        #    item.school_id = new_school_id

        db.session.commit()
        return jsonify({'id': item.id, 'name': item.name, 'price': item.price, 'unit': item.unit, 'school_id': item.school_id})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in update_repair_item: {e}")
        return jsonify({'error': 'A database error occurred while updating item', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in update_repair_item: {e}")
        return jsonify({'error': 'An unexpected error occurred while updating item', 'details': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_repair_item(item_id):
    try:
        item = RepairItem.query.get(item_id)
        if not item:
            return jsonify({'error': '未找到项目 (Repair item not found)'}), 404
        
        deleted_item_info = {'id': item.id, 'name': item.name} # Store info before deleting
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': '项目已删除 (Repair item deleted)', 'item': deleted_item_info})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in delete_repair_item: {e}")
        return jsonify({'error': 'A database error occurred while deleting item', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in delete_repair_item: {e}")
        return jsonify({'error': 'An unexpected error occurred while deleting item', 'details': str(e)}), 500

# --- 价格计算 ---
@app.route('/api/calculate_price', methods=['POST'])
def calculate_price():
    """计算维修总价"""
    data = request.json
    if not data or not data.get('items'):
        return jsonify({'error': '请求数据或维修项目列表为空 (Request data or items list is empty)'}), 400

    selected_items = data.get('items', []) 
    total_price = 0
    
    try:
        for selected in selected_items:
            school_id = selected.get('school_id')
            item_id = selected.get('item_id')
            quantity_str = selected.get('quantity')

            if not school_id or not item_id or quantity_str is None:
                app.logger.warn(f"Skipping item due to missing school_id, item_id, or quantity: {selected}")
                continue
            
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    app.logger.warn(f"Skipping item due to non-positive quantity: {selected}")
                    continue
            except ValueError:
                app.logger.warn(f"Skipping item due to invalid quantity format: {selected}")
                continue

            # Query the specific item directly from the database
            # This query is inside the loop, which is fine for now given the context.
            # For very large lists of items, consider fetching all relevant items once.
            item_info = RepairItem.query.filter_by(school_id=school_id, id=item_id).first()

            if item_info:
                total_price += item_info.price * quantity
            else:
                app.logger.warn(f"Repair item not found for school_id {school_id}, item_id {item_id}. Skipping in price calculation.")
        
        return jsonify({"total_price": round(total_price, 2)})

    except SQLAlchemyError as e:
        # This will catch errors from the RepairItem.query
        app.logger.error(f"Database error in calculate_price: {e}")
        return jsonify({'error': 'A database error occurred during price calculation', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"General error in calculate_price: {e}")
        return jsonify({'error': 'An unexpected error occurred during price calculation', 'details': str(e)}), 500

# --- 计价单管理 ---
@app.route('/api/quotations', methods=['POST'])
def submit_quotation():
    data = request.json
    if not data:
        return jsonify({'error': '请求数据为空 (Request data is empty)'}), 400

    school_id = data.get('school_id')
    selected_items_details = data.get('items', [])
    total_price_str = data.get('total_price') 
    repair_person = data.get('repair_person', '未指定')
    repair_location = data.get('repair_location', '未指定')
    repair_time_str = data.get('repair_time')

    if not school_id:
        return jsonify({'error': '缺少学校ID (Missing school_id)'}), 400
    if not selected_items_details: # Check if items list is empty
        return jsonify({'error': '维修项目列表不能为空 (Items list cannot be empty)'}), 400
    if total_price_str is None: # Check for presence of total_price
        return jsonify({'error': '缺少总价 (Missing total_price)'}), 400
    if not repair_time_str:
        return jsonify({'error': '缺少维修时间 (Missing repair_time)'}), 400
    
    try:
        total_price = float(total_price_str)
    except ValueError:
        return jsonify({'error': '总价格式无效 (Invalid total_price format)'}), 400

    try:
        repair_time = datetime.datetime.fromisoformat(repair_time_str)
    except ValueError:
        return jsonify({'error': '维修时间格式不正确，请使用 ISO 格式 (YYYY-MM-DDTHH:MM) (Invalid repair_time format)'}), 400

    try:
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': f'学校ID {school_id} 未找到 (School ID {school_id} not found)'}), 404

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
        db.session.flush()  # Flush to get quotation.id for items

        for item_detail in selected_items_details:
            if not all(k in item_detail for k in ['item_id', 'name', 'price', 'unit', 'quantity', 'subtotal']):
                db.session.rollback() 
                return jsonify({'error': f'维修项目明细不完整 (Incomplete repair item detail): {item_detail}'}), 400
            
            try:
                item_price = float(item_detail['price'])
                item_quantity = int(item_detail['quantity'])
                item_subtotal = float(item_detail['subtotal'])
                # Add checks for negative values if necessary
                if item_price < 0 or item_quantity < 0 or item_subtotal < 0:
                    db.session.rollback()
                    return jsonify({'error': f'项目价格/数量/小计不能为负数: {item_detail}'}), 400

            except ValueError:
                db.session.rollback()
                return jsonify({'error': f'维修项目明细中价格/数量/小计格式无效 (Invalid format for price/quantity/subtotal in item detail): {item_detail}'}), 400

            qitem = QuotationItem(
                quotation_id=quotation.id,
                item_id=item_detail['item_id'],
                name=item_detail['name'],
                price=item_price,
                unit=item_detail['unit'],
                quantity=item_quantity,
                subtotal=item_subtotal
            )
            db.session.add(qitem)
        
        db.session.commit()
        
        # Re-fetch items for the response to ensure they are loaded
        # quotation.items will be fresh from the session after commit if relationship is configured correctly
        # but explicit query is safer if there are any doubts about session state or relationship loading.
        final_items = QuotationItem.query.filter_by(quotation_id=quotation.id).all()
        quotation_items_response = [{
            'item_id': qi.item_id, 'name': qi.name, 'price': qi.price, 
            'unit': qi.unit, 'quantity': qi.quantity, 'subtotal': qi.subtotal
        } for qi in final_items]
        
        return jsonify({
            'id': quotation.id,
            'quotation_number': quotation.quotation_number,
            'school_id': quotation.school_id,
            'school_name': quotation.school_name,
            'repair_person': quotation.repair_person,
            'repair_location': quotation.repair_location,
            'repair_time': quotation.repair_time,
            'items': quotation_items_response, # Use the re-fetched items
            'total_price': quotation.total_price,
            'created_at': quotation.created_at
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in submit_quotation: {e}")
        return jsonify({'error': '提交计价单时发生数据库错误 (A database error occurred while submitting quotation)', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback() # Rollback on general exception as well
        app.logger.error(f"General error in submit_quotation: {e}")
        return jsonify({'error': '提交计价单时发生未知错误 (An unexpected error occurred while submitting quotation)', 'details': str(e)}), 500

@app.route('/api/quotations', methods=['GET'])
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
    try:
        school_id_str = request.args.get('school_id')
        start = request.args.get('start')
        end = request.args.get('end')
        
        query = Quotation.query

        if school_id_str:
            try:
                school_id = int(school_id_str)
                query = query.filter(Quotation.school_id == school_id)
            except ValueError:
                return jsonify({'error': '学校ID格式无效 (Invalid school_id format)'}), 400
        
        if start:
            try:
                # Validate ISO format strictly for start date
                datetime.datetime.fromisoformat(start.replace('Z', '+00:00')) 
                query = query.filter(Quotation.created_at >= start)
            except ValueError:
                return jsonify({'error': '起始日期格式无效，请使用ISO格式 (Invalid start date format, use ISO format e.g., YYYY-MM-DDTHH:MM:SSZ)'}), 400
        if end:
            try:
                # Validate ISO format strictly for end date
                datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                query = query.filter(Quotation.created_at <= end)
            except ValueError:
                return jsonify({'error': '结束日期格式无效，请使用ISO格式 (Invalid end date format, use ISO format e.g., YYYY-MM-DDTHH:MM:SSZ)'}), 400

        # Consider pagination for potentially large datasets
        # For example: page = request.args.get('page', 1, type=int)
        # per_page = request.args.get('per_page', 20, type=int)
        # quotations_page = query.order_by(Quotation.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        # quotations_list = quotations_page.items
        # total_pages = quotations_page.pages
        
        quotations_list = query.order_by(Quotation.id.desc()).all() 
        
        result = []
        for q in quotations_list:
            # q.items should correctly load related QuotationItem objects
            items_data = [{
                'item_id': item.item_id, 'name': item.name, 'price': item.price,
                'unit': item.unit, 'quantity': item.quantity, 'subtotal': item.subtotal
            } for item in q.items]
            
            result.append({
                'id': q.id,
                'quotation_number': q.quotation_number,
                'school_id': q.school_id,
                'school_name': q.school_name,
                'repair_person': q.repair_person,
                'repair_location': q.repair_location,
                'repair_time': q.repair_time,
                'items': items_data,
                'total_price': q.total_price,
                'created_at': q.created_at
                # 'total_pages': total_pages # if using pagination
            })
        return jsonify(result) # Could also return {'quotations': result, 'total_pages': total_pages}

    except SQLAlchemyError as e:
        app.logger.error(f"Database error in get_quotations: {e}")
        return jsonify({'error': '获取计价单时发生数据库错误 (A database error occurred while fetching quotations)', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"General error in get_quotations: {e}")
        return jsonify({'error': '获取计价单时发生未知错误 (An unexpected error occurred while fetching quotations)', 'details': str(e)}), 500

@app.route('/api/quotations/<int:quotation_id>/image', methods=['GET'])
def generate_quotation_image(quotation_id):
    """生成计价单图片"""
    try:
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({"error": "未找到计价单 (Quotation not found)"}), 404

        # The rest of the image generation logic
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
    
    except SQLAlchemyError as e: # Catch database errors when fetching quotation
        app.logger.error(f"Database error in generate_quotation_image: {e}")
        return jsonify({'error': '生成图片时发生数据库错误 (Database error during image generation)', 'details': str(e)}), 500
    except IOError as e: # Specific to font loading or file operations
        app.logger.error(f"IOError in generate_quotation_image: {e}")
        return jsonify({'error': f"生成图片时发生IO错误 (IO error during image generation): {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Error generating image for quotation {quotation_id}: {e}")
        return jsonify({"error": f"生成图片失败 (Failed to generate image): {str(e)}"}), 500

@app.route('/api/quotations/<int:quotation_id>/excel', methods=['GET'])
def export_quotation_excel(quotation_id):
    """导出计价单为Excel（单行模式）"""
    try:
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({"error": "未找到计价单 (Quotation not found)"}), 404
        
        # The rest of the Excel generation logic
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
    
    except SQLAlchemyError as e: # Catch database errors when fetching quotation
        app.logger.error(f"Database error in export_quotation_excel: {e}")
        return jsonify({'error': '导出Excel时发生数据库错误 (Database error during Excel export)', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"Error exporting excel for quotation {quotation_id}: {e}")
        return jsonify({"error": f"导出Excel失败 (Failed to export Excel): {str(e)}"}), 500

@app.route('/api/quotations/export_batch_excel', methods=['GET'])
def export_batch_quotations_excel():
    """批量导出所有计价单为Excel（单行模式，支持筛选）"""
    try:
        school_id_str = request.args.get('school_id')
        start = request.args.get('start')
        end = request.args.get('end')

        query = Quotation.query # Start with a base query

        if school_id_str:
            try:
                school_id = int(school_id_str)
                query = query.filter(Quotation.school_id == school_id)
            except ValueError:
                return jsonify({'error': '学校ID格式无效 (Invalid school_id format)'}), 400
        
        if start:
            try:
                # Validate ISO format strictly for start date
                datetime.datetime.fromisoformat(start.replace('Z', '+00:00')) 
                query = query.filter(Quotation.created_at >= start)
            except ValueError:
                return jsonify({'error': '起始日期格式无效，请使用ISO格式 (Invalid start date format, use ISO format e.g., YYYY-MM-DDTHH:MM:SSZ)'}), 400
        
        if end:
            try:
                # Validate ISO format strictly for end date
                datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                query = query.filter(Quotation.created_at <= end)
            except ValueError:
                return jsonify({'error': '结束日期格式无效，请使用ISO格式 (Invalid end date format, use ISO format e.g., YYYY-MM-DDTHH:MM:SSZ)'}), 400
            
        quotations_to_export = query.order_by(Quotation.id.desc()).all()

        if not quotations_to_export:
            return jsonify({"message": "没有符合条件的计价单可以导出 (No quotations match criteria for export)"}), 404

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "批量计价单"
        
        # Calculate max_items safely, defaulting to 0 if quotations_to_export is empty
        max_items = 0
        if quotations_to_export:
             max_items = max((len(q.items) for q in quotations_to_export), default=0)

        headers = ["单号", "学校", "维修人员", "维修地点", "维修时间", "总金额"]
        for i in range(max_items):
            headers += [f"项目{i+1}名称", f"项目{i+1}单价", f"项目{i+1}数量", f"项目{i+1}单位", f"项目{i+1}小计"]
        ws.append(headers)

        for quotation in quotations_to_export:
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
    
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in export_batch_quotations_excel: {e}")
        return jsonify({'error': '批量导出Excel时发生数据库错误 (Database error during batch Excel export)', 'details': str(e)}), 500
    except Exception as e:
        app.logger.error(f"General error in export_batch_quotations_excel: {e}") # More specific logging
        return jsonify({"error": f"批量导出Excel时发生未知错误 (An unexpected error occurred during batch Excel export): {str(e)}"}), 500

@app.route('/api/dev/clear_schools_and_items', methods=['POST'])
def clear_schools_and_items():
    try:
        # Consider adding a confirmation step or making this route admin-only in a real app
        num_items_deleted = RepairItem.query.delete()
        num_schools_deleted = School.query.delete()
        db.session.commit()
        app.logger.info(f"Cleared {num_schools_deleted} schools and {num_items_deleted} repair items.")
        return jsonify({'message': f'已清空 {num_schools_deleted} 个学校和 {num_items_deleted} 个维修项目 (Cleared {num_schools_deleted} schools and {num_items_deleted} repair items)'})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in clear_schools_and_items: {e}")
        return jsonify({'error': '清空数据时发生数据库错误 (Database error during data clearing)', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in clear_schools_and_items: {e}")
        return jsonify({'error': '清空数据时发生未知错误 (Unexpected error during data clearing)', 'details': str(e)}), 500

@app.route('/api/dev/import_school_repair_items', methods=['POST'])
def import_school_repair_items():
    data = request.json
    if not data or 'schools' not in data or not isinstance(data['schools'], list):
        return jsonify({'error': '请求数据格式无效，需要包含学校列表 (Invalid request data format, must include a list of schools)'}), 400

    schools_data = data['schools']
    imported_schools_count = 0
    imported_items_count = 0

    try:
        for school_info in schools_data:
            if not isinstance(school_info, dict) or 'name' not in school_info:
                app.logger.warn(f"Skipping school due to missing name: {school_info}")
                continue # Or return error
            
            school_name = school_info['name']
            # Optional: Check if school already exists
            existing_school = School.query.filter_by(name=school_name).first()
            if existing_school:
                s = existing_school
                app.logger.info(f"Using existing school: {school_name}")
            else:
                s = School(name=school_name)
                db.session.add(s)
                db.session.flush()  #获取id
                imported_schools_count +=1
            
            items_data = school_info.get('items', [])
            if not isinstance(items_data, list):
                app.logger.warn(f"Skipping items for school {school_name} due to invalid format: {items_data}")
                continue # Or return error

            for item_info in items_data:
                if not isinstance(item_info, dict) or not all(k in item_info for k in ['name', 'price']):
                    app.logger.warn(f"Skipping item for school {school_name} due to missing name/price: {item_info}")
                    continue # Or return error
                try:
                    price = float(item_info['price'])
                    unit = item_info.get('unit', '项') # Default unit to '项'
                except ValueError:
                    app.logger.warn(f"Skipping item for school {school_name} due to invalid price: {item_info}")
                    continue # Or return error

                # Optional: Check if item already exists for this school
                # exists = RepairItem.query.filter_by(school_id=s.id, name=item_info['name']).first()
                # if not exists:
                db.session.add(RepairItem(name=item_info['name'], price=price, unit=unit, school_id=s.id))
                imported_items_count += 1
        
        db.session.commit()
        return jsonify({'message': f'导入完成 (Import complete). {imported_schools_count} 个新学校, {imported_items_count} 个维修项目已导入.'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in import_school_repair_items: {e}")
        return jsonify({'error': '导入数据时发生数据库错误 (Database error during data import)', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in import_school_repair_items: {e}")
        return jsonify({'error': '导入数据时发生未知错误 (Unexpected error during data import)', 'details': str(e)}), 500

@app.route('/api/quotations/<int:quotation_id>', methods=['DELETE'])
def delete_quotation(quotation_id):
    try:
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'error': '未找到计价单 (Quotation not found)'}), 404
        
        # 先删除关联的 QuotationItem 记录
        QuotationItem.query.filter_by(quotation_id=quotation_id).delete()
        # 然后删除 Quotation 记录
        db.session.delete(quotation)
        db.session.commit()
        return jsonify({'message': '计价单已成功删除 (Quotation deleted successfully)'})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error in delete_quotation for ID {quotation_id}: {e}")
        return jsonify({'error': '删除计价单时发生数据库错误 (Database error while deleting quotation)', 'details': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"General error in delete_quotation for ID {quotation_id}: {e}")
        return jsonify({'error': '删除计价单时发生未知错误 (Unexpected error while deleting quotation)', 'details': str(e)}), 500

if __name__ == '__main__':
    # 确保 uploads 文件夹存在
    uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    app.run(debug=True, port=5001) # 使用与前端不同的端口，避免冲突