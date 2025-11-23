import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pyodbc
import threading
# Cấu hình kết nối tới SQL Server LocalDB
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\MSSQLLocalDB;"
    "DATABASE=quiz_fun;"
    "Trusted_Connection=yes;"
)

def connect_db():
    """Tạo và trả về kết nối tới CSDL SQL Server."""
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        return conn
    except pyodbc.Error as e:
        print(f"Lỗi kết nối SQL Server: {e}")
        return None
    return None
class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống quản lý bệnh viện - Đăng nhập")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        # Khung chính
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Tiêu đề
        title = ttk.Label(main_frame, text="Đăng nhập hệ thống", font=("Segoe UI", 14, "bold"))
        title.pack(pady=(0, 12))

        # Nhập tài khoản
        user_frame = ttk.Frame(main_frame)
        user_frame.pack(fill="x", pady=6)
        ttk.Label(user_frame, text="Tài khoản:").pack(side="left")
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(user_frame, textvariable=self.username_var)
        self.username_entry.pack(side="right", fill="x", expand=True)

        # Nhập mật khẩu
        pass_frame = ttk.Frame(main_frame)
        pass_frame.pack(fill="x", pady=6)
        ttk.Label(pass_frame, text="Mật khẩu:").pack(side="left")
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(pass_frame, textvariable=self.password_var, show="•")
        self.password_entry.pack(side="right", fill="x", expand=True)

        # Nút đăng nhập
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=16)
        login_btn = ttk.Button(btn_frame, text="Đăng nhập", command=self.handle_login)
        login_btn.pack()

        # Gợi ý
        hint = ttk.Label(main_frame, text="Gợi ý: admin / admin", foreground="#666")
        hint.pack(pady=(6, 0))

        # Enter để đăng nhập
        self.root.bind("<Return>", lambda e: self.handle_login())

        # Thiết lập style nhẹ nhàng
        self._setup_style()

    def _setup_style(self):
        style = ttk.Style()
        # Đảm bảo tương thích Windows
        style.theme_use("vista" if "vista" in style.theme_names() else "default")

    def handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if username == "admin" and password == "admin":
            self.open_admin_window()
        else:
            self.open_staff_window()

    def open_admin_window(self):
        # Tạo cửa sổ mới cho Admin
        win = tk.Toplevel(self.root)
        win.title("Bảng điều khiển Admin")
        win.geometry("600x380")
        ttk.Label(win, text="Bảng điều khiển Admin", font=("Segoe UI", 13, "bold")).pack(pady=12)

        # Khu chức năng ví dụ
        nav = ttk.Notebook(win)
        nav.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab quản lý bệnh nhân
        patients_tab = ttk.Frame(nav, padding=10)
        nav.add(patients_tab, text="Bệnh nhân")
        ttk.Label(patients_tab, text="Quản lý hồ sơ bệnh nhân (thêm/sửa/xóa/tìm kiếm)").pack(anchor="w")

        # Tab quản lý bác sĩ
        doctors_tab = ttk.Frame(nav, padding=10)
        nav.add(doctors_tab, text="Bác sĩ")
        ttk.Label(doctors_tab, text="Quản lý lịch làm việc và chuyên khoa").pack(anchor="w")

        # Tab báo cáo hệ thống
        reports_tab = ttk.Frame(nav, padding=10)
        nav.add(reports_tab, text="Báo cáo")
        ttk.Label(reports_tab, text="Thống kê thu chi, giường bệnh, công suất").pack(anchor="w")

        # Nút đăng xuất
        ttk.Button(win, text="Đăng xuất", command=win.destroy).pack(pady=8)

    def open_staff_window(self):
        # Tạo cửa sổ mới cho Nhân viên/Khách
        win = tk.Toplevel(self.root)
        win.title("Bảng điều khiển Nhân viên/Khách")
        win.geometry("520x320")
        ttk.Label(win, text="Bảng điều khiển Nhân viên/Khách", font=("Segoe UI", 13, "bold")).pack(pady=12)

        info = ttk.Label(
            win,
            text="Bạn đang ở chế độ giới hạn.\nMột số chức năng chỉ hiển thị ở tài khoản Admin.",
            foreground="#444",
            justify="center"
        )
        info.pack(pady=6)

        # Chức năng tối thiểu
        actions_frame = ttk.Frame(win, padding=10)
        actions_frame.pack(fill="x")
        ttk.Button(actions_frame, text="Đăng ký khám").pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Tra cứu lịch hẹn").pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Xem phòng/giường trống").pack(side="left", padx=5)

        # Gợi ý nâng cấp
        ttk.Label(win, text="Để sử dụng đầy đủ tính năng, vui lòng đăng nhập bằng tài khoản Admin.").pack(pady=10)

        ttk.Button(win, text="Đóng", command=win.destroy).pack(pady=8)


if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()