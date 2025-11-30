-- Bước 1: TẠO VÀ CHUYỂN SANG CƠ SỞ DỮ LIỆU LỚN: QuanLyBenhVien
----------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'QuanLyBenhVien')
BEGIN
    -- SỬA LỖI: Thêm COLLATE vào đây để thiết lập Collation ngay khi tạo Database
    CREATE DATABASE QuanLyBenhVien COLLATE Vietnamese_CI_AS;
END
GO

USE QuanLyBenhVien;
GO

PRINT N'--- ĐÃ TẠO VÀ CHUYỂN SANG DATABASE: QuanLyBenhVien ---';
GO

-- Bước 2: DỌN DẸP CÁC OBJECT CŨ
----------------------------------------------------------------------
IF OBJECT_ID('trg_KiemTraXungDotLichKham', 'TR') IS NOT NULL DROP TRIGGER trg_KiemTraXungDotLichKham;
IF OBJECT_ID('vw_ThongKeTheoNgay', 'V') IS NOT NULL DROP VIEW vw_ThongKeTheoNgay;
IF OBJECT_ID('vw_ThongKeTheoThang', 'V') IS NOT NULL DROP VIEW vw_ThongKeTheoThang;
GO
IF OBJECT_ID('LichTruc', 'U') IS NOT NULL DROP TABLE LichTruc;
IF OBJECT_ID('LichKham', 'U') IS NOT NULL DROP TABLE LichKham;
IF OBJECT_ID('BenhNhan', 'U') IS NOT NULL DROP TABLE BenhNhan;
IF OBJECT_ID('BacSi', 'U') IS NOT NULL DROP TABLE BacSi;
IF OBJECT_ID('PHONG', 'U') IS NOT NULL DROP TABLE PHONG;
GO

-- Bước 3: TẠO CÁC BẢNG (DDL)
----------------------------------------------------------------------

CREATE TABLE PHONG (
    MaPhong CHAR(5) PRIMARY KEY,
    TenPhong NVARCHAR(100) NOT NULL,
    ChuyenKhoa NVARCHAR(100)
);
GO

CREATE TABLE BacSi (
    MaBS CHAR(5) PRIMARY KEY,
    HoTen NVARCHAR(50) NOT NULL,
    GioiTinh NVARCHAR(5),
    DiaChi NVARCHAR(100),
    ChuyenKhoa NVARCHAR(50) NOT NULL
);
GO

CREATE TABLE BenhNhan (
    MaBenhNhan VARCHAR(15) PRIMARY KEY,
    HoTen NVARCHAR(100) NOT NULL,
    NgaySinh DATE,
    GioiTinh NVARCHAR(10) CHECK (GioiTinh IN (N'Nam', N'Nữ')),
    DiaChi NVARCHAR(255),
    SoDienThoai VARCHAR(15)
);
GO

CREATE TABLE LichKham (
    MaLichKham INT IDENTITY(1,1) PRIMARY KEY,
    MaBenhNhan VARCHAR(15) NOT NULL,
    MaBS CHAR(5) NOT NULL,
    MaPhong CHAR(5),
    NgayGioKham DATETIME NOT NULL,
    TinhTrangKham NVARCHAR(100) DEFAULT N'Chờ khám',
    FOREIGN KEY (MaBenhNhan) REFERENCES BenhNhan(MaBenhNhan),
    FOREIGN KEY (MaBS) REFERENCES BacSi(MaBS),
    FOREIGN KEY (MaPhong) REFERENCES PHONG(MaPhong)
);
GO

CREATE TABLE LichTruc (
    MaTruc INT IDENTITY(1,1) PRIMARY KEY,
    MaBS CHAR(5) NOT NULL,
    NgayTruc DATE NOT NULL,
    CaTruc NVARCHAR(20),
    ChuyenKhoaTruc NVARCHAR(50) NOT NULL,
    FOREIGN KEY (MaBS) REFERENCES BacSi(MaBS)
);
GO

-- Bước 4: CHÈN DỮ LIỆU TỔNG HỢP (DML)
----------------------------------------------------------------------

INSERT INTO PHONG (MaPhong, TenPhong, ChuyenKhoa) VALUES
('P01', N'Phòng khám Tim Mạch', N'Tim mạch'),
('P02', N'Phòng khám Nhi', N'Nhi khoa'),
('P03', N'Phòng khám Da Liễu', N'Da liễu'),
('P04', N'Phòng Nội tổng hợp', N'Nội khoa'),
('P05', N'Phòng Ngoại tổng hợp', N'Ngoại khoa');
GO

