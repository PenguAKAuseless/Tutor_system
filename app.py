from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta # Thêm thư viện để xử lý "Ghi nhớ"

app = Flask(__name__)

# --- CẤU HÌNH ---
# 1. Secret Key (Bắt buộc để dùng session và flash)
app.secret_key = os.urandom(24) 

# 2. Đặt thời gian tồn tại cho session "Ghi nhớ" (ví dụ: 7 ngày)
app.permanent_session_lifetime = timedelta(days=7)

# 3. Cấu hình kết nối MySQL
#    !!! THAY THẾ BẰNG THÔNG TIN MYSQL CỦA BẠN !!!
db_config = {
    'host': 'localhost',
    'user': 'root',         # <-- Tên người dùng CSDL (ví dụ: root)
    'password': '',         # <-- Mật khẩu CSDL của bạn (MySQL 8.0 thường CÓ mật khẩu)
    'database': 'login_db'  # <-- Tên database
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

# --- CÁC ROUTE (ĐƯỜNG DẪN WEB) ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    """API/Trang đăng nhập (xử lý bằng Email)"""
    
    # Nếu người dùng đã đăng nhập rồi, chuyển họ đến dashboard
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Lấy dữ liệu từ form HTML
        email = request.form['email'] # <-- SỬA: Lấy 'email'
        password_candidate = request.form['password']
        
        # Lấy trạng thái "Ghi nhớ" (dùng .get() vì checkbox có thể không được gửi)
        remember = request.form.get('remember_me')

        conn = get_db_connection()
        if not conn:
            flash('Lỗi kết nối CSDL. Vui lòng thử lại sau.', 'danger')
            return render_template('login.html')
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # SỬA: Tìm người dùng bằng EMAIL
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password_candidate):
                # Mật khẩu chính xác, tạo session
                session['loggedin'] = True
                session['id'] = user['id']
                session['email'] = user['email'] # <-- SỬA: Lưu 'email' vào session
                
                # SỬA: Xử lý "Ghi nhớ"
                if remember:
                    # Nếu "Ghi nhớ" được chọn, đặt session là vĩnh viễn (theo_lifetime)
                    session.permanent = True
                else:
                    # Nếu không, session sẽ bị xóa khi đóng trình duyệt
                    session.permanent = False
                
                flash('Đăng nhập thành công!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Sai email hoặc mật khẩu.', 'danger') # <-- SỬA: Thông báo lỗi
                
        except mysql.connector.Error as err:
            flash(f'Lỗi máy chủ: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Trang đăng ký tài khoản mới (xử lý bằng Email)"""
    
    if request.method == 'POST':
        # --- THAY ĐỔI: Lấy tất cả dữ liệu từ form ---
        email = request.form['email']
        password = request.form['password']
        ho_va_ten = request.form.get('ho_va_ten')
        ma_so_sinh_vien = request.form.get('ma_so_sinh_vien')
        ngay_sinh = request.form.get('ngay_sinh') # Sẽ ở dạng 'YYYY-MM-DD'
        gioi_tinh = request.form.get('gioi_tinh')
        khoa = request.form.get('khoa')
        nhu_cau_ho_tro = request.form.get('nhu_cau_ho_tro', '') # Mặc định là rỗng
        
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        if not conn:
            flash('Lỗi kết nối CSDL. Vui lòng thử lại sau.', 'danger')
            return render_template('register.html')

        cursor = conn.cursor(dictionary=True)
        
        try:
            # SỬA: Kiểm tra xem EMAIL đã tồn tại chưa
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            account = cursor.fetchone()
            
            if account:
                flash('Email này đã được đăng ký!', 'warning') # <-- SỬA: Thông báo
            elif not email or not password or not ho_va_ten or not ma_so_sinh_vien:
                flash('Vui lòng điền đầy đủ các trường bắt buộc!', 'danger')
            else:
                # --- THAY ĐỔI: INSERT tất cả dữ liệu mới ---
                sql = """INSERT INTO users (email, password_hash, ho_va_ten, ma_so_sinh_vien, ngay_sinh, gioi_tinh, khoa, nhu_cau_ho_tro) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                val = (email, hashed_password, ho_va_ten, ma_so_sinh_vien, ngay_sinh, gioi_tinh, khoa, nhu_cau_ho_tro)
                
                cursor.execute(sql, val)
                conn.commit()
                flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
                return redirect(url_for('login'))
                
        except mysql.connector.Error as err:
            flash(f'Lỗi khi đăng ký: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    """Trang thông tin cá nhân (Dashboard)"""
    
    if 'loggedin' in session:
        # --- THAY ĐỔI: Lấy tất cả thông tin user ---
        conn = get_db_connection()
        if not conn:
            flash('Lỗi kết nối CSDL.', 'danger')
            return redirect(url_for('login'))
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Lấy ID của user đang đăng nhập từ session
            user_id = session['id']
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_profile = cursor.fetchone()
            
            if user_profile:
                # Gửi toàn bộ đối tượng user cho template
                return render_template('dashboard.html', user=user_profile)
            else:
                flash('Không tìm thấy thông tin người dùng.', 'danger')
                return redirect(url_for('logout'))
                
        except mysql.connector.Error as err:
            flash(f'Lỗi máy chủ: {err}', 'danger')
            return redirect(url_for('login'))
        finally:
            cursor.close()
            conn.close()
    
    # Nếu chưa đăng nhập, chuyển về trang login
    flash('Vui lòng đăng nhập để xem trang này.', 'warning')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Xóa session để đăng xuất"""
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None) # <-- SỬA: Xóa 'email' khỏi session
    flash('Bạn đã đăng xuất.', 'success')
    return redirect(url_for('login'))
