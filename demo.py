from flask import Flask, render_template, redirect, url_for, flash, session
import mysql.connector
import os

app = Flask(__name__)
# Cần có secret_key để dùng session
app.secret_key = os.urandom(24) 

# --- CẤU HÌNH KẾT NỐI MYSQL ---
# !!! THAY THẾ PASSWORD BẰNG MẬT KHẨU CỦA BẠN !!!
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Giathoai2610',         # <-- THAY MẬT KHẨU CỦA BẠN VÀO ĐÂY
    'database': 'history_demo_db' # Tên CSDL chúng ta vừa tạo
}

# --- HÀM TRỢ GIÚP ---
def get_db_connection():
    """Hàm tiện ích để kết nối đến MySQL"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối CSDL: {err}")
        return None

# --- ROUTE TRANG CHỦ (ĐỂ GIẢ LẬP ĐĂNG NHẬP) ---
@app.route('/')
def home():
    """
    Trang này giả lập rằng User 1 (student_A) đã đăng nhập.
    Nó tự động tạo session cho bạn.
    """
    session['loggedin'] = True
    session['id'] = 1 # <-- GIẢ LẬP LÀ USER ID 1
    session['email'] = 'student_A@test.com'
    
    return """
        <h1>Chào, student_A@test.com!</h1>
        <p>Bạn đã được tự động đăng nhập (Session đã được tạo).</p>
        <a href="/lich_su_dang_ky">
            >> Nhấn vào đây để xem Lịch sử đăng ký của tôi
        </a>
        <p>(API sẽ tìm các sự kiện mà User ID 1 đã đăng ký)</p>
    """

# --- API LỊCH SỬ ĐĂNG KÝ (Code của bạn) ---
@app.route('/lich_su_dang_ky')
def lich_su_dang_ky():
    """
    API cho trang Lịch sử đăng ký.
    Lấy tất cả sự kiện mà user hiện tại đã đăng ký.
    """
    
    # 1. Bảo vệ route: Bắt buộc đăng nhập
    if 'loggedin' not in session:
        flash('Vui lòng đăng nhập để xem trang này.', 'warning')
        # (Trong demo này, chúng ta giả lập login ở trang chủ)
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    if not conn:
        flash('Lỗi kết nối CSDL.', 'danger')
        return redirect(url_for('home'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 2. Lấy user_id của người đang đăng nhập từ session
        #    (Trong demo này, session['id'] sẽ là 1)
        user_id = session['id']
        
        # 3. Xây dựng câu lệnh SQL
        sql_query = """
            SELECT e.* FROM events e
            JOIN event_registrations r ON e.id = r.event_id
            WHERE r.user_id = %s
            ORDER BY e.ngay_dien_ra DESC
        """
        
        # 4. Thực thi câu lệnh
        cursor.execute(sql_query, (user_id,))
        registered_events = cursor.fetchall() # Sẽ tìm thấy 2 sự kiện (101, 102)
        
        # 5. Gửi dữ liệu (danh sách sự kiện) sang file HTML
        return render_template(
            'lich_su.html', 
            registered_events=registered_events
        )

    except mysql.connector.Error as err:
        flash(f'Lỗi máy chủ: {err}', 'danger')
        return redirect(url_for('home'))
    finally:
        cursor.close()
        conn.close()

# --- KHỞI CHẠY APP ---
if __name__ == '__main__':
    app.run(debug=True)
