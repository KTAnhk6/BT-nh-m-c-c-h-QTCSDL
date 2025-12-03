import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, date
import random
import pyodbc
from pymongo import MongoClient

# ============================================================
# 1. KẾT NỐI SQL SERVER & MONGODB
# ============================================================
DB_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-V034CN8\\SQLEXPRESS;"
    "DATABASE=QuanLyBenhVien;"
    "Trusted_Connection=yes;"
)

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "QuanLyBenhVien"


def connect_db():
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Lỗi kết nối SQL Server: {e}")
        return None


def get_mongo_db():
    try:
        client = MongoClient(MONGO_URI)
        return client[MONGO_DB_NAME]
    except Exception as e:
        print(f"Lỗi kết nối MongoDB: {e}")
        return None


# ============================================================
# 2. KHỞI TẠO HỆ THỐNG (TÀI KHOẢN, BẢNG TAIKHOAN)
# ============================================================
def ensure_system_setup():
    """
    - Tạo bảng taikhoan nếu chưa có
    - Tạo tài khoản admin/staff mặc định
    """
    conn = connect_db()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # Tạo bảng taikhoan nếu chưa có
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects 
                           WHERE object_id = OBJECT_ID(N'taikhoan') AND type in (N'U'))
            BEGIN
                CREATE TABLE taikhoan (
                    tendangnhap VARCHAR(50) PRIMARY KEY,
                    matkhau VARCHAR(255) NOT NULL,
                    quyen NVARCHAR(20) NOT NULL
                );
            END
        """)
        conn.commit()

        # Tạo admin mặc định
        cursor.execute("SELECT COUNT(*) FROM taikhoan WHERE tendangnhap = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO taikhoan(tendangnhap, matkhau, quyen) VALUES ('admin', 'admin', N'Admin')"
            )
            conn.commit()
            print("Đã tạo tài khoản admin (admin/admin)")

        # Tạo staff mặc định
        cursor.execute("SELECT COUNT(*) FROM taikhoan WHERE tendangnhap = 'staff'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO taikhoan(tendangnhap, matkhau, quyen) VALUES ('staff', 'staff', N'Staff')"
            )
            conn.commit()
            print("Đã tạo tài khoản staff (staff/staff)")

    except Exception as e:
        print("Lỗi khởi tạo hệ thống:", e)
    finally:
        conn.close()


# ============================================================
# 3. CÁC HÀM CƠ BẢN LÀM VIỆC VỚI SQL
# ============================================================
def login_check(username, password):
    conn = connect_db()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quyen FROM taikhoan
            WHERE tendangnhap = ? AND matkhau = ?
        """, (username, password))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print("Lỗi đăng nhập:", e)
        return None
    finally:
        conn.close()


def register_new_user(username, password):
    conn = connect_db()
    if conn is None:
        return False, "Không kết nối được SQL Server."

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM taikhoan WHERE tendangnhap = ?", (username,))
        if cursor.fetchone()[0] > 0:
            return False, "Tên tài khoản đã tồn tại."

        cursor.execute("""
            INSERT INTO taikhoan(tendangnhap, matkhau, quyen)
            VALUES (?, ?, N'Staff')
        """, (username, password))
        conn.commit()
        return True, "Đăng ký tài khoản thành công!"
    except Exception as e:
        return False, f"Lỗi SQL: {e}"
    finally:
        conn.close()


def get_specialties():
    """
    Lấy danh sách Chuyên khoa từ bảng BacSi
    """
    conn = connect_db()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ChuyenKhoa FROM BacSi ORDER BY ChuyenKhoa")
        return [row[0] for row in cursor.fetchall() if row[0] is not None]
    except Exception as e:
        print("Lỗi lấy chuyên khoa:", e)
        return []
    finally:
        conn.close()


def fetch_doctors():
    conn = connect_db()
    if conn is None:
        return []

    doctors = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaBS, HoTen FROM BacSi ORDER BY HoTen")
        for row in cursor.fetchall():
            doctors.append((row[0], row[1]))
        return doctors
    except Exception as e:
        print("Lỗi khi lấy danh sách bác sĩ:", e)
        return []
    finally:
        conn.close()


def fetch_patients_by_doctor(ma_bs):
    conn = connect_db()
    if conn is None:
        return []

    results = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT BN.HoTen, LK.NgayGioKham, LK.TinhTrangKham
            FROM LichKham LK
            JOIN BenhNhan BN ON LK.MaBenhNhan = BN.MaBenhNhan
            WHERE LK.MaBS = ?
            ORDER BY LK.NgayGioKham DESC
        """, (ma_bs,))
        
        for row in cursor.fetchall():
            results.append((row[0], row[1], row[2]))
        return results
    except Exception as e:
        print("Lỗi lấy bệnh nhân theo bác sĩ:", e)
        return []
    finally:
        conn.close()


def search_lichkham(keyword):
    conn = connect_db()
    if conn is None:
        return []

    results = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT BN.HoTen, BS.HoTen, LK.NgayGioKham, LK.TinhTrangKham
            FROM LichKham LK
            JOIN BenhNhan BN ON LK.MaBenhNhan = BN.MaBenhNhan
            JOIN BacSi BS ON LK.MaBS = BS.MaBS
            WHERE BN.HoTen LIKE ? OR BN.MaBenhNhan LIKE ?
            ORDER BY LK.NgayGioKham DESC
        """, (f"%{keyword}%", f"%{keyword}%"))

        for row in cursor.fetchall():
            results.append((row[0], row[1], row[2], row[3]))
        return results
    except Exception as e:
        print("Lỗi tìm lịch khám:", e)
        return []
    finally:
        conn.close()