@app.route('/su_kien')
def su_kien():
    """API cho trang Tìm kiếm sự kiện (filter)"""
    
    # 1. Bảo vệ route: Bắt buộc đăng nhập
    if 'loggedin' not in session:
        flash('Vui lòng đăng nhập để xem trang này.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash('Lỗi kết nối CSDL.', 'danger')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 2. Lấy dữ liệu cho các bộ lọc (dropdowns)
        cursor.execute("SELECT DISTINCT chu_de FROM events ORDER BY chu_de")
        all_chu_de = [row['chu_de'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT co_so FROM events ORDER BY co_so")
        all_co_so = [row['co_so'] for row in cursor.fetchall()]

        # 3. Lấy các tham số filter từ URL (request.args vì form dùng GET)
        search_chu_de = request.args.get('chu_de')
        search_co_so = request.args.get('co_so')
        search_trang_thai = request.args.get('trang_thai')
        search_ngay = request.args.get('ngay')
        search_gio_bd = request.args.get('gio_bd')
        search_gio_kt = request.args.get('gio_kt')

        # 4. Xây dựng câu lệnh SQL động
        sql_query = "SELECT * FROM events WHERE 1=1"
        params = []

        if search_chu_de:
            sql_query += " AND chu_de = %s"
            params.append(search_chu_de)
        if search_co_so:
            sql_query += " AND co_so = %s"
            params.append(search_co_so)
        if search_ngay:
            sql_query += " AND ngay_dien_ra = %s"
            params.append(search_ngay)
        if search_gio_bd:
            sql_query += " AND thoi_gian_bat_dau >= %s"
            params.append(search_gio_bd)
        if search_gio_kt:
            sql_query += " AND thoi_gian_ket_thuc <= %s"
            params.append(search_gio_kt)
        
        # Xử lý logic 'Trạng thái'
        if search_trang_thai == 'con_trong':
            sql_query += " AND (so_cho_da_dang_ky < tong_so_cho)"
        elif search_trang_thai == 'da_day':
            sql_query += " AND (so_cho_da_dang_ky >= tong_so_cho)"

        sql_query += " ORDER BY ngay_dien_ra, thoi_gian_bat_dau"

        # 5. Thực thi query
        cursor.execute(sql_query, tuple(params))
        events = cursor.fetchall()
        
        # 6. Render template, gửi data ra ngoài
        return render_template(
            'su_kien.html', 
            events=events,
            all_chu_de=all_chu_de,
            all_co_so=all_co_so,
            search_values=request.args # Gửi lại giá trị tìm kiếm để giữ state của form
        )

    except mysql.connector.Error as err:
        flash(f'Lỗi máy chủ: {err}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()
@app.route('/su_kien_goi_y')
def su_kien_goi_y():
    """API cho trang Sự kiện gợi ý"""
    
    # 1. Bảo vệ route: Bắt buộc đăng nhập
    if 'loggedin' not in session:
        flash('Vui lòng đăng nhập để xem trang này.', 'warning')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if not conn:
        flash('Lỗi kết nối CSDL.', 'danger')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 2. Lấy thông tin (Khoa) của user đang đăng nhập
        user_id = session['id']
        cursor.execute("SELECT khoa FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        user_khoa = user['khoa'] if user else None

        if not user_khoa:
            flash('Không tìm thấy thông tin khoa của bạn để gợi ý.', 'warning')
            return render_template('su_kien_goi_y.html', suggested_events=[])

        # 3. Lấy các sự kiện:
        #    - Thuộc khoa của user HOẶC là sự kiện "Chung"
        #    - User CHƯA đăng ký
        #    - Sự kiện CÒN TRỐNG
        sql_query = """
            SELECT e.* FROM events e
            WHERE 
                (e.khoa_lien_quan = %s OR e.khoa_lien_quan = 'Tư vấn chung')
            AND 
                (e.so_cho_da_dang_ky < e.tong_so_cho)
            AND 
                e.id NOT IN (
                    SELECT r.event_id FROM event_registrations r WHERE r.user_id = %s
                )
            ORDER BY e.ngay_dien_ra
        """
        params = (user_khoa, user_id)
        
        cursor.execute(sql_query, params)
        suggested_events = cursor.fetchall()
        
        # 4. Render template mới
        return render_template(
            'su_kien_goi_y.html', 
            suggested_events=suggested_events
        )

    except mysql.connector.Error as err:
        flash(f'Lỗi máy chủ: {err}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()
@app.route('/lich_su_dang_ky')
def lich_su_dang_ky():
    """
    API cho trang Lịch sử đăng ký.
    Lấy tất cả sự kiện mà user hiện tại đã đăng ký.
    """
    
    # 1. Bảo vệ route: Bắt buộc đăng nhập
    if 'loggedin' not in session:
        flash('Vui lòng đăng nhập để xem trang này.', 'warning')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if not conn:
        flash('Lỗi kết nối CSDL.', 'danger')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 2. Lấy user_id của người đang đăng nhập từ session
        user_id = session['id']
        
        # 3. Xây dựng câu lệnh SQL
        #    Chúng ta dùng JOIN để kết nối 2 bảng:
        #    - Lấy thông tin sự kiện (events)
        #    - Dựa trên các lượt đăng ký (event_registrations)
        #    - Của user_id hiện tại
        sql_query = """
            SELECT e.* FROM events e
            JOIN event_registrations r ON e.id = r.event_id
            WHERE r.user_id = %s
            ORDER BY e.ngay_dien_ra DESC
        """
        
        # 4. Thực thi câu lệnh
        cursor.execute(sql_query, (user_id,))
        registered_events = cursor.fetchall()
        
        # 5. Gửi dữ liệu (danh sách sự kiện) sang file HTML
        return render_template(
            'lich_su.html', 
            registered_events=registered_events
        )

    except mysql.connector.Error as err:
        flash(f'Lỗi máy chủ: {err}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

# --- KHỞI CHẠY APP ---
if __name__ == '__main__':
    app.run(debug=True)