-- Bước 4.1: CHÈN DỮ LIỆU BÁC SĨ (Đảm bảo mỗi khoa chỉ có 2 người)
----------------------------------------------------------------------
PRINT N'--- CHÈN DỮ LIỆU BÁC SĨ (MỖI KHOA 2 NGƯỜI) ---';

-- Tim mạch (BS001, BS004)
INSERT INTO BacSi (MaBS, HoTen, GioiTinh, DiaChi, ChuyenKhoa) VALUES
('BS001', N'Nguyễn Văn An', N'Nam', N'123 Đường A, Hà Nội', N'Tim mạch'),
('BS004', N'Phạm Thu Dung', N'Nữ', N'101 Phố D, Hà Nội', N'Tim mạch');

-- Nhi khoa (BS002, BS009)
INSERT INTO BacSi (MaBS, HoTen, GioiTinh, DiaChi, ChuyenKhoa) VALUES
('BS002', N'Trần Thị Bình', N'Nữ', N'456 Phố B, TP.HCM', N'Nhi khoa'),
('BS009', N'Đỗ Thị Hương', N'Nữ', N'555 Phố E, Hà Nội', N'Nhi khoa');

-- Da liễu (BS003, BS010)
INSERT INTO BacSi (MaBS, HoTen, GioiTinh, DiaChi, ChuyenKhoa) VALUES
('BS003', N'Lê Minh Cường', N'Nam', N'789 Đường C, Đà Nẵng', N'Da liễu'),
('BS010', N'Hoàng Thanh Trúc', N'Nữ', N'222 Phố F, TP.HCM', N'Da liễu');

-- Nội khoa (BS005, BS006)
INSERT INTO BacSi (MaBS, HoTen, GioiTinh, ChuyenKhoa) VALUES
('BS005', N'Vũ Hải Yến', N'Nữ', N'Nội khoa'),
('BS006', N'Trần Thị Mai', N'Nữ', N'Nội khoa');

-- Ngoại khoa (BS007, BS008)
INSERT INTO BacSi (MaBS, HoTen, GioiTinh, ChuyenKhoa) VALUES
('BS007', N'Phạm Văn Cường', N'Nam', N'Ngoại khoa'),
('BS008', N'Lê Văn Minh', N'Nam', N'Ngoại khoa');
GO

-- Chèn dữ liệu bệnh nhân và các bảng khác
INSERT INTO BenhNhan (MaBenhNhan, HoTen, NgaySinh, GioiTinh, DiaChi, SoDienThoai) VALUES
('BN-A001', N'Nguyễn Văn An', '1990-05-15', N'Nam', N'123 Đường Lê Lợi, Quận 1, TP.HCM', '0901234567'),
('BN-A002', N'Trần Thị Bình', '1985-08-20', N'Nữ', N'456 Đường Nguyễn Huệ, Quận 1, TP.HCM', '0912345678'),
('BN-A003', N'Lê Văn Cường', '1978-12-10', N'Nam', N'789 Đường Pasteur, Quận 3, TP.HCM', '0923456789'),
('BN-A004', N'Phạm Thị Dung', '1995-03-25', N'Nữ', N'321 Đường Cách Mạng Tháng 8, Quận 10, TP.HCM', '0934567890'),
('BN-A005', N'Hoàng Văn Em', '1982-07-30', N'Nam', N'654 Đường 3/2, Quận 10, TP.HCM', '0945678901'),
('BN-B001', N'Nguyễn Văn A', '1990-01-01', N'Nam', N'TP.HCM', NULL),
('BN-B002', N'Lê Thị B', '1995-03-02', N'Nữ', N'TP.HCM', NULL),
('BN-B003', N'Trần Văn C', '1988-05-20', N'Nam', N'TP.HCM', NULL),
('BN-B004', N'Phạm Thị D', '2000-09-15', N'Nữ', N'TP.HCM', NULL),
('BN-C001', N'Nguyễn Văn A', '1990-05-12', N'Nam', N'Hà Nội', '0987654321'),
('BN-C002', N'Nguyễn Thị B', '1991-06-13', N'Nữ', N'Hà Nội', '0983665512'),
('BN-C003', N'Trần Văn C', '1992-07-14', N'Nam', N'Hà Nội', '0988655321');
GO