def fetch_monthly_stats(year, month):
    conn = connect_db()
    if conn is None: 
        return []

    results = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CAST(NgayGioKham AS DATE) AS Ngay,
                   COUNT(*) AS SoLuong
            FROM LichKham
            WHERE YEAR(NgayGioKham) = ? AND MONTH(NgayGioKham) = ?
            GROUP BY CAST(NgayGioKham AS DATE)
            ORDER BY Ngay
        """, (year, month))

        for row in cursor.fetchall():
            results.append((row[0], row[1]))
        return results
    except Exception as e:
        print("Lỗi thống kê:", e)
        return []
    finally:
        conn.close()


def search_appointments_by_period(year, month=None):
    conn = connect_db()
    if conn is None:
        return []

    results = []
    try:
        cursor = conn.cursor()
        if month:
            cursor.execute("""
                SELECT BN.HoTen, BN.MaBenhNhan, BS.HoTen, 
                       LK.NgayGioKham, LK.TinhTrangKham
                FROM LichKham LK
                JOIN BenhNhan BN ON LK.MaBenhNhan = BN.MaBenhNhan
                JOIN BacSi BS ON LK.MaBS = BS.MaBS
                WHERE YEAR(LK.NgayGioKham) = ? AND MONTH(LK.NgayGioKham) = ?
                ORDER BY LK.NgayGioKham DESC
            """, (year, month))
        else:
            cursor.execute("""
                SELECT BN.HoTen, BN.MaBenhNhan, BS.HoTen, 
                       LK.NgayGioKham, LK.TinhTrangKham
                FROM LichKham LK
                JOIN BenhNhan BN ON LK.MaBenhNhan = BN.MaBenhNhan
                JOIN BacSi BS ON LK.MaBS = BS.MaBS
                WHERE YEAR(LK.NgayGioKham) = ?
                ORDER BY LK.NgayGioKham DESC
            """, (year,))

        for row in cursor.fetchall():
            results.append((row[0], row[1], row[2], row[3], row[4]))
        return results
    except Exception as e:
        print("Lỗi tra cứu theo thời gian:", e)
        return []
    finally:
        conn.close()


def fetch_inpatients():
    conn = connect_db()
    if conn is None:
        return []

    results = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                BN.HoTen,
                BN.GioiTinh,
                BN.NgaySinh,
                LK.NgayGioKham,
                ISNULL(P.TenPhong, LK.MaPhong)
            FROM
                LichKham AS LK
            JOIN
                BenhNhan AS BN ON LK.MaBenhNhan = BN.MaBenhNhan
            LEFT JOIN
                PHONG AS P ON LK.MaPhong = P.MaPhong
            WHERE
                LK.TinhTrangKham LIKE N'Điều trị nội trú%' OR LK.TinhTrangKham LIKE N'%nội trú%'
            ORDER BY LK.NgayGioKham DESC
        """)

        for row in cursor.fetchall():
            results.append((row[0], row[1], row[2], row[3], row[4]))
        return results
    except Exception as e:
        print("Lỗi nội trú:", e)
        return []
    finally:
        conn.close()


def fetch_doctor_schedule():
    conn = connect_db()
    if conn is None:
        return []

    results = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT BS.HoTen, LT.NgayTruc, LT.CaTruc, LT.ChuyenKhoaTruc
            FROM LichTruc LT
            JOIN BacSi BS ON LT.MaBS = BS.MaBS
            WHERE LT.NgayTruc >= CAST(GETDATE() AS DATE)
            ORDER BY LT.NgayTruc ASC, LT.CaTruc
        """)

        for row in cursor.fetchall():
            results.append((row[0], row[1], row[2], row[3]))
        return results
    except Exception as e:
        print("Lỗi lịch trực:", e)
        return []
    finally:
        conn.close()


def fetch_doctor_stats():
    conn = connect_db()
    if conn is None:
        return []

    results = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                BS.HoTen,
                BS.ChuyenKhoa,
                COUNT(LK.MaLichKham) AS TongSoLanKham
            FROM
                BacSi BS
            LEFT JOIN
                LichKham LK ON BS.MaBS = LK.MaBS
            GROUP BY
                BS.HoTen,
                BS.ChuyenKhoa
            ORDER BY
                TongSoLanKham DESC
        """)

        for row in cursor.fetchall():
            results.append((row[0], row[1], row[2]))
        return results
    except Exception as e:
        print("Lỗi thống kê bác sĩ:", e)
        return []
    finally:
        conn.close()


def insert_benhnhan_and_lichkham(ho_ten, ngay_sinh, gioi_tinh, dia_chi, chuyen_khoa, ngay_gio_kham):
    """
    Đăng ký bệnh nhân mới:
    - Thêm vào BenhNhan + LichKham trong SQL
    - Đồng thời lưu backup sang MongoDB
    """
    conn = connect_db()
    mongo_db = get_mongo_db()
    if conn is None:
        return False, "Không thể kết nối SQL Server"

    try:
        cursor = conn.cursor()

        # 1. Tạo mã bệnh nhân mới
        cursor.execute("""
            SELECT TOP 1 MaBenhNhan 
            FROM BenhNhan 
            ORDER BY MaBenhNhan DESC
        """)
        row = cursor.fetchone()

        if row is None:
            new_id_num = 1
        else:
            try:
                new_id_num = int(row[0][2:]) + 1  # BN0001 -> 0001
            except:
                new_id_num = random.randint(1000, 9999)

        ma_bn = f"BN{new_id_num:04d}"

        # 2. Chèn bệnh nhân (SQL)
        cursor.execute("""
            INSERT INTO BenhNhan(MaBenhNhan, HoTen, NgaySinh, GioiTinh, DiaChi)
            VALUES (?, ?, ?, ?, ?)
        """, (ma_bn, ho_ten, ngay_sinh, gioi_tinh, dia_chi))

        # 3. Lấy bác sĩ theo chuyên khoa (SQL)
        cursor.execute("""
            SELECT TOP 1 MaBS, HoTen
            FROM BacSi
            WHERE ChuyenKhoa = ?
        """, (chuyen_khoa,))
        doctor = cursor.fetchone()

        if not doctor:
            conn.rollback()
            return False, "Không tìm thấy bác sĩ phù hợp với chuyên khoa!"

        ma_bs = doctor[0]
        ten_bs = doctor[1]

        # 4. Thêm lịch khám (SQL)
        cursor.execute("""
            INSERT INTO LichKham (MaBenhNhan, MaBS, NgayGioKham, TinhTrangKham)
            VALUES (?, ?, ?, N'Chờ khám')
        """, (ma_bn, ma_bs, ngay_gio_kham))

        conn.commit()

        # 5. Ghi backup sang MongoDB (nếu kết nối được)
        if mongo_db is not None:
            try:
                bn_coll = mongo_db["benhnhan"]
                lk_coll = mongo_db["lichkham"]

                bn_coll.insert_one({
                    "MaBenhNhan": ma_bn,
                    "HoTen": ho_ten,
                    "NgaySinh": str(ngay_sinh),
                    "GioiTinh": gioi_tinh,
                    "DiaChi": dia_chi,
                    "SoDienThoai": ""
                })

                lk_coll.insert_one({
                    "MaBenhNhan": ma_bn,
                    "MaBS": ma_bs,
                    "MaPhong": None,
                    "NgayGioKham": str(ngay_gio_kham),
                    "TinhTrangKham": "Chờ khám"
                })
            except Exception as e:
                print("Lỗi backup MongoDB (có thể bỏ qua):", e)

        return True, f"Đăng ký thành công!\n\nMã BN: {ma_bn}\nKhoa: {chuyen_khoa}\nBác sĩ: {ten_bs}"

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi SQL: {str(e)}"
    finally:
        conn.close()


