from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import openai
import requests
import json
from datetime import datetime
from dateutil import parser

app = Flask(__name__)
CORS(app)

# openAI API 키 설정
openai.api_key = "sk-..."

# MySQL 설정
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'test'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# OpenAI 챗봇 (Ollama 연동)
OLLAMA_URL = "http://localhost:11434/api/chat"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    payload = {
        "model": "gemma:2b",
        "messages": [{"role": "user", "content": user_input}]
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        final_reply = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    final_reply += data.get("message", {}).get("content", "")
                except Exception as e:
                    print("[WARN] 파싱 오류:", e)
        return jsonify({"response": final_reply})
    except Exception as e:
        print("[ERROR]", e)
        return jsonify({"error": str(e)}), 500

# 상품, 간식, 사료, 용품 API
@app.route("/api/foods", methods=['GET'])
def get_foods():
    try:
        category = request.args.get("category")
        with mysql.connection.cursor() as cur:
            if category and category != "전체":
                cur.execute("SELECT id, name, price, image_url AS img, category FROM Product WHERE category = %s", (category,))
            else:
                cur.execute("SELECT id, name, price, image_url AS img, category FROM Product")
            data = cur.fetchall()
        return jsonify(data)
    except Exception as e:
        print("[ERROR Foods API]", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/feed", methods=['GET'])
def get_feed():
    try:
        category = request.args.get("category")
        feed_categories = ['건식사료', '소프트사료', '습식사료', '에어/동결사료', '화식/생식사료']
        with mysql.connection.cursor() as cur:
            if category and category in feed_categories:
                cur.execute(
                    "SELECT name, price, image_url AS img, category FROM Product1 WHERE category = %s", (category,)
                )
            else:
                format_strings = ','.join(['%s'] * len(feed_categories))
                sql = f"SELECT name, price, image_url AS img, category FROM Product1 WHERE category IN ({format_strings})"
                cur.execute(sql, tuple(feed_categories))
            data = cur.fetchall()
        return jsonify(data)
    except Exception as e:
        print("[ERROR Feed API]", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/goods", methods=['GET'])
def get_goods():
    try:
        category = request.args.get("category")
        # 실제 사용 중인 카테고리 리스트로 맞춰주세요!
        goods_categories = [
            '하우스/스텝', '의류/액세서리', '이동장/유모차',
            '목욕용품', '위생/배변', '급식기/급수기',
            '산책/훈련', '케어용품'
        ]
        with mysql.connection.cursor() as cur:
            if category and category in goods_categories:
                cur.execute(
                    "SELECT name, price, image_url, category FROM Product2 WHERE category = %s", (category,)
                )
            else:
                format_strings = ','.join(['%s'] * len(goods_categories))
                sql = f"SELECT name, price, image_url, category FROM Product2 WHERE category IN ({format_strings})"
                cur.execute(sql, tuple(goods_categories))
            goods = cur.fetchall()
        return jsonify(goods)
    except Exception as e:
        print("[ERROR Goods API]", e)
        return jsonify({"error": str(e)}), 500


# 회원가입
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    region = data.get('region', '')

    if not all([username, email, password]):
        return jsonify({'success': False, 'message': '필수값 누락'}), 400

    with mysql.connection.cursor() as cur:
        cur.execute("SELECT 1 FROM User1 WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({'success': False, 'message': '이미 가입된 이메일'}), 409

        cur.execute(
            "INSERT INTO User1 (username, email, password, region) VALUES (%s, %s, %s, %s)",
            (username, email, password, region)
        )
    mysql.connection.commit()
    return jsonify({'success': True}), 201

# 로그인
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    with mysql.connection.cursor() as cur:
        cur.execute("SELECT id, username FROM User1 WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
    if user:
        return jsonify({'success': True, 'username': user['username']})
    return jsonify({'success': False, 'message': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401

# 시설/병원 정보
@app.route('/api/facilities', methods=['GET'])
def get_facilities():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM facility")
            rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        print("[ERROR] /api/facilities:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM hospital")
            rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        print("[ERROR] /api/hospitals:", e)
        return jsonify({"error": str(e)}), 500

# 마이페이지 정보
@app.route("/api/mypage")
def mypage_info():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username, email, region, dog_type, dog_old FROM User1 WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        if user:
            return jsonify(user)
        else:
            return jsonify({"error": "회원 정보를 찾을 수 없습니다."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 회원 탈퇴
@app.route("/api/withdraw", methods=["POST"])
def withdraw():
    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"success": False, "message": "로그인 정보가 없습니다."}), 400
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM User1 WHERE username = %s", (username,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 회원 정보 수정
@app.route('/api/user/<username>', methods=['GET', 'PUT'])
def user_profile(username):
    cur = mysql.connection.cursor()
    if request.method == 'GET':
        cur.execute("SELECT username, email, region, dog_type, dog_old FROM User1 WHERE username=%s", (username,))
        user = cur.fetchone()
        return jsonify(user or {})
    elif request.method == 'PUT':
        data = request.get_json()

        # dog_old 안전하게 float 변환!
        dog_old = data.get('dog_old')
        try:
            if dog_old is None or dog_old == "" or str(dog_old).lower() == "null":
                dog_old = 0.0
            else:
                dog_old = float(dog_old)
        except (ValueError, TypeError):
            dog_old = 0.0

        cur.execute("""
            UPDATE User1
               SET email=%s, region=%s, dog_type=%s, dog_old=%s
             WHERE username=%s
        """, (
            data['email'],
            data['region'],
            data['dog_type'],
            dog_old,     # ← 변환된 값!
            username
        ))
        mysql.connection.commit()
        return jsonify({'success': True})

@app.route("/api/cart", methods=["GET"])
def get_cart_items():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "로그인이 필요합니다."}), 400

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT id FROM User1 WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify([])

        user_id = user["id"]

        cursor.execute("""
            SELECT c.product_id, c.quantity, c.added_at,
                   COALESCE(p.name, p1.name, p2.name) AS name,
                   COALESCE(p.price, p1.price, p2.price) AS price,
                   COALESCE(p.image_url, p1.image_url, p2.image_url) AS img
            FROM cartitem c
            LEFT JOIN product p ON c.product_id = p.id
            LEFT JOIN product1 p1 ON c.product_id = p1.id
            LEFT JOIN product2 p2 ON c.product_id = p2.id
            WHERE c.user_id = %s
        """, (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        return jsonify(rows)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    username = data.get("username")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    added_at_raw = data.get("added_at")

    # ✅ ISO 문자열을 datetime으로 파싱
    try:
        if added_at_raw:
            added_at_dt = parser.isoparse(added_at_raw)
            added_at = added_at_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            added_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return jsonify(success=False, message=f"날짜 파싱 오류: {str(e)}")

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM User1 WHERE username = %s", (username,))
        result = cursor.fetchone()
        if not result:
            return jsonify(success=False, message="유저를 찾을 수 없습니다.")

        user_id = result["id"]

        cursor.execute("""
            INSERT INTO cartitem (user_id, product_id, quantity, added_at)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """, (user_id, product_id, quantity, added_at))

        mysql.connection.commit()
        cursor.close()
        return jsonify(success=True)

    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route("/api/cart", methods=["PUT"])
def update_cart_quantity():
    data = request.get_json()
    username = data.get("username")
    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if not username or not product_id or quantity is None:
        return jsonify(success=False, message="필수 정보 누락")

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM User1 WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify(success=False, message="유저 없음")
        
        user_id = user["id"]
        cursor.execute("""
            UPDATE cartitem SET quantity = %s
            WHERE user_id = %s AND product_id = %s
        """, (quantity, user_id, product_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@app.route("/api/cart/delete", methods=["POST"])
def delete_cart_item():
    data = request.get_json()
    username = data.get("username")
    product_id = data.get("product_id")

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM User1 WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다."})

        user_id = user["id"]

        cursor.execute("DELETE FROM cartitem WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/product/<int:product_id>")
def get_product(product_id):
    cursor = mysql.connection.cursor()

    for table in ['product', 'product1', 'product2']:
        cursor.execute(f"""
            SELECT id, name, price, image_url AS img, category
            FROM {table}
            WHERE id = %s
        """, (product_id,))
        result = cursor.fetchone()
        if result:
            result["source_table"] = table  # 선택: 어느 테이블에서 가져왔는지
            cursor.close()
            return jsonify(result)

    cursor.close()
    return jsonify({"error": "상품을 찾을 수 없습니다."})




# 서버 실행
if __name__ == '__main__':
    app.run(debug=True)