-- Cập nhật LichTruc: Chỉ sử dụng các MaBS (BS001, BS004, BS002, BS009, BS003, BS010, BS005, BS007)
INSERT INTO LichTruc (MaBS, NgayTruc, CaTruc, ChuyenKhoaTruc) VALUES
('BS001', '2025-11-15', N'Sáng', N'Tim mạch'),
('BS002', '2025-11-15', N'Chiều', N'Nhi khoa'),
('BS004', '2025-11-16', N'Tối', N'Tim mạch'),
('BS003', '2025-11-16', N'Sáng', N'Da liễu'),
('BS005', '2025-11-17', N'Sáng', N'Nội khoa'),
('BS007', '2025-11-17', N'Chiều', N'Ngoại khoa'),
('BS009', '2025-11-18', N'Sáng', N'Nhi khoa'),
('BS006', '2025-11-18', N'Tối', N'Nội khoa'); -- Đã đổi BS011 sang BS006
GO

-- Cập nhật LichKham: Chỉ sử dụng các MaBS đã chọn
INSERT INTO LichKham (MaBenhNhan, MaBS, MaPhong, NgayGioKham, TinhTrangKham) VALUES
('BN-A001', 'BS001', 'P01', '2025-10-01 10:00:00', N'Khám định kỳ'),
('BN-A002', 'BS001', 'P01', '2025-10-02 11:00:00', N'Kiểm tra HA'),
('BN-A003', 'BS002', 'P02', '2025-10-01 08:30:00', N'Sốt'),
('BN-A004', 'BS002', 'P02', '2025-10-01 09:00:00', N'Viêm họng'),
('BN-A005', 'BS002', 'P02', '2025-10-03 15:00:00', N'Tiêm chủng'),
('BN-A001', 'BS003', 'P03', '2025-10-05 14:00:00', N'Mụn trứng cá'),
('BN-A002', 'BS004', 'P01', '2025-11-01 08:00:00', N'Đau ngực'),
('BN-B001', 'BS005', 'P04', '2025-11-10 09:00:00', N'Lần đầu khám Nội'),
('BN-B002', 'BS007', 'P05', '2025-11-10 10:30:00', N'Lần đầu khám Ngoại'),
('BN-B003', 'BS005', 'P04', '2025-11-11 14:00:00', N'Tái khám Nội'),
('BN-B004', 'BS003', 'P03', '2025-11-11 15:30:00', N'Lần đầu khám Da Liễu'),
('BN-B001', 'BS006', 'P04', '2025-11-12 08:00:00', N'Theo dõi Nội'),
('BN-C001', 'BS004', 'P01', '2025-11-20 08:30:00', N'Đã khám Tim Mạch'), -- Đã đổi BS011 sang BS004
('BN-C002', 'BS009', 'P02', '2025-11-20 09:00:00', N'Chờ khám Nhi'),
('BN-C003', 'BS003', 'P03', '2025-11-21 10:00:00', N'Đã khám Da Liễu'),
('BN-C001', 'BS001', 'P01', '2025-11-28 14:00:00', N'Tái khám Tim Mạch'),
('BN-C002', 'BS002', 'P02', '2025-12-01 09:30:00', N'Điều trị nội trú Nhi');
GO

-- Bước 5: THÊM TRIGGER, VIEW VÀ TRUY VẤN BÁO CÁO TỔNG HỢP
----------------------------------------------------------------------

-- ⭐ THÊM TRIGGER: Ngăn chặn Xung đột Thời gian Khám cho Bác sĩ ⭐
PRINT N'--- TRIGGER: Ngăn chặn Xung đột Thời gian Khám cho Bác sĩ ---';
GO

CREATE TRIGGER trg_KiemTraXungDotLichKham
ON LichKham
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM LichKham LK
        JOIN inserted I ON LK.MaBS = I.MaBS AND LK.NgayGioKham = I.NgayGioKham
        WHERE LK.MaLichKham != I.MaLichKham
    )
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50001, N'Lỗi: Bác sĩ đã có lịch khám vào đúng thời điểm này. Vui lòng chọn thời gian khác.', 1;
    END
END;
GO

-- CÁC BÁO CÁO TỔNG HỢP

PRINT N'--- BÁO CÁO 1: THỐNG KÊ BỆNH NHÂN THEO NGÀY ---';
GO
CREATE VIEW vw_ThongKeTheoNgay AS
SELECT
    CAST(NgayGioKham AS DATE) AS NgayKham,
    COUNT(DISTINCT MaBenhNhan) AS SoLuongBenhNhan
FROM LichKham
GROUP BY CAST(NgayGioKham AS DATE);
GO

SELECT * FROM vw_ThongKeTheoNgay ORDER BY NgayKham;
GO

