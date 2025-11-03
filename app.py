from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os 

app = Flask(__name__)

# --- CẤU HÌNH ---
# 1. Secret Key (Bắt buộc để dùng session và flash)
app.secret_key = os.urandom(24) 

# 2. Cấu hình kết nối MySQL
#    !!! THAY THẾ BẰNG THÔNG TIN MYSQL CỦA BẠN TẠI ĐÂY !!!
db_config = {
    'host': 'localhost',
    'user': 'root',         # <-- Tên người dùng CSDL (mặc định của XAMPP là root)
    'password': 'Giathoai2610',         # <-- Mật khẩu CSDL (mặc định của XAMPP là rỗng)
    'database': 'login_db'  # <-- Tên database đã tạo ở Bước 2
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
    """Trang đăng nhập (cũng là trang chủ)"""
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        conn = get_db_connection()
        if not conn:
            flash('Lỗi kết nối CSDL. Vui lòng thử lại sau.', 'danger')
            return render_template('login.html')
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password_candidate):
                # Tạo session
                session['loggedin'] = True
                session['id'] = user['id']
                session['username'] = user['username']
                
                flash('Đăng nhập thành công!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Sai tên đăng nhập hoặc mật khẩu.', 'danger')
                
        except mysql.connector.Error as err:
            flash(f'Lỗi máy chủ: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Trang đăng ký tài khoản mới"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        if not conn:
            flash('Lỗi kết nối CSDL. Vui lòng thử lại sau.', 'danger')
            return render_template('register.html')

        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            account = cursor.fetchone()
            
            if account:
                flash('Tài khoản này đã tồn tại!', 'warning')
            elif not username or not password:
                flash('Vui lòng điền đầy đủ thông tin!', 'danger')
            else:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                               (username, hashed_password))
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
    """Trang bí mật - Chỉ người đã đăng nhập mới thấy"""
    if 'loggedin' in session:
        return render_template('dashboard.html', username=session['username'])
    
    flash('Vui lòng đăng nhập để xem trang này.', 'warning')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Xóa session để đăng xuất"""
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('Bạn đã đăng xuất.', 'success')
    return redirect(url_for('login'))


# --- KHỞI CHẠY APP ---
if __name__ == '__main__':
    app.run(debug=True)