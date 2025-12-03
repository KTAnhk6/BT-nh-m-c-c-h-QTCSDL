-- Bước 1: TẠO VÀ CHUYỂN SANG CƠ SỞ DỮ LIỆU LỚN: QuanLyBenhVien
----------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'QuanLyBenhVien')
BEGIN
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

PRINT N'--- BÁO CÁO 5: BỆNH NHÂN ĐANG ĐIỀU TRỊ NỘI TRÚ ---';

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