PRINT N'--- BÁO CÁO 2: THỐNG KÊ BỆNH NHÂN THEO THÁNG ---';
GO
CREATE VIEW vw_ThongKeTheoThang AS
SELECT
    YEAR(NgayGioKham) AS Nam,
    MONTH(NgayGioKham) AS Thang,
    COUNT(DISTINCT MaBenhNhan) AS SoLuongBenhNhan
FROM LichKham
GROUP BY YEAR(NgayGioKham), MONTH(NgayGioKham);
GO

SELECT * FROM vw_ThongKeTheoThang ORDER BY Nam, Thang;
GO

PRINT N'--- BÁO CÁO 3: TỔNG SỐ LẦN KHÁM CỦA TỪNG BÁC SĨ ---';

SELECT
    BS.MaBS,
    BS.HoTen,
    BS.ChuyenKhoa,
    COUNT(LK.MaLichKham) AS TongSoLanKham
FROM
    BacSi BS
LEFT JOIN
    LichKham LK ON BS.MaBS = LK.MaBS
GROUP BY
    BS.MaBS,
    BS.HoTen,
    BS.ChuyenKhoa
ORDER BY
    TongSoLanKham DESC;
GO

PRINT N'--- BÁO CÁO 4: BÁC SĨ CÓ NHIỀU BỆNH NHÂN NHẤT (TOP) ---';

WITH SoLanKham AS (
    SELECT MaBS, COUNT(MaLichKham) AS TongSoBenhNhan
    FROM LichKham
    GROUP BY MaBS
)
SELECT TOP 1 WITH TIES
    BS.HoTen,
    BS.ChuyenKhoa,
    SLK.TongSoBenhNhan
FROM
    BacSi BS
JOIN
    SoLanKham SLK ON BS.MaBS = SLK.MaBS
ORDER BY
    SLK.TongSoBenhNhan DESC;
GO

PRINT N'--- BÁO CÁO 5: BỆNH NHÂN ĐANG ĐIỀU TRỊ NỘI TRÚ (ĐÃ SỬA) ---';

SELECT
    BN.MaBenhNhan,
    BN.HoTen AS TenBenhNhan,
    BN.SoDienThoai,
    LK.NgayGioKham AS NgayNhapVien,
    BS.HoTen AS BacSiPhuTrach,
    P.TenPhong AS PhongDieuTri
FROM
    LichKham AS LK
JOIN
    BenhNhan AS BN ON LK.MaBenhNhan = BN.MaBenhNhan
JOIN
    BacSi AS BS ON LK.MaBS = BS.MaBS
LEFT JOIN
    PHONG AS P ON LK.MaPhong = P.MaPhong
WHERE
    LK.TinhTrangKham LIKE N'Điều trị nội trú%'; 
GO

PRINT N'--- BÁO CÁO 6: XÁC NHẬN SỐ LƯỢNG BÁC SĨ MỖI KHOA (KIỂM TRA) ---';
SELECT ChuyenKhoa, COUNT(MaBS) AS SoLuongBacSi
FROM BacSi
GROUP BY ChuyenKhoa
ORDER BY ChuyenKhoa;
GO

PRINT N'--- KỊCH BẢN SQL TỔNG HỢP ĐÃ HOÀN TẤT THÀNH CÔNG TRONG DATABASE QuanLyBenhVien ---';
GO

-- Đoạn mã SQL cũ kết thúc ở khoảng dòng 228/229
GO

-- Bước 6: XEM TẤT CẢ DỮ LIỆU GỐC TRONG CÁC BẢNG (KIỂM TRA) 
----------------------------------------------------------------------

PRINT N'--- DỮ LIỆU GỐC: BẢNG PHONG ---';
SELECT * FROM PHONG ORDER BY MaPhong;
GO

PRINT N'--- DỮ LIỆU GỐC: BẢNG BacSi ---';
SELECT * FROM BacSi ORDER BY MaBS;
GO

PRINT N'--- DỮ LIỆU GỐC: BẢNG BenhNhan ---';
SELECT * FROM BenhNhan ORDER BY MaBenhNhan;
GO

PRINT N'--- DỮ LIỆU GỐC: BẢNG LichKham (Đã sắp xếp theo thời gian khám) ---';
SELECT * FROM LichKham ORDER BY NgayGioKham DESC;
GO

PRINT N'--- DỮ LIỆU GỐC: BẢNG LichTruc (Đã sắp xếp theo ngày trực) ---';
SELECT * FROM LichTruc ORDER BY NgayTruc DESC, CaTruc;
GO