# ============================================================
# 4. HÀM ĐỒNG BỘ TỪ MONGODB → SQL (MODE B - THỦ CÔNG)
# ============================================================
def sync_from_mongo_main():
    """
    Đồng bộ dữ liệu từ MongoDB sang SQL Server:
    - PHONG
    - BacSi
    - BenhNhan
    - LichKham
    - LichTruc
    Tránh trùng bằng cách kiểm tra khóa chính / cặp trường.
    """
    mongo_db = get_mongo_db()
    if mongo_db is None:
        return False, "Không kết nối được MongoDB."

    conn = connect_db()
    if conn is None:
        return False, "Không kết nối được SQL Server."

    try:
        cursor = conn.cursor()

        # ---------- 1. PHONG ----------
        phong_coll = mongo_db["phong"]
        for doc in phong_coll.find({}):
            ma = doc.get("MaPhong")
            ten = doc.get("TenPhong")
            ck = doc.get("ChuyenKhoa")
            if not ma:
                continue
            cursor.execute("SELECT COUNT(*) FROM PHONG WHERE MaPhong = ?", (ma,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO PHONG(MaPhong, TenPhong, ChuyenKhoa)
                    VALUES (?, ?, ?)
                """, (ma, ten, ck))

        # ---------- 2. BacSi ----------
        bacsi_coll = mongo_db["bacsi"]
        for doc in bacsi_coll.find({}):
            ma = doc.get("MaBS")
            ten = doc.get("HoTen")
            gt = doc.get("GioiTinh")
            dc = doc.get("DiaChi")
            ck = doc.get("ChuyenKhoa")
            if not ma:
                continue
            cursor.execute("SELECT COUNT(*) FROM BacSi WHERE MaBS = ?", (ma,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO BacSi(MaBS, HoTen, GioiTinh, DiaChi, ChuyenKhoa)
                    VALUES (?, ?, ?, ?, ?)
                """, (ma, ten, gt, dc, ck))

        # ---------- 3. BenhNhan ----------
        benhnhan_coll = mongo_db["benhnhan"]
        for doc in benhnhan_coll.find({}):
            ma = doc.get("MaBenhNhan")
            ten = doc.get("HoTen")
            ns = doc.get("NgaySinh")
            gt = doc.get("GioiTinh")
            dc = doc.get("DiaChi")
            sdt = doc.get("SoDienThoai")
            if not ma:
                continue

            cursor.execute("SELECT COUNT(*) FROM BenhNhan WHERE MaBenhNhan = ?", (ma,))
            if cursor.fetchone()[0] == 0:
                # chuyển ngày sinh
                try:
                    ns_date = datetime.strptime(ns, "%Y-%m-%d").date() if ns else None
                except:
                    ns_date = None
                cursor.execute("""
                    INSERT INTO BenhNhan(MaBenhNhan, HoTen, NgaySinh, GioiTinh, DiaChi, SoDienThoai)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ma, ten, ns_date, gt, dc, sdt))

        # ---------- 4. LichKham ----------
        lichkham_coll = mongo_db["lichkham"]
        for doc in lichkham_coll.find({}):
            ma_bn = doc.get("MaBenhNhan")
            ma_bs = doc.get("MaBS")
            ma_p = doc.get("MaPhong")
            ngay = doc.get("NgayGioKham")
            tt = doc.get("TinhTrangKham")
            if not (ma_bn and ma_bs and ngay):
                continue
            try:
                ngay_dt = datetime.strptime(ngay, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    ngay_dt = datetime.fromisoformat(ngay)
                except:
                    continue

            # kiểm tra tồn tại theo bộ 4 khóa logic
            cursor.execute("""
                SELECT COUNT(*) FROM LichKham
                WHERE MaBenhNhan = ? AND MaBS = ? AND ISNULL(MaPhong,'') = ISNULL(?, '')
                      AND NgayGioKham = ?
            """, (ma_bn, ma_bs, ma_p, ngay_dt))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO LichKham(MaBenhNhan, MaBS, MaPhong, NgayGioKham, TinhTrangKham)
                    VALUES (?, ?, ?, ?, ?)
                """, (ma_bn, ma_bs, ma_p, ngay_dt, tt))

        # ---------- 5. LichTruc ----------
        lichtruc_coll = mongo_db["lichtruc"]
        for doc in lichtruc_coll.find({}):
            ma_bs = doc.get("MaBS")
            ngay = doc.get("NgayTruc")
            ca = doc.get("CaTruc")
            ck = doc.get("ChuyenKhoa") or doc.get("ChuyenKhoaTruc")
            if not (ma_bs and ngay):
                continue
            try:
                ngay_date = datetime.strptime(ngay, "%Y-%m-%d").date()
            except:
                try:
                    ngay_date = datetime.fromisoformat(ngay).date()
                except:
                    continue

            cursor.execute("""
                SELECT COUNT(*) FROM LichTruc
                WHERE MaBS = ? AND NgayTruc = ? AND ISNULL(CaTruc,'') = ISNULL(?, '')
                      AND ISNULL(ChuyenKhoaTruc,'') = ISNULL(?, '')
            """, (ma_bs, ngay_date, ca, ck))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO LichTruc(MaBS, NgayTruc, CaTruc, ChuyenKhoaTruc)
                    VALUES (?, ?, ?, ?)
                """, (ma_bs, ngay_date, ca, ck))

        conn.commit()
        return True, "Đồng bộ dữ liệu từ MongoDB sang SQL Server thành công!"
    except Exception as e:
        conn.rollback()
        print("Lỗi khi đồng bộ:", e)
        return False, f"Lỗi khi đồng bộ: {e}"
    finally:
        conn.close()


# ============================================================
# 5. GIAO DIỆN STAFF
# ============================================================
class StaffWindow:
    def __init__(self, root, parent_window):
        self.root = root 
        self.win = parent_window
        self.win.title("Hệ thống Đăng ký Khám")
        self.win.geometry("550x350")
        self.win.resizable(False, False)       

        main_frame = ttk.Frame(self.win, padding=20, style='App.TFrame') 
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Khu vực Bệnh nhân / Nhân viên", 
                  font=("Segoe UI", 13, "bold"), 
                  style='Header.TLabel').pack(pady=12)

        actions_frame = ttk.Frame(main_frame, padding=10, style='App.TFrame')
        actions_frame.pack(fill="x", pady=10)
        actions_frame.columnconfigure((0, 1), weight=1)

        ttk.Button(actions_frame, text="Đăng ký khám", 
                   command=self.open_registration_form, 
                   style='Accent.TButton').grid(row=0, column=0, padx=5, sticky="ew")

        ttk.Button(actions_frame, text="Tra cứu lịch hẹn", 
                   command=self.open_appointment_search, 
                   style='Accent.TButton').grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Button(main_frame, text="Đăng xuất", command=self.win.destroy).pack(pady=20)

    def _get_specialties_sync(self):
        return get_specialties()

    def open_registration_form(self):
        form_win = tk.Toplevel(self.win)
        form_win.title("Phiếu Đăng Ký Khám Bệnh")
        form_win.geometry("500x450")
        
        form_frame = ttk.Frame(form_win, padding=15, style='App.TFrame')
        form_frame.pack(fill="both", expand=True)
        
        ttk.Label(form_frame, text="Thông tin Bệnh nhân", 
                  font=("Segoe UI", 11, "bold"), 
                  style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=10)

        fields = [
            ("Họ tên:", tk.StringVar(value="")), 
            ("Ngày sinh (YYYY-MM-DD):", tk.StringVar(value="")),
            ("Giới tính:", tk.StringVar(value="Nam")),
            ("Địa chỉ:", tk.StringVar(value="")),
        ]
        
        self.entry_vars = {}
        for i, (label_text, var) in enumerate(fields):
            ttk.Label(form_frame, text=label_text, style='TLabel').grid(row=i+1, column=0, sticky="w", pady=5)
            if "Giới tính" in label_text:
                entry = ttk.Combobox(form_frame, textvariable=var, values=["Nam", "Nữ"], state="readonly")
            else:
                entry = ttk.Entry(form_frame, textvariable=var)
            entry.grid(row=i+1, column=1, sticky="ew", padx=10)
            self.entry_vars[label_text] = var

        current_row = len(fields) + 1

        ttk.Label(form_frame, text="Ngày khám (YYYY-MM-DD):", style='TLabel').grid(row=current_row, column=0, sticky="w", pady=5)
        self.exam_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d")) 
        ttk.Entry(form_frame, textvariable=self.exam_date_var).grid(row=current_row, column=1, sticky="ew", padx=10)
        current_row += 1

        ttk.Label(form_frame, text="Đăng ký khám Khoa:", style='TLabel').grid(row=current_row, column=0, sticky="w", pady=5)
        self.spec_var = tk.StringVar()
        specialties = self._get_specialties_sync()
        
        self.spec_combo = ttk.Combobox(form_frame, textvariable=self.spec_var, values=specialties, state="readonly")
        if specialties: 
            self.spec_combo.set(specialties[0])
        else:
            self.spec_combo['values'] = ["Tim mạch", "Nội", "Ngoại", "Nhi", "Da liễu"]
            self.spec_combo.set("Tim mạch")
            
        self.spec_combo.grid(row=current_row, column=1, sticky="ew", padx=10)
        current_row += 1

        form_frame.columnconfigure(1, weight=1)

        ttk.Button(form_frame, text="Gửi yêu cầu khám", 
                   command=lambda: self._handle_registration(form_win), 
                   style='Accent.TButton').grid(row=current_row, column=0, columnspan=2, pady=20)

    def _handle_registration(self, form_win):
        ho_ten = self.entry_vars["Họ tên:"].get().strip()
        ngay_sinh = self.entry_vars["Ngày sinh (YYYY-MM-DD):"].get().strip()
        gioi_tinh = self.entry_vars["Giới tính:"].get().strip()
        dia_chi = self.entry_vars["Địa chỉ:"].get().strip()
        
        ngay_kham_date_only = self.exam_date_var.get().strip() 
        chuyen_khoa = self.spec_var.get()

        if not all([ho_ten, ngay_sinh, gioi_tinh, ngay_kham_date_only, chuyen_khoa]):
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ thông tin.")
            return

        try:
            d_sinh = datetime.strptime(ngay_sinh, "%Y-%m-%d")
            d_kham = datetime.strptime(ngay_kham_date_only, "%Y-%m-%d").date()

            if d_sinh.year < 1900 or d_sinh.year > datetime.now().year:
                messagebox.showerror("Lỗi ngày tháng", "Năm sinh không hợp lệ.")
                return
            
            if d_kham < date.today():
                messagebox.showerror("Lỗi ngày tháng", "Ngày khám không thể ở trong quá khứ.")
                return

        except ValueError:
            messagebox.showerror("Lỗi nhập liệu", "Ngày tháng phải đúng định dạng YYYY-MM-DD.")
            return

        # Mặc định 08:00
        ngay_gio_kham_full = f"{ngay_kham_date_only} 08:00:00"

        threading.Thread(
            target=lambda: self._run_db_insert(
                ho_ten, ngay_sinh, gioi_tinh, dia_chi, chuyen_khoa, ngay_gio_kham_full, form_win
            )
        ).start()

    def _run_db_insert(self, *args):
        success, msg = insert_benhnhan_and_lichkham(*args[:-1])
        self.root.after(0, lambda: self._show_result(success, msg, args[-1]))

    def _show_result(self, success, msg, form_win):
        if success:
            messagebox.showinfo("Thành công", msg)
            form_win.destroy()
        else:
            messagebox.showerror("Thất bại", msg)

    def open_appointment_search(self):
        search_win = tk.Toplevel(self.win)
        search_win.title("Tra Cứu Lịch Hẹn")
        search_win.geometry("700x400")
        
        main_frame = ttk.Frame(search_win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        search_frame = ttk.Frame(main_frame, style='App.TFrame')
        search_frame.pack(fill="x", pady=10)
        
        ttk.Label(search_frame, text="Mã BN/Tên BN:", style='TLabel').pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", fill="x", expand=True)
        
        tree = ttk.Treeview(main_frame, columns=("TenBN", "TenBS", "TGKham", "TrangThai"), show="headings")
        ttk.Button(search_frame, text="Tìm kiếm", 
                   command=lambda: self._handle_appointment_search(tree), 
                   style='Accent.TButton').pack(side="left", padx=10)
        
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')
        
        tree.heading("TenBN", text="Tên Bệnh Nhân")
        tree.heading("TenBS", text="Bác Sĩ")
        tree.heading("TGKham", text="Ngày Giờ")
        tree.heading("TrangThai", text="Tình Trạng")

        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("TenBN", width=150, anchor='w')
        tree.column("TenBS", width=120, anchor='w')
        tree.column("TGKham", width=150, anchor='center')
        tree.column("TrangThai", width=120, anchor='center')

        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")     

    def _handle_appointment_search(self, tree):
        keyword = self.search_var.get().strip()
        if not keyword: 
            messagebox.showwarning("Lỗi", "Vui lòng nhập từ khóa.")
            return
        
        for item in tree.get_children(): 
            tree.delete(item)

        def run_search(k):
            results = search_lichkham(k)
            self.root.after(0, lambda: self._update_search_tree(results, tree))
        
        threading.Thread(target=lambda: run_search(keyword)).start()
        
    def _update_search_tree(self, results, tree):
        for item in tree.get_children():
            tree.delete(item)
        
        if not results:
            tree.insert("", "end", values=("Không tìm thấy kết quả.", "", "", ""), tags=('oddrow',))
            return
            
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            ngay_gio = row[2].strftime('%Y-%m-%d %H:%M') if isinstance(row[2], datetime) else str(row[2])
            tree.insert("", "end", values=(row[0], row[1], ngay_gio, row[3]), tags=(tag,))


# ============================================================
# 6. ỨNG DỤNG CHÍNH + ADMIN DASHBOARD
# ============================================================
class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Bệnh Viện (Hybrid Mongo + SQL Server)")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self._setup_style()
        ensure_system_setup()

        main_frame = ttk.Frame(root, padding=30, style='App.TFrame') 
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="ĐĂNG NHẬP", 
                  font=("Segoe UI", 16, "bold"), 
                  style='Header.TLabel').pack(pady=15)

        ttk.Label(main_frame, text="Tài khoản:", style='TLabel').pack(anchor="w", pady=(10, 0))
        self.user_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.user_var).pack(fill="x", pady=5)

        ttk.Label(main_frame, text="Mật khẩu:", style='TLabel').pack(anchor="w", pady=(10, 0))
        self.pass_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.pass_var, show="•").pack(fill="x", pady=5)

        btn_frame = ttk.Frame(main_frame, style='App.TFrame')
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Đăng nhập", 
                   command=self.handle_login, 
                   style='Accent.TButton').pack(side="left", padx=10, ipadx=10)
        ttk.Button(btn_frame, text="Đăng ký mới", 
                   command=self.open_register_window).pack(side="left", padx=10, ipadx=10)

        self.root.bind("<Return>", lambda e: self.handle_login())

    def _setup_style(self):
        COLOR_PRIMARY = '#0078D7'
        COLOR_BACKGROUND = '#F0F0F0'
        COLOR_TEXT = '#333333'

        style = ttk.Style()
        style.theme_use("clam")
        style.configure('App.TFrame', background=COLOR_BACKGROUND)
        style.configure('TFrame', background=COLOR_BACKGROUND)
        style.configure('TLabel', background=COLOR_BACKGROUND, foreground=COLOR_TEXT)
        style.configure('Header.TLabel', background=COLOR_BACKGROUND, foreground=COLOR_PRIMARY)
        style.configure('Accent.TButton', 
                        foreground='white', 
                        background=COLOR_PRIMARY, 
                        font=("Segoe UI", 10, "bold"),
                        padding=6)
        style.map('Accent.TButton', 
                  background=[('active', '#005CBF'), ('pressed', '#005CBF')])
        style.configure("Treeview.Heading", 
                        font=("Segoe UI", 10, "bold"), 
                        background=COLOR_PRIMARY,
                        foreground='white')
        style.configure("Treeview", 
                        rowheight=25,
                        background='white',
                        foreground=COLOR_TEXT,
                        fieldbackground='white')
        style.map('Treeview', background=[('selected', COLOR_PRIMARY)])

    def open_register_window(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Đăng Ký Tài Khoản")
        reg_win.geometry("350x250")
        
        f = ttk.Frame(reg_win, padding=20, style='App.TFrame')
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Tên đăng nhập:", style='TLabel').pack(anchor="w")
        u_var = tk.StringVar()
        ttk.Entry(f, textvariable=u_var).pack(fill="x")

        ttk.Label(f, text="Mật khẩu:", style='TLabel').pack(anchor="w")
        p_var = tk.StringVar()
        ttk.Entry(f, textvariable=p_var, show="•").pack(fill="x")
        
        def do_reg():
            if not u_var.get() or not p_var.get():
                messagebox.showwarning("Lỗi", "Vui lòng nhập đủ thông tin")
                return
            success, msg = register_new_user(u_var.get(), p_var.get())
            if success:
                messagebox.showinfo("Thành công", msg)
                reg_win.destroy()
            else:
                messagebox.showerror("Lỗi", msg)
                
        ttk.Button(f, text="Đăng Ký Ngay", command=do_reg, style='Accent.TButton').pack(pady=15)

    def handle_login(self):
        u = self.user_var.get().strip()
        p = self.pass_var.get().strip()
        
        role = login_check(u, p)
        if role == 'Admin':
            self.open_admin_window()
        elif role == 'Staff':
            self.open_staff_window()
        else:
            messagebox.showerror("Lỗi", "Tài khoản hoặc mật khẩu không đúng!")

    def open_staff_window(self):
        win = tk.Toplevel(self.root)
        StaffWindow(self.root, win)

    # ================= ADMIN DASHBOARD =======================
    def open_admin_window(self):
        win = tk.Toplevel(self.root)
        win.title("Admin Dashboard - Hybrid Mongo + SQL Server")
        win.geometry("650x650")
        
        main_frame = ttk.Frame(win, padding=20, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="BẢNG ĐIỀU KHIỂN QUẢN TRỊ", 
                  font=("Segoe UI", 16, "bold"),
                  style='Header.TLabel').pack(pady=10)
        
        func_frame = ttk.Frame(main_frame, padding=10, style='App.TFrame')
        func_frame.pack(fill="x", pady=15)
        
        btn_style = 'Accent.TButton'
        ttk.Button(func_frame, text="1. Danh sách BN Theo Bác Sĩ", 
                   command=self.show_patients_by_doctor_list, 
                   style=btn_style).pack(fill="x", pady=5)
        ttk.Button(func_frame, text="2. Lịch Khám Bác Sĩ Theo Ngày", 
                   command=self.show_doctor_appointments_by_date_picker, 
                   style=btn_style).pack(fill="x", pady=5)
        ttk.Button(func_frame, text="3. TK Số Lượng BN Theo Tháng/Ngày", 
                   command=self.show_patient_stats, 
                   style=btn_style).pack(fill="x", pady=5)
        ttk.Button(func_frame, text="4. Tra Cứu BN Theo Năm/Tháng", 
                   command=self.show_period_search, 
                   style=btn_style).pack(fill="x", pady=5)
        ttk.Button(func_frame, text="5. Báo Cáo BN Nội Trú", 
                   command=self.show_inpatient_report, 
                   style=btn_style).pack(fill="x", pady=5)
        ttk.Button(func_frame, text="6. Quản Lý Lịch Trực Bác Sĩ", 
                   command=lambda: self.show_doctor_schedule(win), 
                   style=btn_style).pack(fill="x", pady=5)
        ttk.Button(func_frame, text="7. TK Tổng Số Ca Khám Bác Sĩ", 
                   command=lambda: self.show_doctor_stats(win), 
                   style=btn_style).pack(fill="x", pady=5)

        # Nút đồng bộ dữ liệu từ Mongo
        btn8 = tk.Button(
            win,
            text="8. Đồng bộ dữ liệu từ MongoDB → SQL Server",
            bg="#007bff",
            fg="white",
            font=("Arial", 12, "bold"),
            command=lambda: [
                self.sync_from_mongo(),
                messagebox.showinfo("Thành công", "Đồng bộ dữ liệu thành công từ MongoDB → SQL Server!")
            ]
        )
        btn8.pack(pady=5)

        ttk.Button(main_frame, text="Đăng xuất", command=win.destroy).pack(pady=20)

    # ============ NÚT ĐỒNG BỘ MONGODB → SQL ==============
    def sync_from_mongo(self):
        def run():
            success, msg = sync_from_mongo_main()
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Đồng bộ", msg))
            else:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", msg))
        threading.Thread(target=run).start()

    # =============== Chức năng 1 =============================
    def show_patients_by_doctor_list(self):
        win = tk.Toplevel(self.root)
        win.title("Bệnh Nhân Theo Bác Sĩ")
        win.geometry("650x450")
        
        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)
        
        doctors = fetch_doctors()
        if not doctors:
            messagebox.showinfo("Thông báo", "Không tìm thấy bác sĩ nào trong hệ thống.\nHãy thử bấm nút Đồng bộ từ Mongo.")
            win.destroy()
            return
            
        doctor_map = {f"{d[1]} ({d[0]})": d[0] for d in doctors}
        doctor_names = list(doctor_map.keys())
        
        control_frame = ttk.Frame(main_frame, style='App.TFrame')
        control_frame.pack(fill="x", pady=5)
        ttk.Label(control_frame, text="Chọn Bác Sĩ:", style='TLabel').pack(side="left", padx=5)
        
        doc_var = tk.StringVar()
        doc_combo = ttk.Combobox(control_frame, textvariable=doc_var, values=doctor_names, state="readonly", width=40)
        if doctor_names:
            doc_combo.set(doctor_names[0])
        doc_combo.pack(side="left", fill="x", expand=True, padx=5)

        tree = ttk.Treeview(main_frame, columns=("HoTen", "NgayGioKham", "TinhTrangKham"), show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')

        tree.heading("HoTen", text="Tên Bệnh Nhân")
        tree.heading("NgayGioKham", text="Ngày Giờ Khám")
        tree.heading("TinhTrangKham", text="Tình Trạng")

        tree.column("HoTen", width=250, anchor='w')
        tree.column("NgayGioKham", width=150, anchor='center')
        tree.column("TinhTrangKham", width=100, anchor='center')
        tree.pack(fill="both", expand=True, pady=10)
        
        def search():
            selected_name = doc_var.get()
            if not selected_name:
                return
            ma_bs = doctor_map[selected_name]
            
            for item in tree.get_children():
                tree.delete(item)
            
            def run_fetch():
                results = fetch_patients_by_doctor(ma_bs)
                self.root.after(0, lambda: self._update_patient_by_doctor_tree(results, tree))
            threading.Thread(target=run_fetch).start()
            
        ttk.Button(control_frame, text="Xem", command=search, style='Accent.TButton').pack(side="left", padx=5)
        if doctor_names:
            search()

    def _update_patient_by_doctor_tree(self, results, tree):
        if not results:
            tree.insert("", "end", values=("Không có bệnh nhân.", "", ""), tags=('oddrow',))
            return
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            ngay_gio = row[1].strftime('%Y-%m-%d %H:%M') if isinstance(row[1], datetime) else str(row[1])
            tree.insert("", "end", values=(row[0], ngay_gio, row[2]), tags=(tag,))

    # =============== Chức năng 2 =============================
    def show_doctor_appointments_by_date_picker(self):
        win = tk.Toplevel(self.root)
        win.title("Lịch Khám Theo Bác Sĩ và Ngày")
        win.geometry("700x500")
        
        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)
        
        doctors = fetch_doctors()
        if not doctors:
            messagebox.showinfo("Thông báo", "Không tìm thấy bác sĩ nào.\nHãy thử bấm nút Đồng bộ từ Mongo.")
            win.destroy()
            return
            
        doctor_map = {f"{d[1]} ({d[0]})": d[0] for d in doctors}
        doctor_names = list(doctor_map.keys())
        
        control_frame = ttk.Frame(main_frame, style='App.TFrame')
        control_frame.pack(fill="x", pady=5)
        control_frame.columnconfigure((1, 3), weight=1)
        
        ttk.Label(control_frame, text="Chọn Bác Sĩ:", style='TLabel').grid(row=0, column=0, padx=5, sticky="w")
        self.doc_app_var = tk.StringVar()
        self.doc_app_combo = ttk.Combobox(control_frame, textvariable=self.doc_app_var, values=doctor_names, state="readonly")
        if doctor_names:
            self.doc_app_combo.set(doctor_names[0])
        self.doc_app_combo.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(control_frame, text="Ngày (YYYY-MM-DD):", style='TLabel').grid(row=0, column=2, padx=5, sticky="w")
        self.date_app_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(control_frame, textvariable=self.date_app_var).grid(row=0, column=3, padx=5, sticky="ew")

        tree = ttk.Treeview(main_frame, columns=("HoTen", "NgayGioKham", "TinhTrangKham"), show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')
        tree.heading("HoTen", text="Tên Bệnh Nhân")
        tree.heading("NgayGioKham", text="Ngày Giờ Khám")
        tree.heading("TinhTrangKham", text="Tình Trạng")

        tree.column("HoTen", width=250, anchor='w')
        tree.column("NgayGioKham", width=150, anchor='center')
        tree.column("TinhTrangKham", width=100, anchor='center')
        tree.pack(fill="both", expand=True, pady=10)
        
        def search_appointments():
            selected_name = self.doc_app_var.get()
            ngay = self.date_app_var.get()
            if not selected_name or not ngay:
                return

            try:
                datetime.strptime(ngay, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Lỗi", "Ngày phải đúng định dạng YYYY-MM-DD.")
                return

            ma_bs = doctor_map[selected_name]
            for item in tree.get_children():
                tree.delete(item)
            
            def run_fetch():
                results = fetch_patients_by_doctor(ma_bs)
                filtered = []
                for r in results:
                    ngay_kham = r[1]
                    if isinstance(ngay_kham, datetime) and ngay_kham.strftime("%Y-%m-%d") == ngay:
                        filtered.append(r)
                    elif isinstance(ngay_kham, str) and ngay_kham.startswith(ngay):
                        filtered.append(r)
                self.root.after(0, lambda: self._update_patient_by_doctor_tree(filtered, tree))

            threading.Thread(target=run_fetch).start()
            
        ttk.Button(control_frame, text="Tìm Lịch Khám", 
                   command=search_appointments, 
                   style='Accent.TButton').grid(row=0, column=4, padx=5, sticky="e")

    # =============== Chức năng 3 =============================
    def show_patient_stats(self):
        win = tk.Toplevel(self.root)
        win.title("Thống Kê Số Lượng Bệnh Nhân Khám Bệnh")
        win.geometry("550x450")
        
        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        current_year = date.today().year
        current_month = date.today().month
        
        control_frame = ttk.Frame(main_frame, style='App.TFrame')
        control_frame.pack(fill="x", pady=5)

        ttk.Label(control_frame, text="Năm:", style='TLabel').pack(side="left", padx=5)
        self.year_stats_var = tk.StringVar(value=str(current_year))
        ttk.Entry(control_frame, textvariable=self.year_stats_var, width=5).pack(side="left", padx=5)
        
        ttk.Label(control_frame, text="Tháng:", style='TLabel').pack(side="left", padx=5)
        self.month_stats_var = tk.StringVar(value=str(current_month))
        months = [str(i) for i in range(1, 13)]
        ttk.Combobox(control_frame, textvariable=self.month_stats_var, values=months, state="readonly", width=5).pack(side="left", padx=5)
        
        tree = ttk.Treeview(main_frame, columns=("Ngay", "SoLuong"), show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')
        tree.heading("Ngay", text="Ngày")
        tree.heading("SoLuong", text="Số Lượng Bệnh Nhân")

        tree.column("Ngay", width=200, anchor='center')
        tree.column("SoLuong", width=150, anchor='center')
        tree.pack(fill="both", expand=True, pady=10)
        
        def search_stats():
            try:
                year = int(self.year_stats_var.get())
                month = int(self.month_stats_var.get())
            except ValueError:
                messagebox.showerror("Lỗi", "Năm và Tháng phải là số nguyên.")
                return

            for item in tree.get_children():
                tree.delete(item)
            
            def run_fetch():
                results = fetch_monthly_stats(year, month)
                self.root.after(0, lambda: self._update_monthly_stats_tree(results, tree, year, month))
            threading.Thread(target=run_fetch).start()
            
        ttk.Button(control_frame, text="Thống kê", 
                   command=search_stats, 
                   style='Accent.TButton').pack(side="left", padx=10)
        search_stats()

    def _update_monthly_stats_tree(self, results, tree, year, month):
        if not results:
            tree.insert("", "end", values=(f"Không có dữ liệu trong tháng {month}/{year}.", ""), tags=('oddrow',))
            return
            
        total_patients = 0
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            ngay = row[0].strftime('%Y-%m-%d') if isinstance(row[0], (datetime, date)) else str(row[0])
            tree.insert("", "end", values=(ngay, row[1]), tags=(tag,))
            total_patients += row[1]
            
        tree.insert("", "end", values=("TỔNG CỘNG", total_patients), tags=('evenrow',))

    # =============== Chức năng 4 =============================
    def show_period_search(self):
        win = tk.Toplevel(self.root)
        win.title("Tra Cứu Bệnh Nhân Khám Bệnh theo Thời Gian")
        win.geometry("800x500")
        
        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        current_year = date.today().year
        
        control_frame = ttk.Frame(main_frame, style='App.TFrame')
        control_frame.pack(fill="x", pady=5)

        ttk.Label(control_frame, text="Năm:", style='TLabel').pack(side="left", padx=5)
        self.search_year_var = tk.StringVar(value=str(current_year))
        ttk.Entry(control_frame, textvariable=self.search_year_var, width=5).pack(side="left", padx=5)
        
        ttk.Label(control_frame, text="Tháng (tùy chọn, 1-12):", style='TLabel').pack(side="left", padx=5)
        self.search_month_var = tk.StringVar(value="")
        months_and_empty = [""] + [str(i) for i in range(1, 13)]
        ttk.Combobox(control_frame, textvariable=self.search_month_var, values=months_and_empty, width=5).pack(side="left", padx=5)
        
        tree = ttk.Treeview(main_frame, 
                            columns=("HoTen", "MaBenhNhan", "TenBS", "NgayGioKham", "TrangThai"), 
                            show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')
        tree.heading("HoTen", text="Tên BN")
        tree.heading("MaBenhNhan", text="Mã BN")
        tree.heading("TenBS", text="Bác sĩ")
        tree.heading("NgayGioKham", text="Ngày giờ khám")
        tree.heading("TrangThai", text="Tình trạng")

        tree.column("HoTen", width=180, anchor='w')
        tree.column("MaBenhNhan", width=90, anchor='center')
        tree.column("TenBS", width=150, anchor='w')
        tree.column("NgayGioKham", width=150, anchor='center')
        tree.column("TrangThai", width=120, anchor='center')
        tree.pack(fill="both", expand=True, pady=10)

        def do_search():
            try:
                year = int(self.search_year_var.get())
            except ValueError:
                messagebox.showerror("Lỗi", "Năm phải là số nguyên.")
                return
            
            month_text = self.search_month_var.get().strip()
            if month_text == "":
                month = None
            else:
                try:
                    month = int(month_text)
                    if month < 1 or month > 12:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Lỗi", "Tháng phải để trống hoặc là số từ 1 tới 12.")
                    return
            
            for item in tree.get_children():
                tree.delete(item)

            def run_fetch():
                results = search_appointments_by_period(year, month)
                self.root.after(0, lambda: self._update_period_search_tree(results, tree))
            threading.Thread(target=run_fetch).start()

        ttk.Button(control_frame, text="Tra cứu", 
                   command=do_search, 
                   style='Accent.TButton').pack(side="left", padx=10)

    def _update_period_search_tree(self, results, tree):
        if not results:
            tree.insert("", "end", values=("Không có dữ liệu.", "", "", "", ""), tags=('oddrow',))
            return
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            ngay = row[3].strftime('%Y-%m-%d %H:%M') if isinstance(row[3], datetime) else str(row[3])
            tree.insert("", "end", values=(row[0], row[1], row[2], ngay, row[4]), tags=(tag,))

    # =============== Chức năng 5 =============================
    def show_inpatient_report(self):
        win = tk.Toplevel(self.root)
        win.title("Báo cáo bệnh nhân nội trú")
        win.geometry("750x450")

        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(main_frame, 
                            columns=("HoTen", "GioiTinh", "NgaySinh", "NgayNhapVien", "Phong"), 
                            show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')

        tree.heading("HoTen", text="Tên BN")
        tree.heading("GioiTinh", text="Giới tính")
        tree.heading("NgaySinh", text="Ngày sinh")
        tree.heading("NgayNhapVien", text="Ngày nhập viện")
        tree.heading("PhongDieuTri", text="Phòng điều trị")

        tree.column("HoTen", width=200, anchor='w')
        tree.column("GioiTinh", width=80, anchor='center')
        tree.column("NgaySinh", width=100, anchor='center')
        tree.column("NgayNhapVien", width=150, anchor='center')
        tree.column("PhongDieuTri", width=150, anchor='center')
        tree.pack(fill="both", expand=True, pady=10)

        def run_fetch():
            results = fetch_inpatients()
            self.root.after(0, lambda: self._update_inpatient_tree(results, tree))
        threading.Thread(target=run_fetch).start()

    def _update_inpatient_tree(self, results, tree):
        if not results:
            tree.insert("", "end", values=("Không có bệnh nhân nội trú.", "", "", "", ""), tags=('oddrow',))
            return
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            ngay_sinh = row[2].strftime('%Y-%m-%d') if isinstance(row[2], (datetime, date)) else str(row[2])
            ngay_nhap = row[3].strftime('%Y-%m-%d %H:%M') if isinstance(row[3], datetime) else str(row[3])
            tree.insert("", "end", values=(row[0], row[1], ngay_sinh, ngay_nhap, row[4]), tags=(tag,))

    # =============== Chức năng 6 =============================
    def show_doctor_schedule(self, parent):
        win = tk.Toplevel(parent)
        win.title("Lịch trực bác sĩ")
        win.geometry("700x450")

        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(main_frame, 
                            columns=("TenBS", "NgayTruc", "CaTruc", "ChuyenKhoa"), 
                            show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')

        tree.heading("TenBS", text="Bác sĩ")
        tree.heading("NgayTruc", text="Ngày trực")
        tree.heading("CaTruc", text="Ca trực")
        tree.heading("ChuyenKhoa", text="Chuyên khoa trực")

        tree.column("TenBS", width=200, anchor='w')
        tree.column("NgayTruc", width=120, anchor='center')
        tree.column("CaTruc", width=100, anchor='center')
        tree.column("ChuyenKhoa", width=200, anchor='w')
        tree.pack(fill="both", expand=True, pady=10)

        def run_fetch():
            results = fetch_doctor_schedule()
            self.root.after(0, lambda: self._update_schedule_tree(results, tree))
        threading.Thread(target=run_fetch).start()

    def _update_schedule_tree(self, results, tree):
        if not results:
            tree.insert("", "end", values=("Không có lịch trực.", "", "", ""), tags=('oddrow',))
            return
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            ngay = row[1].strftime('%Y-%m-%d') if isinstance(row[1], (datetime, date)) else str(row[1])
            tree.insert("", "end", values=(row[0], ngay, row[2], row[3]), tags=(tag,))

    # =============== Chức năng 7 =============================
    def show_doctor_stats(self, parent):
        win = tk.Toplevel(parent)
        win.title("Thống kê số ca khám của bác sĩ")
        win.geometry("650x450")

        main_frame = ttk.Frame(win, padding=15, style='App.TFrame')
        main_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(main_frame, 
                            columns=("TenBS", "ChuyenKhoa", "SoCa"), 
                            show="headings")
        tree.tag_configure('oddrow', background='#F0F0FF')
        tree.tag_configure('evenrow', background='#FFFFFF')

        tree.heading("TenBS", text="Bác sĩ")
        tree.heading("ChuyenKhoa", text="Chuyên khoa")
        tree.heading("SoCa", text="Số ca khám")

        tree.column("TenBS", width=220, anchor='w')
        tree.column("ChuyenKhoa", width=150, anchor='w')
        tree.column("SoCa", width=100, anchor='center')
        tree.pack(fill="both", expand=True, pady=10)

        def run_fetch():
            results = fetch_doctor_stats()
            self.root.after(0, lambda: self._update_doctor_stats_tree(results, tree))
        threading.Thread(target=run_fetch).start()

    def _update_doctor_stats_tree(self, results, tree):
        if not results:
            tree.insert("", "end", values=("Không có dữ liệu.", "", ""), tags=('oddrow',))
            return
        for i, row in enumerate(results):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            tree.insert("", "end", values=(row[0], row[1], row[2]), tags=(tag,))


# ============================================================
# 7. CHẠY ỨNG DỤNG
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()