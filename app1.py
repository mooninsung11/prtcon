from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# DB 초기화
def init_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            product TEXT NOT NULL,
            method TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 주문 등록 API
@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.get_json()
    product = data.get('product')
    method = data.get('method')
    timestamp = data.get('timestamp') or datetime.now().isoformat()

    if not product or not method:
        return jsonify({"success": False, "message": "상품 또는 결제수단 누락"}), 400

    order_id = str(uuid.uuid4())[:8]  # 간단한 주문번호 생성
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO orders (id, product, method, timestamp) VALUES (?, ?, ?, ?)',
                       (order_id, product, method, timestamp))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "order_id": order_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 주문 목록 조회 API (선택)
@app.route('/api/orders', methods=['GET'])
def list_orders():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, product, method, timestamp FROM orders ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    result = [{"id": r[0], "product": r[1], "method": r[2], "timestamp": r[3]} for r in rows]
    return jsonify(result)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
