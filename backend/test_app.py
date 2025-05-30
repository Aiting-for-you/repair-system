import unittest
import json
from backend.app import app, db, School, RepairItem, Quotation, QuotationItem # Import necessary components from your app

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            # Check and add "其他" item for schools during initial setup, if any schools are pre-created.
            # For most tests, we'll create schools and items as needed.
            # The logic in app.py's app_context block for "其他" will run when schools are added.

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

class TestSchoolAPI(BaseTestCase):
    def test_get_schools_empty(self):
        response = self.client.get('/api/schools')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

    def test_add_and_get_school(self):
        # Add a school
        post_response = self.client.post('/api/schools', json={'name': 'Test School 1'})
        self.assertEqual(post_response.status_code, 201)
        school_data = json.loads(post_response.data)
        self.assertEqual(school_data['name'], 'Test School 1')
        school_id = school_data['id']

        # Verify "其他" item creation
        with app.app_context():
            other_item = RepairItem.query.filter_by(school_id=school_id, name='其他').first()
            self.assertIsNotNone(other_item)
            self.assertEqual(other_item.price, 0.0)

        # Get the school
        get_response = self.client.get('/api/schools')
        self.assertEqual(get_response.status_code, 200)
        schools = json.loads(get_response.data)
        self.assertEqual(len(schools), 1)
        self.assertEqual(schools[0]['name'], 'Test School 1')

    def test_add_school_missing_name(self):
        response = self.client.post('/api/schools', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.data))

    def test_update_school(self):
        # Add a school first
        post_response = self.client.post('/api/schools', json={'name': 'Original Name'})
        school_id = json.loads(post_response.data)['id']

        # Update the school
        put_response = self.client.put(f'/api/schools/{school_id}', json={'name': 'Updated Name'})
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(json.loads(put_response.data)['name'], 'Updated Name')

        # Verify update
        get_response = self.client.get(f'/api/schools')
        schools = json.loads(get_response.data)
        self.assertEqual(schools[0]['name'], 'Updated Name')


    def test_update_school_not_found(self):
        response = self.client.put('/api/schools/999', json={'name': 'Non Existent'})
        self.assertEqual(response.status_code, 404)

    def test_update_school_missing_name(self):
        post_response = self.client.post('/api/schools', json={'name': 'School To Update badly'})
        school_id = json.loads(post_response.data)['id']
        response = self.client.put(f'/api/schools/{school_id}', json={})
        self.assertEqual(response.status_code, 400)


    def test_delete_school(self):
        post_response = self.client.post('/api/schools', json={'name': 'School To Delete'})
        school_id = json.loads(post_response.data)['id']

        delete_response = self.client.delete(f'/api/schools/{school_id}')
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn('School deleted', json.loads(delete_response.data)['message'])

        # Verify deletion
        get_response = self.client.get(f'/api/schools')
        schools = json.loads(get_response.data)
        self.assertEqual(len(schools), 0)


    def test_delete_school_not_found(self):
        response = self.client.delete('/api/schools/999')
        self.assertEqual(response.status_code, 404)


class TestRepairItemAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create a school for item tests
        with app.app_context():
            school = School(name="Test School for Items")
            db.session.add(school)
            db.session.commit()
            self.school_id = school.id
            # The "其他" item is added automatically by app logic when a school is created

    def test_get_repair_items_by_school_empty(self):
        # The "其他" item is auto-added, so it won't be truly empty unless we delete it.
        # Let's test that it returns the "其他" item initially.
        response = self.client.get(f'/api/schools/{self.school_id}/items')
        self.assertEqual(response.status_code, 200)
        items = json.loads(response.data)
        self.assertEqual(len(items), 1) # Should have the "其他" item
        self.assertEqual(items[0]['name'], '其他')

    def test_add_and_get_repair_items_by_school(self):
        # Add an item to the school
        item_data = {'name': 'New Light Bulb', 'price': 15.0, 'unit': 'pcs', 'school_id': self.school_id}
        post_response = self.client.post('/api/items', json=item_data)
        self.assertEqual(post_response.status_code, 201)
        
        response = self.client.get(f'/api/schools/{self.school_id}/items')
        self.assertEqual(response.status_code, 200)
        items = json.loads(response.data)
        self.assertEqual(len(items), 2) # "其他" + new item
        # Check for the newly added item (order might vary)
        added_item_in_response = next((item for item in items if item['name'] == 'New Light Bulb'), None)
        self.assertIsNotNone(added_item_in_response)
        self.assertEqual(added_item_in_response['price'], 15.0)

    def test_get_repair_items_school_not_found(self):
        response = self.client.get('/api/schools/999/items')
        self.assertEqual(response.status_code, 404) # School not found

    def test_get_all_repair_items(self):
        # Add an item
        item_data = {'name': 'Projector Lamp', 'price': 150.0, 'unit': 'pcs', 'school_id': self.school_id}
        self.client.post('/api/items', json=item_data)

        response = self.client.get('/api/items')
        self.assertEqual(response.status_code, 200)
        items = json.loads(response.data)
        self.assertTrue(len(items) >= 1) # At least one "其他" and our new item
        found_item = any(item['name'] == 'Projector Lamp' for item in items)
        self.assertTrue(found_item)

    def test_add_item_missing_params(self):
        response = self.client.post('/api/items', json={'name': 'Incomplete Item'})
        self.assertEqual(response.status_code, 400)

    def test_add_item_invalid_school_id(self):
        item_data = {'name': 'Item for NonExistent School', 'price': 10.0, 'unit': 'pcs', 'school_id': 999}
        response = self.client.post('/api/items', json=item_data)
        self.assertEqual(response.status_code, 404) # School ID not found

    def test_update_repair_item(self):
        # Add an item first
        item_data = {'name': 'Old Item Name', 'price': 25.0, 'unit': 'pcs', 'school_id': self.school_id}
        post_response = self.client.post('/api/items', json=item_data)
        item_id = json.loads(post_response.data)['id']

        # Update the item
        update_data = {'name': 'Updated Item Name', 'price': 30.0, 'unit': 'set'}
        put_response = self.client.put(f'/api/items/{item_id}', json=update_data)
        self.assertEqual(put_response.status_code, 200)
        updated_item = json.loads(put_response.data)
        self.assertEqual(updated_item['name'], 'Updated Item Name')
        self.assertEqual(updated_item['price'], 30.0)

    def test_update_repair_item_not_found(self):
        response = self.client.put('/api/items/999', json={'name': 'Non Existent Item'})
        self.assertEqual(response.status_code, 404)
    
    def test_update_repair_item_invalid_data(self):
        item_data = {'name': 'Item to update badly', 'price': 25.0, 'unit': 'pcs', 'school_id': self.school_id}
        post_response = self.client.post('/api/items', json=item_data)
        item_id = json.loads(post_response.data)['id']

        update_data = {'price': 'not-a-number'}
        put_response = self.client.put(f'/api/items/{item_id}', json=update_data)
        self.assertEqual(put_response.status_code, 400)


    def test_delete_repair_item(self):
        item_data = {'name': 'Item To Delete', 'price': 5.0, 'unit': 'pcs', 'school_id': self.school_id}
        post_response = self.client.post('/api/items', json=item_data)
        item_id = json.loads(post_response.data)['id']

        delete_response = self.client.delete(f'/api/items/{item_id}')
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn('Repair item deleted', json.loads(delete_response.data)['message'])

    def test_delete_repair_item_not_found(self):
        response = self.client.delete('/api/items/999')
        self.assertEqual(response.status_code, 404)


class TestCalculatePriceAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        with app.app_context():
            school1 = School(name="School A")
            db.session.add(school1)
            db.session.commit()
            self.school1_id = school1.id

            item1_s1 = RepairItem(name="Lightbulb", price=10.0, unit="pc", school_id=self.school1_id)
            item2_s1 = RepairItem(name="Faucet", price=50.0, unit="pc", school_id=self.school1_id)
            db.session.add_all([item1_s1, item2_s1])
            db.session.commit()
            self.item1_s1_id = item1_s1.id
            self.item2_s1_id = item2_s1.id
    
    def test_calculate_price_valid(self):
        payload = {
            "items": [
                {"school_id": self.school1_id, "item_id": self.item1_s1_id, "quantity": 2}, # 2 * 10 = 20
                {"school_id": self.school1_id, "item_id": self.item2_s1_id, "quantity": 1}  # 1 * 50 = 50
            ]
        }
        response = self.client.post('/api/calculate_price', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_price'], 70.0)

    def test_calculate_price_non_existent_item(self):
        payload = {
            "items": [
                {"school_id": self.school1_id, "item_id": 999, "quantity": 1} # Non-existent
            ]
        }
        response = self.client.post('/api/calculate_price', json=payload)
        self.assertEqual(response.status_code, 200) # Endpoint should still succeed
        data = json.loads(response.data)
        self.assertEqual(data['total_price'], 0.0) # Non-existent item contributes 0

    def test_calculate_price_mix_valid_invalid(self):
        payload = {
            "items": [
                {"school_id": self.school1_id, "item_id": self.item1_s1_id, "quantity": 3}, # 3 * 10 = 30
                {"school_id": self.school1_id, "item_id": 998, "quantity": 1},          # Invalid
                {"school_id": 999, "item_id": self.item2_s1_id, "quantity": 1}           # Invalid school
            ]
        }
        response = self.client.post('/api/calculate_price', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_price'], 30.0)

    def test_calculate_price_zero_quantity(self):
        payload = {
            "items": [
                {"school_id": self.school1_id, "item_id": self.item1_s1_id, "quantity": 0}
            ]
        }
        response = self.client.post('/api/calculate_price', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_price'], 0.0)

    def test_calculate_price_empty_items_list(self):
        payload = {"items": []}
        response = self.client.post('/api/calculate_price', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_price'], 0.0)

    def test_calculate_price_missing_items_key(self):
        payload = {} # Missing 'items' key
        response = self.client.post('/api/calculate_price', json=payload)
        self.assertEqual(response.status_code, 400) # Assuming strict validation


class TestQuotationAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        with app.app_context():
            school = School(name="Test School for Quotes")
            db.session.add(school)
            db.session.commit()
            self.school_id = school.id
            self.school_name = school.name

            item1 = RepairItem(name="Q-Item 1", price=10.0, unit="pc", school_id=self.school_id)
            item2 = RepairItem(name="Q-Item 2", price=20.0, unit="set", school_id=self.school_id)
            db.session.add_all([item1, item2])
            db.session.commit()
            self.item1_id = item1.id
            self.item2_id = item2.id
            self.item1_price = item1.price
            self.item2_price = item2.price
            self.item1_unit = item1.unit
            self.item2_unit = item2.unit


    def test_submit_and_get_quotation(self):
        quotation_payload = {
            "school_id": self.school_id,
            "repair_person": "Test User",
            "repair_location": "Room 101",
            "repair_time": "2024-01-01T10:00:00",
            "items": [
                {"item_id": self.item1_id, "name": "Q-Item 1", "price": self.item1_price, "unit": self.item1_unit, "quantity": 2, "subtotal": self.item1_price * 2},
                {"item_id": self.item2_id, "name": "Q-Item 2", "price": self.item2_price, "unit": self.item2_unit, "quantity": 1, "subtotal": self.item2_price * 1}
            ],
            "total_price": (self.item1_price * 2) + (self.item2_price * 1)
        }
        post_response = self.client.post('/api/quotations', json=quotation_payload)
        self.assertEqual(post_response.status_code, 201, msg=post_response.data)
        posted_quotation = json.loads(post_response.data)
        self.assertEqual(posted_quotation['school_id'], self.school_id)
        self.assertEqual(len(posted_quotation['items']), 2)
        quotation_id = posted_quotation['id']

        # Test GET /api/quotations
        get_response = self.client.get('/api/quotations')
        self.assertEqual(get_response.status_code, 200)
        quotations = json.loads(get_response.data)
        self.assertEqual(len(quotations), 1)
        self.assertEqual(quotations[0]['id'], quotation_id)
        self.assertEqual(quotations[0]['total_price'], quotation_payload['total_price'])

    def test_submit_quotation_missing_params(self):
        response = self.client.post('/api/quotations', json={"school_id": self.school_id})
        self.assertEqual(response.status_code, 400)

    def test_submit_quotation_invalid_school_id(self):
        quotation_payload = {
            "school_id": 999, # Non-existent
            "repair_person": "Test User", "repair_location": "Room 101", "repair_time": "2024-01-01T10:00:00",
            "items": [{"item_id": self.item1_id, "name": "Q-Item 1", "price": 10, "unit": "pc", "quantity": 1, "subtotal": 10}],
            "total_price": 10
        }
        response = self.client.post('/api/quotations', json=quotation_payload)
        self.assertEqual(response.status_code, 404) # School not found

    def test_submit_quotation_item_detail_validation(self):
        # Test missing item details
        quotation_payload_bad_item = {
            "school_id": self.school_id, "repair_person": "Test User", "repair_location": "Room 101", 
            "repair_time": "2024-01-01T10:00:00",
            "items": [{"item_id": self.item1_id, "name": "Q-Item 1"}], # Missing price, quantity etc.
            "total_price": 10
        }
        response = self.client.post('/api/quotations', json=quotation_payload_bad_item)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Incomplete repair item detail", json.loads(response.data)['error'])

    def test_get_quotations_filtered_by_school(self):
        # Add a quotation for self.school_id
        self.client.post('/api/quotations', json={
            "school_id": self.school_id, "repair_person": "TU1", "repair_location": "L1", 
            "repair_time": "2024-01-01T10:00:00",
            "items": [{"item_id": self.item1_id, "name": "Q-Item 1", "price": 10, "unit": "pc", "quantity": 1, "subtotal": 10}],
            "total_price": 10
        })
        # Add another school and a quotation for it
        with app.app_context():
            other_school = School(name="Other School")
            db.session.add(other_school)
            db.session.commit()
            other_school_id = other_school.id
        self.client.post('/api/quotations', json={
            "school_id": other_school_id, "repair_person": "TU2", "repair_location": "L2", 
            "repair_time": "2024-01-02T10:00:00",
            "items": [{"item_id": 1, "name": "Q-Item X", "price": 5, "unit": "pc", "quantity": 1, "subtotal": 5}], # Assume item 1 exists or use a real one
            "total_price": 5
        })
        
        response = self.client.get(f'/api/quotations?school_id={self.school_id}')
        self.assertEqual(response.status_code, 200)
        quotations = json.loads(response.data)
        self.assertEqual(len(quotations), 1)
        self.assertEqual(quotations[0]['school_id'], self.school_id)

    # Date filtering tests would require more complex setup or mocking datetime.now()
    # For now, we'll assume basic date string comparison works if format is consistent.

    def test_delete_quotation(self):
        # Add a quotation
        post_response = self.client.post('/api/quotations', json={
            "school_id": self.school_id, "repair_person": "TU", "repair_location": "L", 
            "repair_time": "2024-01-03T10:00:00",
            "items": [{"item_id": self.item1_id, "name": "Q-Item 1", "price": 10, "unit": "pc", "quantity": 1, "subtotal": 10}],
            "total_price": 10
        })
        quotation_id = json.loads(post_response.data)['id']

        # Ensure quotation items are created
        with app.app_context():
            items = QuotationItem.query.filter_by(quotation_id=quotation_id).all()
            self.assertTrue(len(items) > 0)

        delete_response = self.client.delete(f'/api/quotations/{quotation_id}')
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn('Quotation deleted successfully', json.loads(delete_response.data)['message'])

        # Verify quotation items are also deleted
        with app.app_context():
            items_after_delete = QuotationItem.query.filter_by(quotation_id=quotation_id).all()
            self.assertEqual(len(items_after_delete), 0)


    def test_delete_quotation_not_found(self):
        response = self.client.delete('/api/quotations/999')
        self.assertEqual(response.status_code, 404)


class TestFileGenerationAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        with app.app_context():
            school = School(name="School for Files")
            db.session.add(school)
            db.session.commit()
            self.school_id = school.id

            item = RepairItem(name="FileGen Item", price=100.0, unit="svc", school_id=self.school_id)
            db.session.add(item)
            db.session.commit()
            self.item_id = item.id
            
            quotation_payload = {
                "school_id": self.school_id, "repair_person": "File User", "repair_location": "Server Room",
                "repair_time": "2024-01-04T10:00:00",
                "items": [{"item_id": self.item_id, "name": "FileGen Item", "price": 100.0, "unit": "svc", "quantity": 1, "subtotal": 100.0}],
                "total_price": 100.0
            }
            response = self.client.post('/api/quotations', json=quotation_payload)
            self.quotation_id = json.loads(response.data)['id']

    def test_get_quotation_image(self):
        response = self.client.get(f'/api/quotations/{self.quotation_id}/image')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')

    def test_get_quotation_image_not_found(self):
        response = self.client.get('/api/quotations/999/image')
        self.assertEqual(response.status_code, 404)

    def test_get_quotation_excel(self):
        response = self.client.get(f'/api/quotations/{self.quotation_id}/excel')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_get_quotation_excel_not_found(self):
        response = self.client.get('/api/quotations/999/excel')
        self.assertEqual(response.status_code, 404)
        

if __name__ == '__main__':
    unittest.main()
